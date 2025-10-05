"""Tests for the API utils endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from src import dependencies
from src.utils.config import LocalStorageConfig
from src.utils.storage import LocalStorageManager


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from src.main import app

    return TestClient(app)


@pytest.fixture
def sample_gpx_file():
    """Provide path to sample GPX file."""
    return Path(__file__).parent.parent / "data" / "file.gpx"


def test_root_endpoint(client):
    """Test the root endpoint returns API message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Cycling GPX API"


def test_map_tiles_endpoint_success(client):
    """Test successful map tiles proxy."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.content = b"fake_png_data"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_client_class.return_value = mock_client

        response = client.get("/api/map-tiles/10/512/342.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert b"fake_png_data" in response.content


def test_map_tiles_endpoint_config_not_initialized(client):
    """Test map tiles endpoint when map config is not initialized."""
    original_map_config = dependencies.map_config
    dependencies.map_config = None

    try:
        response = client.get("/api/map-tiles/10/512/342.png")
        assert response.status_code == 500
        assert "Map configuration not initialized" in response.json()["detail"]
    finally:
        dependencies.map_config = original_map_config


def test_map_tiles_endpoint_http_error(client):
    """Test map tiles endpoint with HTTP error."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_client_class.return_value = mock_client

        response = client.get("/api/map-tiles/10/512/342.png")

        assert response.status_code == 404


def test_map_tiles_endpoint_request_error(client):
    """Test map tiles endpoint with request error."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.RequestError("Connection error", request=MagicMock())
        )
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_client_class.return_value = mock_client

        response = client.get("/api/map-tiles/10/512/342.png")

        assert response.status_code == 500


def test_map_tiles_endpoint_unexpected_error(client):
    """Test map tiles endpoint with unexpected error."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Unexpected error"))
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_client_class.return_value = mock_client

        response = client.get("/api/map-tiles/10/512/342.png")

        assert response.status_code == 500


def test_serve_storage_file_local_mode_success(client, sample_gpx_file, tmp_path):
    """Test successfully serving a file from local storage."""
    original_storage_manager = dependencies.storage_manager

    try:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=str(tmp_path),
            base_url="http://localhost:8000/storage",
        )
        local_manager = LocalStorageManager(config)
        dependencies.storage_manager = local_manager

        test_file_path = tmp_path / "test-file.gpx"
        test_file_path.write_text(sample_gpx_file.read_text())

        response = client.get("/storage/test-file.gpx")

        assert response.status_code == 200
        assert "content-disposition" in response.headers
        assert 'filename="test-file.gpx"' in response.headers["content-disposition"]
        assert response.content == sample_gpx_file.read_bytes()
    finally:
        dependencies.storage_manager = original_storage_manager


def test_serve_storage_file_manager_not_initialized(client):
    """Test serving storage file when storage manager is not initialized."""
    original_storage_manager = dependencies.storage_manager
    dependencies.storage_manager = None

    try:
        response = client.get("/storage/test-file.gpx")
        assert response.status_code == 500
        assert "Storage manager not initialized" in response.json()["detail"]
    finally:
        dependencies.storage_manager = original_storage_manager


def test_serve_storage_file_s3_mode_not_available(client):
    """Test serving storage file when in S3 mode (not available)."""
    original_storage_manager = dependencies.storage_manager

    try:
        # Mock a non-local storage manager
        mock_manager = MagicMock()
        mock_manager.__class__.__name__ = "S3Manager"
        dependencies.storage_manager = mock_manager

        response = client.get("/storage/test-file.gpx")

        assert response.status_code == 404
        assert "File serving only available in local mode" in response.json()["detail"]
    finally:
        dependencies.storage_manager = original_storage_manager


def test_serve_storage_file_file_not_found(client, tmp_path):
    """Test serving storage file when file doesn't exist."""
    original_storage_manager = dependencies.storage_manager

    try:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=str(tmp_path),
            base_url="http://localhost:8000/storage",
        )
        local_manager = LocalStorageManager(config)
        dependencies.storage_manager = local_manager

        response = client.get("/storage/nonexistent-file.gpx")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    finally:
        dependencies.storage_manager = original_storage_manager


def test_serve_storage_file_local_storage_not_available(client, tmp_path):
    """Test serving file when local storage manager lacks get_file_path method."""
    original_storage_manager = dependencies.storage_manager

    try:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=str(tmp_path),
            base_url="http://localhost:8000/storage",
        )
        local_manager = LocalStorageManager(config)
        dependencies.storage_manager = local_manager

        with patch("src.api.utils.hasattr") as mock_hasattr:

            def mock_hasattr_func(obj, attr):
                if attr == "get_file_path":
                    return False
                return hasattr(obj, attr)

            mock_hasattr.side_effect = mock_hasattr_func

            response = client.get("/storage/test-file.gpx")

            assert response.status_code == 500
            assert response.json()["detail"] == "Local storage not available"
    finally:
        dependencies.storage_manager = original_storage_manager
