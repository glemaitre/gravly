"""Dependencies and shared state management for the FastAPI application.

This module provides dependency injection functions and manages global state
for database connections, storage management, and service instances.
"""

import logging
from collections.abc import AsyncGenerator
from tempfile import TemporaryDirectory

from sqlalchemy.ext.asyncio import AsyncSession

from .services.wahoo.service import WahooService
from .utils.config import (
    DatabaseConfig,
    MapConfig,
    ServerConfig,
    StorageConfig,
    StravaConfig,
    WahooConfig,
    load_environment_config,
)
from .utils.storage import StorageManager

logger = logging.getLogger(__name__)

# Load configuration at module level
(
    _db_config,
    _storage_config,
    _strava_config,
    _wahoo_config,
    _map_config,
    _server_config,
) = load_environment_config()

# Global state
temp_dir: TemporaryDirectory | None = None
storage_manager: StorageManager | None = None
# Strava service is now created per-request with database session
wahoo: WahooService = WahooService(_wahoo_config)  # Initialize at module level
engine = None
SessionLocal = None

# Configuration
db_config: DatabaseConfig = _db_config
storage_config: StorageConfig = _storage_config
strava_config: StravaConfig = _strava_config
wahoo_config: WahooConfig = _wahoo_config
map_config: MapConfig = _map_config
server_config: ServerConfig = _server_config


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database session.

    Yields
    ------
    AsyncSession
        Database session for the request

    Raises
    ------
    RuntimeError
        If database session is not initialized
    """
    if SessionLocal is None:
        raise RuntimeError("Database session not initialized")

    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_storage() -> StorageManager:
    """Dependency for storage manager.

    Returns
    -------
    StorageManager
        Storage manager instance

    Raises
    ------
    RuntimeError
        If storage manager is not initialized
    """
    if storage_manager is None:
        raise RuntimeError("Storage manager not initialized")
    return storage_manager


def get_strava_config() -> StravaConfig:
    """Get Strava configuration.

    Returns
    -------
    StravaConfig
        Strava configuration
    """
    return strava_config


def get_wahoo_service() -> WahooService:
    """Dependency for Wahoo service.

    Returns
    -------
    WahooService
        Wahoo service instance

    Raises
    ------
    RuntimeError
        If Wahoo service is not initialized
    """
    if wahoo is None:
        raise RuntimeError("Wahoo service not initialized")
    return wahoo
