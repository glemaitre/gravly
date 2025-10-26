"""Wahoo API endpoints."""

import base64
import logging
from datetime import datetime
from pathlib import Path

import gpxpy
from fastapi import APIRouter, Form, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.dependencies import get_wahoo_service
from src.models.track import Track, TrackType
from src.utils.gpx import convert_gpx_to_fit, extract_from_gpx_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wahoo", tags=["wahoo"])


def create_wahoo_router() -> APIRouter:
    """Create Wahoo router with dependencies."""

    @router.get("/auth-url")
    async def get_wahoo_auth_url(state: str = "wahoo_auth"):
        """Get Wahoo OAuth authorization URL"""
        try:
            wahoo_service = get_wahoo_service()

            # Use centralized server configuration for OAuth redirect

            auth_url = wahoo_service.get_authorization_url(state)

            logger.info("Generated Wahoo authorization URL")

            return {"auth_url": auth_url}
        except Exception as e:
            logger.error(f"Error generating Wahoo authorization URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate authorization URL: {str(e)}",
            )

    @router.post("/exchange-code")
    async def exchange_wahoo_code(code: str = Form(...)):
        """Exchange Wahoo authorization code for access token"""
        try:
            wahoo_service = get_wahoo_service()
            token_response = wahoo_service.exchange_code_for_token(code)
            return {
                "access_token": token_response["access_token"],
                "expires_at": token_response["expires_at"],
            }
        except Exception as e:
            print(e)
            logger.error(f"Error exchanging Wahoo code: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Failed to exchange code: {str(e)}"
            )

    @router.post("/refresh-token")
    async def refresh_wahoo_token():
        """Refresh Wahoo access token using refresh token"""
        try:
            wahoo_service = get_wahoo_service()
            success = wahoo_service.refresh_access_token()
            if success:
                return {"success": True, "message": "Token refreshed successfully"}
            else:
                raise HTTPException(status_code=401, detail="Failed to refresh token")
        except Exception as e:
            logger.error(f"Error refreshing Wahoo token: {str(e)}")
            raise HTTPException(status_code=401, detail="Failed to refresh token")

    @router.post("/deauthorize")
    async def deauthorize_wahoo():
        """Deauthorize the application and delete all tokens"""
        try:
            wahoo_service = get_wahoo_service()
            wahoo_service.deauthorize()
            return {"success": True, "message": "Deauthorized successfully"}
        except Exception as e:
            logger.error(f"Error deauthorizing: {str(e)}")
            raise HTTPException(
                status_code=401, detail=f"Failed to deauthorize: {str(e)}"
            )

    @router.get("/user")
    async def get_wahoo_user():
        """Get authenticated user information"""
        try:
            wahoo_service = get_wahoo_service()
            user = wahoo_service.get_user()
            return user
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Failed to get user: {str(e)}")

    @router.get("/callback")
    async def wahoo_callback(
        code: str = Query(None, description="Authorization code from Wahoo"),
    ):
        """Handle Wahoo OAuth callback and print the authorization code."""
        try:
            if not code:
                logger.warning("Wahoo callback received without authorization code")
                raise HTTPException(
                    status_code=400, detail="Authorization code is required"
                )

            logger.info(f"Received Wahoo authorization code: {code}")

            return {
                "message": "Wahoo authorization code received successfully",
                "code": code,
                "status": "success",
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling Wahoo callback: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to handle callback: {str(e)}"
            )

    @router.post("/routes/{route_id}/upload")
    async def upload_route(route_id: int):
        """Upload a route from the database to Wahoo"""
        logger.info(f"Received upload request for route_id={route_id}")
        from src.dependencies import SessionLocal as global_session_local

        if global_session_local is None:
            logger.error("Database not initialized")
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            logger.info(f"Querying database for route_id={route_id}")
            async with global_session_local() as session:
                # Get the route from database
                stmt = select(Track).where(
                    Track.id == route_id, Track.track_type == TrackType.ROUTE
                )
                result = await session.execute(stmt)
                track = result.scalar_one_or_none()

                if not track:
                    logger.error(f"Route {route_id} not found in database")
                    raise HTTPException(status_code=404, detail="Route not found")

                logger.info(f"Found route: {track.name}")

                # Load GPX file using storage manager
                from src.dependencies import storage_manager as global_storage_manager

                if not global_storage_manager:
                    raise HTTPException(
                        status_code=500, detail="Storage manager not available"
                    )

                logger.info(f"Loading GPX from storage: {track.file_path}")
                gpx_bytes = global_storage_manager.load_gpx_data(track.file_path)

                if gpx_bytes is None:
                    logger.error(f"Failed to load GPX data from {track.file_path}")
                    raise HTTPException(status_code=404, detail="GPX file not found")

                gpx_content = gpx_bytes.decode("utf-8")

                logger.info(f"Attempting to upload route {route_id} to Wahoo")
                logger.info(f"Route name: {track.name}")
                logger.info(f"GPX file size: {len(gpx_content)} bytes")
                logger.info(f"GPX file preview (first 500 chars): {gpx_content[:500]}")

                # Upload route to Wahoo
                logger.info("=== WAHOO UPLOAD REQUEST ===")
                logger.info("Endpoint: POST https://api.wahooligan.com/v1/routes")
                logger.info(f"Uploading route: {track.name}")

                wahoo_service = get_wahoo_service()

                # Parse GPX and extract metadata
                gpx = gpxpy.parse(gpx_content)
                gpx_data = extract_from_gpx_file(gpx, str(route_id))

                logger.info(
                    f"Extracted GPX stats: distance={gpx_data.total_stats.total_distance:.2f}km, "
                    f"elevation_gain={gpx_data.total_stats.total_elevation_gain:.0f}m, "
                    f"elevation_loss={gpx_data.total_stats.total_elevation_loss:.0f}m"
                )

                # Get start point
                start_point = gpx_data.points[0] if gpx_data.points else None

                # Convert GPX to FIT format
                fit_bytes = convert_gpx_to_fit(gpx, track.name)
                logger.info(f"Converted GPX to FIT, size: {len(fit_bytes)} bytes")

                # Encode FIT content as base64 data URI for Wahoo API
                fit_base64 = base64.b64encode(fit_bytes).decode("utf-8")
                route_file_data_uri = f"data:application/vnd.fit;base64,{fit_base64}"

                logger.info(
                    f"FIT encoded to base64, size: {len(route_file_data_uri)} chars"
                )

                # Call Wahoo service to upload route
                external_id = f"gravly_route_{route_id}"

                # Prepare common route parameters (for both create and update)
                common_params = {
                    "route_file": route_file_data_uri,
                    "filename": f"{track.name}.fit",
                    "route_name": track.name,
                    "description": track.comments or "",
                    "provider_updated_at": (
                        gpx.time.isoformat() if gpx.time else datetime.now().isoformat()
                    ),
                    "start_lat": start_point.latitude if start_point else None,
                    "start_lng": start_point.longitude if start_point else None,
                    "distance": gpx_data.total_stats.total_distance
                    * 1000,  # Convert km to meters
                    "ascent": (
                        gpx_data.total_stats.total_elevation_gain
                        if gpx_data.total_stats.total_elevation_gain > 0
                        else None
                    ),
                    "descent": (
                        gpx_data.total_stats.total_elevation_loss
                        if gpx_data.total_stats.total_elevation_loss > 0
                        else None
                    ),
                }

                # Get all routes from Wahoo to check if route exists
                logger.info("Fetching all routes from Wahoo Cloud")
                all_routes = wahoo_service.get_routes()

                # Look for existing route with matching external_id
                wahoo_route_id = None
                for route in all_routes:
                    if route.get("external_id") == external_id:
                        wahoo_route_id = route["id"]
                        logger.info(
                            f"Found existing route in Wahoo with ID: {wahoo_route_id}"
                        )
                        break

                # Upload or update the route
                if wahoo_route_id:
                    # Update existing route (external_id is not passed for updates)
                    logger.info(f"Updating existing route {wahoo_route_id} in Wahoo")
                    result = wahoo_service.update_route(
                        route_id=wahoo_route_id, **common_params
                    )
                    logger.info("=== WAHOO UPLOAD RESPONSE ===")
                    logger.info(f"Status: Success (Updated)")
                    logger.info(f"Response: {result}")
                    logger.info("========================================")
                else:
                    # Create new route (include external_id for new routes)
                    logger.info(f"Creating new route with external_id: {external_id}")
                    create_params = {**common_params, "external_id": external_id}
                    result = wahoo_service.create_route(**create_params)
                    logger.info("=== WAHOO UPLOAD RESPONSE ===")
                    logger.info(f"Status: Success (Created)")
                    logger.info(f"Response: {result}")
                    logger.info("========================================")

                result_message = "updated" if wahoo_route_id else "uploaded"

                logger.info(f"{result_message.capitalize()} route {route_id} to Wahoo")
                return {
                    "success": True,
                    "message": f"Route '{track.name}' {result_message} to Wahoo successfully",
                }
        except HTTPException as he:
            logger.error(f"HTTPException raised: {he.status_code} - {he.detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to upload route: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to upload route: {str(e)}"
            )

    return router
