import logging
from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .api.auth import create_auth_router
from .api.segments import create_segments_router
from .api.strava import create_strava_router
from .api.upload import create_upload_router
from .models.base import Base
from .services.strava import StravaService
from .utils.config import load_environment_config
from .utils.postgres import get_database_url
from .utils.storage import (
    LocalStorageManager,
    StorageManager,
    get_storage_manager,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.info("Backend logging configured")

db_config, storage_config, strava_config, map_config = load_environment_config()

temp_dir: TemporaryDirectory | None = None
storage_manager: StorageManager | None = None
strava = StravaService(strava_config)
DATABASE_URL = get_database_url(
    host=db_config.host,
    port=db_config.port,
    database=db_config.name,
    username=db_config.user,
    password=db_config.password,
)
engine = None
SessionLocal = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    global temp_dir, storage_manager, engine, SessionLocal

    temp_dir = TemporaryDirectory(prefix="cycling_gpx_")
    logger.info(f"Created temporary directory: {temp_dir.name}")

    try:
        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        SessionLocal = async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        logger.info("Database engine and session initialized")
    except Exception as db_init_e:
        logger.warning(f"Failed to initialize database engine: {db_init_e}")
        engine = None
        SessionLocal = None

    try:
        storage_manager = get_storage_manager(storage_config)
        logger.info(
            f"Storage manager initialized successfully "
            f"(type: {storage_config.storage_type})"
        )
    except Exception as e:
        logger.warning(f"Failed to initialize storage manager: {str(e)}")
        storage_manager = None

    if engine is not None:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables ensured")
        except Exception as db_e:
            logger.warning(f"Could not initialize database: {db_e}")
    else:
        logger.warning("Skipping database initialization - engine not available")

    # Strava router will access temp_dir through global import

    yield

    if temp_dir:
        logger.info(f"Cleaning up temporary directory: {temp_dir.name}")
        temp_dir.cleanup()

    if engine:
        logger.info("Closing database engine")
        await engine.dispose()


app = FastAPI(title="Cycling GPX API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include Strava API router (will be initialized with proper dependencies in lifespan)
strava_router = create_strava_router(strava, None)  # temp_dir will be set in lifespan
app.include_router(strava_router)

# Include Upload API router
upload_router = create_upload_router(None, None)  # Will be set in lifespan via globals
app.include_router(upload_router)

# Include Auth API router
auth_router = create_auth_router(None)  # Will be set in lifespan via globals
app.include_router(auth_router)

# Include Segments API router
segments_router = create_segments_router(None)  # Will be set in lifespan via globals
app.include_router(segments_router)


@app.get("/")
async def root():
    return {"message": "Cycling GPX API"}


@app.get("/api/map-tiles/{z}/{x}/{y}.png")
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
    """
    try:
        # Construct the Thunderforest API URL with our server-side API key
        tile_url = f"https://{{s}}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey={map_config.thunderforest_api_key}"

        # Use a random subdomain (s) for load balancing
        import random

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


@app.get("/storage/{file_path:path}")
async def serve_storage_file(file_path: str):
    """Serve files from local storage for development."""
    global storage_manager

    if not storage_manager:
        raise HTTPException(status_code=500, detail="Storage manager not initialized")

    if not isinstance(storage_manager, LocalStorageManager):
        raise HTTPException(
            status_code=404, detail="File serving only available in local mode"
        )

    if hasattr(storage_manager, "get_file_path"):
        local_file_path = storage_manager.get_file_path(file_path)
    else:
        raise HTTPException(status_code=500, detail="Local storage not available")

    if not local_file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        local_file_path, media_type="application/gpx+xml", filename=local_file_path.name
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
