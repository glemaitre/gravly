"""Utility API endpoints for the application.

This module provides general utility endpoints including:
- Root endpoint for API health check
- Map tiles proxy for secure API key management
- Storage file serving for local development
"""

import logging
import random

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from ..utils.storage import LocalStorageManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint for API health check.

    Returns
    -------
    dict
        Simple message indicating the API is running
    """
    return {"message": "Cycling GPX API"}


@router.get("/api/map-tiles/{z}/{x}/{y}.png")
async def get_map_tiles(z: int, x: int, y: int):
    """Proxy endpoint for Thunderforest map tiles to hide API key from frontend.

    This endpoint fetches map tiles from Thunderforest API using the server-side
    API key and returns them to the frontend, keeping the API key secure.

    Parameters
    ----------
    z : int
        Zoom level
    x : int
        Tile X coordinate
    y : int
        Tile Y coordinate

    Returns
    -------
    Response
        PNG image data of the map tile

    Raises
    ------
    HTTPException
        If the map configuration is not initialized or if there's an error
        fetching the tile
    """
    # Import dynamically to allow tests to mock it
    from ..dependencies import map_config as global_map_config

    if global_map_config is None:
        raise HTTPException(status_code=500, detail="Map configuration not initialized")

    try:
        # Construct the Thunderforest API URL with our server-side API key
        tile_url = f"https://{{s}}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey={global_map_config.thunderforest_api_key}"

        # Use a random subdomain for load balancing
        subdomain = random.choice(["a", "b", "c"])
        tile_url = tile_url.replace("{s}", subdomain)

        # Fetch the tile from Thunderforest
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(tile_url)
            response.raise_for_status()

            # Return the tile image with appropriate headers
            return Response(
                content=response.content,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                    "Access-Control-Allow-Origin": "*",
                },
            )

    except httpx.HTTPStatusError as e:
        logger.warning(
            f"HTTP error fetching tile {z}/{x}/{y}: {e.response.status_code}"
        )
        raise HTTPException(
            status_code=e.response.status_code, detail="Failed to fetch map tile"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error fetching tile {z}/{x}/{y}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch map tile")
    except Exception as e:
        logger.error(f"Unexpected error fetching tile {z}/{x}/{y}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/storage/{file_path:path}")
async def serve_storage_file(file_path: str):
    """Serve files from local storage for development.

    This endpoint provides access to files stored in the local storage
    during development. It is only available when using LocalStorageManager.

    Parameters
    ----------
    file_path : str
        Path to the file relative to the storage root

    Returns
    -------
    FileResponse
        The requested file

    Raises
    ------
    HTTPException
        If storage manager is not initialized, not in local mode,
        or if the file is not found
    """
    # Import dynamically to allow tests to mock it
    from ..dependencies import storage_manager as global_storage_manager

    if global_storage_manager is None:
        raise HTTPException(status_code=500, detail="Storage manager not initialized")

    if not isinstance(global_storage_manager, LocalStorageManager):
        raise HTTPException(
            status_code=404, detail="File serving only available in local mode"
        )

    if hasattr(global_storage_manager, "get_file_path"):
        local_file_path = global_storage_manager.get_file_path(file_path)
    else:
        raise HTTPException(status_code=500, detail="Local storage not available")

    if not local_file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        local_file_path, media_type="application/gpx+xml", filename=local_file_path.name
    )
