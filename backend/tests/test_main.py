"""Tests for FastAPI main endpoints."""

import io
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def create_test_image_bytes(format: str = "JPEG") -> bytes:
    """Create test image bytes using PIL for real image validation.

    Args:
        format (str): Image format (JPEG, PNG, GIF, WEBP)

    Returns:
        bytes: Real image file data
    """
    # Create a 10x10 RGBA test image
    img = Image.new("RGB", (10, 10), color="red")

    # Save in specified format to BytesIO
    img_data = io.BytesIO()
    if format.upper() == "JPEG":
        img.save(img_data, format="JPEG")
    elif format.upper() == "PNG":
        img.save(img_data, format="PNG")
    elif format.upper() == "GIF":
        img.save(img_data, format="GIF")
    elif format.upper() == "WEBP":
        img.save(img_data, format="WEBP")
    else:
        raise ValueError(f"Unsupported format: {format}")

    return img_data.getvalue()


@pytest.fixture(autouse=True)
def setup_test_database_config():
    """Set up database and storage configuration for tests.

    IMPORTANT: This fixture must run BEFORE src.main is imported because:
    1. src.main calls load_environment_config() at import time
    2. If we import src.main at the top of this file, it would use real environment
       variables instead of our test configuration
    3. This fixture ensures test environment variables are set FIRST, then imports
       src.main with the correct test configuration

    This pattern prevents tests from failing due to missing or incorrect environment
    variables in the test environment.
    """
    test_config = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "test_cycling",
        "DB_USER": "test_postgres",
        "DB_PASSWORD": "test_password",
        "STORAGE_TYPE": "local",
        "LOCAL_STORAGE_ROOT": "./test_storage",
        "LOCAL_STORAGE_BASE_URL": "http://localhost:8000/storage",
        "STRAVA_CLIENT_ID": "test_client_id",
        "STRAVA_CLIENT_SECRET": "test_client_secret",
        "STRAVA_TOKENS_FILE_PATH": "/tmp/test_strava_tokens.json",
    }

    with patch.dict(os.environ, test_config, clear=False):
        # Import main module AFTER setting up environment variables
        # This ensures src.main loads with test configuration, not real environment
        import src.main as main_module

        # Make main_module available globally for tests as 'src'
        # This allows existing @patch decorators to work with src.main references
        globals()["src"] = type("MockSrc", (), {"main": main_module})()
        yield


@pytest.fixture
def main_module():
    """Get access to the main module for testing.

    This fixture provides access to the src.main module that was imported with
    test configuration by the setup_test_database_config fixture. Tests can use
    this fixture instead of accessing the global 'src' variable directly, which
    provides better type safety and cleaner test code.
    """
    import src.main

    return src.main


@pytest.fixture
def app():
    """Get the FastAPI app instance."""
    from src.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def lifespan():
    """Get the lifespan context manager."""
    from src.main import lifespan as lifespan_cm

    return lifespan_cm


@pytest.fixture
def client(tmp_path, app):
    """Create a test client with temporary directory."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_gpx_file():
    """Get the sample GPX file from tests/data directory."""
    data_dir = Path(__file__).parent / "data"
    gpx_file = data_dir / "file.gpx"
    return gpx_file


@pytest.fixture
def mock_bucket_name():
    """Provide a mock bucket name for testing."""
    return "test-cycling-gpx-bucket"


@pytest.fixture
def mock_s3_environment(mock_bucket_name):
    """Set up mock S3 environment with environment variables."""
    with patch.dict(
        os.environ,
        {
            "AWS_S3_BUCKET": mock_bucket_name,
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        },
    ):
        yield mock_bucket_name


def test_root_endpoint(client):
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Cycling GPX API"}


def test_app_lifespan(app):
    """Test that the app is properly configured."""
    assert app is not None
    assert app.title == "Cycling GPX API"
    assert app.version == "1.0.0"

    routes = [route.path for route in app.routes]
    assert "/" in routes
    assert "/api/upload-gpx" in routes
    # Segments endpoints are now in the segments router with specific paths
    assert any("/api/segments" in route for route in routes)
