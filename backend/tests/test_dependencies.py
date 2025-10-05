"""Tests for the dependencies module."""

import pytest
from fastapi.testclient import TestClient
from src import dependencies


@pytest.fixture
def app():
    """Get the FastAPI app instance."""
    from src.main import app

    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


def test_get_db_raises_when_not_initialized():
    """Test that get_db raises RuntimeError when SessionLocal is None."""
    import asyncio

    original_session_local = dependencies.SessionLocal
    dependencies.SessionLocal = None

    async def run_test():
        gen = dependencies.get_db()
        with pytest.raises(RuntimeError, match="Database session not initialized"):
            # Trigger the generator to execute the check
            await gen.__anext__()

    try:
        asyncio.run(run_test())
    finally:
        dependencies.SessionLocal = original_session_local


def test_get_db_yields_session(app, client):
    """Test that get_db yields a database session."""
    import asyncio

    async def run_test():
        # The app and client fixtures initialize the database
        gen = dependencies.get_db()
        session = await gen.__anext__()

        assert session is not None

        # Cleanup
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    asyncio.run(run_test())


def test_get_storage_raises_when_not_initialized():
    """Test that get_storage raises RuntimeError when storage_manager is None."""
    original_storage_manager = dependencies.storage_manager
    dependencies.storage_manager = None

    try:
        with pytest.raises(RuntimeError, match="Storage manager not initialized"):
            dependencies.get_storage()
    finally:
        dependencies.storage_manager = original_storage_manager


def test_get_storage_returns_manager(app):
    """Test that get_storage returns the storage manager."""
    # The app fixture initializes the storage manager
    manager = dependencies.get_storage()
    assert manager is not None


def test_get_strava_service_raises_when_not_initialized():
    """Test that get_strava_service raises RuntimeError when strava is None."""
    original_strava = dependencies.strava
    dependencies.strava = None

    try:
        with pytest.raises(RuntimeError, match="Strava service not initialized"):
            dependencies.get_strava_service()
    finally:
        dependencies.strava = original_strava


def test_get_strava_service_returns_service():
    """Test that get_strava_service returns the Strava service."""
    service = dependencies.get_strava_service()
    assert service is not None
    assert hasattr(service, "get_authorization_url")


def test_configuration_loaded_at_module_level():
    """Test that configuration is loaded at module level."""
    assert dependencies.db_config is not None
    assert dependencies.storage_config is not None
    assert dependencies.strava_config is not None
    assert dependencies.map_config is not None


def test_strava_service_initialized_at_module_level():
    """Test that Strava service is initialized at module level."""
    assert dependencies.strava is not None
    assert isinstance(dependencies.strava, dependencies.StravaService)
