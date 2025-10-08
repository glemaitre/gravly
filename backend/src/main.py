"""Main FastAPI application module.

This module provides the FastAPI application initialization, lifespan management,
middleware configuration, and router registration.
"""

import logging
from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from . import dependencies
from .api.auth import create_auth_router
from .api.routes import create_routes_router
from .api.segments import create_segments_router
from .api.strava import create_strava_router
from .api.upload import create_upload_router
from .api.utils import router as utils_router
from .models.base import Base
from .utils.postgres import get_database_url
from .utils.storage import get_storage_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.info("Backend logging configured")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown.

    This context manager handles:
    - Temporary directory creation
    - Database engine and session initialization
    - Storage manager initialization
    - Database table creation
    - Cleanup on shutdown

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance

    Yields
    ------
    None
        Control is yielded back to FastAPI after initialization
    """
    # Initialize temporary directory
    dependencies.temp_dir = TemporaryDirectory(prefix="cycling_gpx_")
    logger.info(f"Created temporary directory: {dependencies.temp_dir.name}")

    # Initialize database
    try:
        DATABASE_URL = get_database_url(
            host=dependencies.db_config.host,
            port=dependencies.db_config.port,
            database=dependencies.db_config.name,
            username=dependencies.db_config.user,
            password=dependencies.db_config.password,
        )
        dependencies.engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        dependencies.SessionLocal = async_sessionmaker(
            dependencies.engine, expire_on_commit=False, class_=AsyncSession
        )
        logger.info("Database engine and session initialized")
    except Exception as db_init_e:
        logger.warning(f"Failed to initialize database engine: {db_init_e}")
        dependencies.engine = None
        dependencies.SessionLocal = None

    # Initialize storage manager
    try:
        dependencies.storage_manager = get_storage_manager(dependencies.storage_config)
        logger.info(
            f"Storage manager initialized successfully "
            f"(type: {dependencies.storage_config.storage_type})"
        )
    except Exception as e:
        logger.warning(f"Failed to initialize storage manager: {str(e)}")
        dependencies.storage_manager = None

    # Create database tables
    if dependencies.engine is not None:
        try:
            async with dependencies.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables ensured")
        except Exception as db_e:
            logger.warning(f"Could not initialize database: {db_e}")
    else:
        logger.warning("Skipping database initialization - engine not available")

    yield

    # Cleanup on shutdown
    if dependencies.temp_dir:
        logger.info(f"Cleaning up temporary directory: {dependencies.temp_dir.name}")
        dependencies.temp_dir.cleanup()

    if dependencies.engine:
        logger.info("Closing database engine")
        await dependencies.engine.dispose()


# Initialize FastAPI application
app = FastAPI(title="Cycling GPX API", version="1.0.0", lifespan=lifespan)

# Configure CORS middleware
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

# Register routers
app.include_router(utils_router)
app.include_router(
    create_strava_router(dependencies.strava, None)
)  # temp_dir will be set via dependencies module
app.include_router(
    create_upload_router(None, None)
)  # Will be set in lifespan via dependencies module
app.include_router(
    create_auth_router(None)
)  # Will be set in lifespan via dependencies module
app.include_router(
    create_segments_router(None)
)  # Will be set in lifespan via dependencies module
app.include_router(
    create_routes_router(None)
)  # Will be set in lifespan via dependencies module


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
