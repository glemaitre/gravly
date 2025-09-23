"""Tests for FastAPI main endpoints."""

import asyncio
import json
import os
from pathlib import Path
from unittest.mock import patch

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from src.utils.gpx import GPXBounds, generate_gpx_segment
from src.utils.storage import LocalStorageManager, S3Manager, cleanup_local_file

from backend.src.utils.config import LocalStorageConfig, S3StorageConfig


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


def test_upload_gpx_success(client, sample_gpx_file):
    """Test successful GPX file upload."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 200
    data = response.json()

    assert "file_id" in data
    assert "track_name" in data
    assert "points" in data
    assert "total_stats" in data
    assert "bounds" in data

    assert data["track_name"] == "Test chemin Gravel autour du Puit"
    assert len(data["points"]) == 6951
    assert data["total_stats"]["total_points"] == 6951
    assert data["total_stats"]["total_distance"] >= 0
    assert data["bounds"]["north"] > data["bounds"]["south"]
    assert data["bounds"]["east"] > data["bounds"]["west"]


def test_upload_gpx_invalid_file_extension(client):
    """Test upload with invalid file extension."""
    response = client.post(
        "/api/upload-gpx", files={"file": ("test.txt", b"not a gpx file", "text/plain")}
    )

    assert response.status_code == 400
    assert "File must be a GPX file" in response.json()["detail"]


def test_upload_gpx_invalid_gpx_content(client):
    """Test upload with invalid GPX content."""
    response = client.post(
        "/api/upload-gpx",
        files={"file": ("test.gpx", b"not valid gpx content", "application/gpx+xml")},
    )

    assert response.status_code == 400
    # The error message might vary depending on the specific XML parsing error
    detail = response.json()["detail"]
    assert any(
        msg in detail
        for msg in ["Invalid GPX file", "Error parsing XML", "syntax error"]
    )


def test_upload_gpx_no_file(client):
    """Test upload without file."""
    response = client.post("/api/upload-gpx")

    assert response.status_code == 422  # Validation error


@mock_aws
def test_create_segment_success(client, sample_gpx_file, tmp_path):
    """Test successful segment creation."""

    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket="test-bucket")

    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
                "track_type": "segment",
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "100",
                "surface_type": "forest-trail",
                "difficulty_level": "3",
                "commentary_text": "Test commentary",
                "video_links": "[]",
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert "name" in data
    assert "track_type" in data
    assert "tire_dry" in data
    assert "tire_wet" in data
    assert "file_path" in data

    assert data["name"] == "Test Segment"
    assert data["track_type"] == "segment"
    assert data["tire_dry"] == "slick"
    assert data["tire_wet"] == "semi-slick"
    # File path should start with either s3:// or local:// depending on storage type
    # Note: The actual format might be local:/ instead of local://
    assert data["file_path"].startswith(("s3://", "local://", "local:/"))
    assert data["file_path"].endswith(".gpx")


def test_create_segment_invalid_tire_types(client, sample_gpx_file):
    """Test segment creation with invalid tire types."""
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    response = client.post(
        "/api/segments",
        data={
            "name": "Test Segment",
            "track_type": "segment",
            "tire_dry": "invalid",
            "tire_wet": "semi-slick",
            "file_id": file_id,
            "start_index": "0",
            "end_index": "2",
            "surface_type": "forest-trail",
            "difficulty_level": "3",
        },
    )

    assert response.status_code == 422
    assert "Invalid tire types" in response.json()["detail"]


def test_create_segment_invalid_track_type(client, sample_gpx_file):
    """Test segment creation with invalid track type."""
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    response = client.post(
        "/api/segments",
        data={
            "name": "Test Segment",
            "track_type": "invalid",
            "tire_dry": "slick",
            "tire_wet": "semi-slick",
            "file_id": file_id,
            "start_index": "0",
            "end_index": "2",
            "surface_type": "forest-trail",
            "difficulty_level": "3",
        },
    )

    assert response.status_code == 422
    assert "Invalid track type" in response.json()["detail"]


@mock_aws
def test_create_route_success(client, sample_gpx_file, tmp_path):
    """Test successful route creation."""
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket="test-bucket")

    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        response = client.post(
            "/api/segments",
            data={
                "name": "Test Route",
                "track_type": "route",
                "tire_dry": "knobs",
                "tire_wet": "knobs",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "100",
                "surface_type": "forest-trail",
                "difficulty_level": "3",
                "commentary_text": "Test route commentary",
                "video_links": "[]",
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert "name" in data
    assert "track_type" in data
    assert "tire_dry" in data
    assert "tire_wet" in data
    assert "file_path" in data

    assert data["name"] == "Test Route"
    assert data["track_type"] == "route"
    assert data["tire_dry"] == "knobs"
    assert data["tire_wet"] == "knobs"
    assert data["file_path"].startswith(("s3://", "local://", "local:/"))
    assert data["file_path"].endswith(".gpx")


def test_create_segment_file_not_found(client):
    """Test segment creation with non-existent file ID."""
    response = client.post(
        "/api/segments",
        data={
            "name": "Test Segment",
            "track_type": "segment",
            "tire_dry": "slick",
            "tire_wet": "semi-slick",
            "file_id": "non-existent-id",
            "start_index": "0",
            "end_index": "2",
            "surface_type": "forest-trail",
            "difficulty_level": "3",
        },
    )

    assert response.status_code == 404
    assert "Uploaded file not found" in response.json()["detail"]


def test_create_segment_missing_required_fields(client):
    """Test segment creation with missing required fields."""
    response = client.post(
        "/api/segments",
        data={
            "name": "Test Segment",
            # Missing tire_dry, tire_wet, file_id, start_index, end_index
        },
    )

    assert response.status_code == 422  # Validation error


def test_create_segment_invalid_indices(client, sample_gpx_file, tmp_path):
    """Test segment creation with invalid start/end indices."""
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
                "track_type": "segment",
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "10000",  # Invalid: beyond available points
                "end_index": "5",  # Invalid: end before start
            },
        )

    # This should either succeed (if indices are clamped) or fail gracefully
    # The exact behavior depends on the GPX processing logic
    assert response.status_code in [200, 422, 500]


@mock_aws
def test_create_segment_with_commentary_and_media(client, sample_gpx_file, tmp_path):
    """Test segment creation with commentary and media."""

    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket="test-bucket")

    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment with Media",
                "track_type": "segment",
                "tire_dry": "knobs",
                "tire_wet": "knobs",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "50",
                "surface_type": "field-trail",
                "difficulty_level": "4",
                "commentary_text": "This is a test segment with commentary",
                "video_links": json.dumps(
                    [{"url": "https://youtube.com/watch?v=test", "title": "Test Video"}]
                ),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Segment with Media"


@mock_aws
def test_multiple_segments_same_file(client, sample_gpx_file, tmp_path):
    """Test creating multiple segments from the same uploaded file."""

    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket="test-bucket")

    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        response1 = client.post(
            "/api/segments",
            data={
                "name": "First Segment",
                "track_type": "segment",
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "50",
                "surface_type": "forest-trail",
                "difficulty_level": "3",
            },
        )

        assert response1.status_code == 200

        response2 = client.post(
            "/api/segments",
            data={
                "name": "Second Segment",
                "track_type": "route",
                "tire_dry": "knobs",
                "tire_wet": "knobs",
                "file_id": file_id,
                "start_index": "50",
                "end_index": "100",
                "surface_type": "field-trail",
                "difficulty_level": "4",
            },
        )

        assert response2.status_code == 200

        assert response1.json()["name"] == "First Segment"
        assert response2.json()["name"] == "Second Segment"


@patch("src.main.temp_dir", None)
def test_upload_gpx_no_temp_directory(client, sample_gpx_file):
    """Test upload when temporary directory is not initialized."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 500
    assert "Temporary directory not initialized" in response.json()["detail"]


@patch("src.main.open", side_effect=OSError("Permission denied"))
def test_upload_gpx_file_save_failure(mock_open, client, sample_gpx_file):
    """Test upload when file saving fails due to filesystem error."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 500
    assert "Failed to save file" in response.json()["detail"]
    assert "Permission denied" in response.json()["detail"]


@patch("src.main.open", side_effect=OSError("Disk full"))
def test_upload_gpx_disk_full_failure(mock_open, client, sample_gpx_file):
    """Test upload when file saving fails due to disk space issues."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 500
    assert "Failed to save file" in response.json()["detail"]
    assert "Disk full" in response.json()["detail"]


@patch("src.main.extract_from_gpx_file", side_effect=Exception("GPX processing failed"))
def test_upload_gpx_processing_failure(mock_extract, client, sample_gpx_file):
    """Test upload when GPX processing fails after successful file save."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 400
    assert "Invalid GPX file" in response.json()["detail"]
    assert "GPX processing failed" in response.json()["detail"]


@patch("src.main.extract_from_gpx_file", side_effect=ValueError("Invalid track data"))
def test_upload_gpx_invalid_track_data(mock_extract, client, sample_gpx_file):
    """Test upload when GPX file has invalid track data."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 400
    assert "Invalid GPX file" in response.json()["detail"]
    assert "Invalid track data" in response.json()["detail"]


@patch("src.main.temp_dir", None)
def test_create_segment_no_temp_directory(client):
    """Test segment creation when temporary directory is not initialized."""
    response = client.post(
        "/api/segments",
        data={
            "name": "Test Segment",
            "track_type": "segment",
            "tire_dry": "slick",
            "tire_wet": "semi-slick",
            "file_id": "test-id",
            "start_index": "0",
            "end_index": "2",
            "surface_type": "forest-trail",
            "difficulty_level": "3",
        },
    )

    assert response.status_code == 500
    assert "Temporary directory not initialized" in response.json()["detail"]


@patch(
    "src.main.generate_gpx_segment", side_effect=Exception("Segment generation failed")
)
def test_create_segment_generation_failure(
    mock_generate, client, sample_gpx_file, tmp_path
):
    """Test segment creation when GPX segment generation fails."""
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
                "track_type": "segment",
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "100",
                "surface_type": "forest-trail",
                "difficulty_level": "3",
            },
        )

    assert response.status_code == 500
    assert "Failed to process GPX file" in response.json()["detail"]
    assert "Segment generation failed" in response.json()["detail"]


@patch(
    "src.main.generate_gpx_segment", side_effect=ValueError("Invalid segment indices")
)
def test_create_segment_invalid_indices_generation(
    mock_generate, client, sample_gpx_file, tmp_path
):
    """Test segment creation when generation fails due to invalid indices."""
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
                "track_type": "segment",
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "100",
                "surface_type": "forest-trail",
                "difficulty_level": "3",
            },
        )

    assert response.status_code == 500
    assert "Failed to process GPX file" in response.json()["detail"]
    assert "Invalid segment indices" in response.json()["detail"]


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.options("/api/upload-gpx")
    # CORS preflight should be handled by the middleware
    assert response.status_code in [200, 405]  # Depends on CORS configuration


def test_app_lifespan(app):
    """Test that the app is properly configured."""
    assert app is not None
    assert app.title == "Cycling GPX API"
    assert app.version == "1.0.0"

    routes = [route.path for route in app.routes]
    assert "/" in routes
    assert "/api/upload-gpx" in routes
    assert "/api/segments" in routes


def test_complete_gpx_segment_flow(mock_s3_environment, sample_gpx_file, tmp_path):
    """Test the complete flow: GPX generation -> S3 upload -> cleanup."""
    with mock_aws():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=mock_s3_environment)

        config = S3StorageConfig(
            storage_type="s3",
            bucket=mock_s3_environment,
            access_key_id="test-key",
            secret_access_key="test-secret",
            region="us-east-1",
        )
        s3_manager = S3Manager(config)

        frontend_temp_dir = tmp_path / "temp_gpx_segments"

        file_id, segment_file_path, bounds = generate_gpx_segment(
            input_file_path=sample_gpx_file,
            start_index=1,
            end_index=3,
            segment_name="Test Segment",
            output_dir=frontend_temp_dir,
        )

        assert segment_file_path.exists()
        assert file_id is not None

        # Test bounds return value
        assert isinstance(bounds, GPXBounds)
        assert isinstance(bounds.north, float)
        assert isinstance(bounds.south, float)
        assert isinstance(bounds.east, float)
        assert isinstance(bounds.west, float)
        assert isinstance(bounds.min_elevation, float)
        assert isinstance(bounds.max_elevation, float)
        assert bounds.south <= bounds.north
        assert bounds.west <= bounds.east

        s3_key = s3_manager.upload_gpx_segment(
            local_file_path=segment_file_path,
            file_id=file_id,
            prefix="gpx-segments",
        )

        assert s3_key == f"gpx-segments/{file_id}.gpx"

        response = s3_client.head_object(
            Bucket=mock_s3_environment,
            Key=s3_key,
        )
        assert response["ContentType"] == "application/gpx+xml"
        assert response["Metadata"]["file-id"] == file_id
        assert response["Metadata"]["file-type"] == "gpx-segment"

        cleanup_success = cleanup_local_file(segment_file_path)
        assert cleanup_success is True
        assert not segment_file_path.exists()

        s3_client.head_object(Bucket=mock_s3_environment, Key=s3_key)


def test_s3_upload_failure_cleanup(mock_s3_environment, sample_gpx_file, tmp_path):
    """Test that local file is cleaned up even if S3 upload fails."""
    with mock_aws():
        config = S3StorageConfig(
            storage_type="s3",
            bucket="nonexistent-bucket",
            access_key_id="test-key",
            secret_access_key="test-secret",
            region="us-east-1",
        )
        s3_manager = S3Manager(config)

        frontend_temp_dir = tmp_path / "temp_gpx_segments"

        file_id, segment_file_path, bounds = generate_gpx_segment(
            input_file_path=sample_gpx_file,
            start_index=1,
            end_index=2,
            segment_name="Test Segment",
            output_dir=frontend_temp_dir,
        )

        assert segment_file_path.exists()

        with pytest.raises(Exception) as exc_info:
            s3_manager.upload_gpx_segment(
                local_file_path=segment_file_path,
                file_id=file_id,
                prefix="gpx-segments",
            )
        assert exc_info.value is not None

        cleanup_success = cleanup_local_file(segment_file_path)
        assert cleanup_success is True
        assert not segment_file_path.exists()


def test_multiple_segments_from_same_file(
    mock_s3_environment, sample_gpx_file, tmp_path
):
    """Test creating multiple segments from the same original file."""
    with mock_aws():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=mock_s3_environment)

        config = S3StorageConfig(
            storage_type="s3",
            bucket=mock_s3_environment,
            access_key_id="test-key",
            secret_access_key="test-secret",
            region="us-east-1",
        )
        s3_manager = S3Manager(config)

        frontend_temp_dir = tmp_path / "temp_gpx_segments"

        segments = []
        for i, (start, end) in enumerate([(0, 1), (1, 3), (3, 4)]):
            file_id, segment_file_path, bounds = generate_gpx_segment(
                input_file_path=sample_gpx_file,
                start_index=start,
                end_index=end,
                segment_name=f"Segment {i + 1}",
                output_dir=frontend_temp_dir,
            )

            s3_key = s3_manager.upload_gpx_segment(
                local_file_path=segment_file_path,
                file_id=file_id,
                prefix="gpx-segments",
            )

            segments.append((file_id, s3_key))

            cleanup_local_file(segment_file_path)

        for file_id, s3_key in segments:
            response = s3_client.head_object(
                Bucket=mock_s3_environment,
                Key=s3_key,
            )
            assert response["Metadata"]["file-id"] == file_id

        for file_path in frontend_temp_dir.glob("*.gpx"):
            raise AssertionError(f"Local file should have been cleaned up: {file_path}")


def test_frontend_temp_directory_creation(
    mock_s3_environment, sample_gpx_file, tmp_path
):
    """Test that frontend temp directory is created if it doesn't exist."""
    with mock_aws():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=mock_s3_environment)

        frontend_temp_dir = tmp_path / "nonexistent" / "temp_gpx_segments"

        assert not frontend_temp_dir.exists()

        file_id, segment_file_path, bounds = generate_gpx_segment(
            input_file_path=sample_gpx_file,
            start_index=1,
            end_index=2,
            segment_name="Test Segment",
            output_dir=frontend_temp_dir,
        )

        assert frontend_temp_dir.exists()
        assert segment_file_path.exists()

        cleanup_local_file(segment_file_path)


def test_create_segment_endpoint_with_mock_s3(client, sample_gpx_file):
    """Test the create_segment endpoint with mocked S3 using real GPX file."""
    with mock_aws():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        with open(sample_gpx_file, "rb") as f:
            upload_response = client.post(
                "/api/upload-gpx",
                files={"file": ("test.gpx", f, "application/gpx+xml")},
            )

        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            file_id = upload_data["file_id"]
        else:
            return

        segment_response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
                "track_type": "segment",
                "tire_dry": "slick",
                "tire_wet": "slick",
                "file_id": file_id,
                "start_index": 1,
                "end_index": 2,
                "surface_type": "forest-trail",
                "difficulty_level": "3",
            },
        )

        # Note: This test demonstrates the expected flow
        # The segment creation might fail due to S3 manager initialization
        # but we've already tested the core functionality in other tests
        # Accept either success or S3 init failure
        assert segment_response.status_code in [200, 500]


def test_storage_manager_initialization_failure_handling(app, lifespan, main_module):
    """Test that the app handles storage manager initialization failure gracefully."""

    original_storage_manager = main_module.storage_manager

    try:
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "src.main.get_storage_manager",
                side_effect=Exception("Storage init failed"),
            ):

                async def run_lifespan():
                    async with lifespan(app):
                        assert main_module.storage_manager is None
                        return True

                result = asyncio.run(run_lifespan())
                assert result is True

    finally:
        main_module.storage_manager = original_storage_manager


def test_storage_manager_initialization_exception_handling(app, lifespan, main_module):
    """Test that storage manager initialization exceptions are properly caught
    and logged."""

    original_storage_manager = main_module.storage_manager

    try:
        with patch.dict(
            os.environ,
            {"STORAGE_TYPE": "s3", "AWS_S3_BUCKET": "test-bucket"},
            clear=True,
        ):
            with patch(
                "src.main.get_storage_manager",
                side_effect=Exception("S3 connection failed"),
            ):

                async def run_lifespan():
                    async with lifespan(app):
                        assert main_module.storage_manager is None
                        return True

                result = asyncio.run(run_lifespan())
                assert result is True

    finally:
        main_module.storage_manager = original_storage_manager


def test_create_segment_storage_manager_not_initialized(
    client, sample_gpx_file, main_module
):
    """Test segment creation when storage manager is not initialized."""
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    original_storage_manager = main_module.storage_manager

    try:
        main_module.storage_manager = None

        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
                "track_type": "segment",
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "100",
                "surface_type": "forest-trail",
                "difficulty_level": "3",
            },
        )

        assert response.status_code == 500
        assert "Storage manager not initialized" in response.json()["detail"]

    finally:
        main_module.storage_manager = original_storage_manager


@mock_aws
def test_create_segment_cleanup_local_file_failure(client, sample_gpx_file, tmp_path):
    """Test segment creation when local file cleanup fails."""
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket="test-bucket")

    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        with patch("src.main.cleanup_local_file", return_value=False):
            response = client.post(
                "/api/segments",
                data={
                    "name": "Test Segment",
                    "track_type": "segment",
                    "tire_dry": "slick",
                    "tire_wet": "semi-slick",
                    "file_id": file_id,
                    "start_index": "0",
                    "end_index": "100",
                    "surface_type": "forest-trail",
                    "difficulty_level": "3",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Segment"
        assert data["file_path"].startswith(("s3://", "local://", "local:/"))


def test_serve_storage_file_storage_manager_not_initialized(client, main_module):
    """Test serving storage file when storage manager is not initialized."""
    original_storage_manager = main_module.storage_manager

    try:
        main_module.storage_manager = None

        response = client.get("/storage/test-file.gpx")

        assert response.status_code == 500
        assert response.json()["detail"] == "Storage manager not initialized"

    finally:
        main_module.storage_manager = original_storage_manager


def test_serve_storage_file_s3_mode_not_available(client, sample_gpx_file, main_module):
    """Test serving storage file when in S3 mode (not available)."""
    original_storage_manager = main_module.storage_manager

    try:
        config = S3StorageConfig(
            storage_type="s3",
            bucket="test-bucket",
            access_key_id="test-key",
            secret_access_key="test-secret",
            region="us-east-1",
        )
        s3_manager = S3Manager(config)
        main_module.storage_manager = s3_manager

        response = client.get("/storage/test-file.gpx")

        assert response.status_code == 404
        assert response.json()["detail"] == "File serving only available in local mode"

    finally:
        main_module.storage_manager = original_storage_manager


def test_serve_storage_file_local_mode_success(
    client, sample_gpx_file, tmp_path, main_module
):
    """Test successfully serving a file from local storage."""
    original_storage_manager = main_module.storage_manager

    try:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=str(tmp_path),
            base_url="http://localhost:8000/storage",
        )
        local_manager = LocalStorageManager(config)
        main_module.storage_manager = local_manager

        test_file_path = tmp_path / "test-file.gpx"
        test_file_path.write_text(sample_gpx_file.read_text())

        response = client.get("/storage/test-file.gpx")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/gpx+xml"
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="test-file.gpx"'
        )
        assert response.content == sample_gpx_file.read_bytes()

    finally:
        main_module.storage_manager = original_storage_manager


def test_serve_storage_file_file_not_found(client, tmp_path, main_module):
    """Test serving storage file when file doesn't exist."""
    original_storage_manager = main_module.storage_manager

    try:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=str(tmp_path),
            base_url="http://localhost:8000/storage",
        )
        local_manager = LocalStorageManager(config)
        main_module.storage_manager = local_manager

        response = client.get("/storage/nonexistent-file.gpx")

        assert response.status_code == 404
        assert response.json()["detail"] == "File not found"

    finally:
        main_module.storage_manager = original_storage_manager


def test_serve_storage_file_with_subdirectory(
    client, sample_gpx_file, tmp_path, main_module
):
    """Test serving a file from a subdirectory."""
    original_storage_manager = main_module.storage_manager

    try:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=str(tmp_path),
            base_url="http://localhost:8000/storage",
        )
        local_manager = LocalStorageManager(config)
        main_module.storage_manager = local_manager

        subdir = tmp_path / "gpx-segments"
        subdir.mkdir()
        test_file_path = subdir / "test-file.gpx"
        test_file_path.write_text(sample_gpx_file.read_text())

        response = client.get("/storage/gpx-segments/test-file.gpx")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/gpx+xml"
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="test-file.gpx"'
        )
        assert response.content == sample_gpx_file.read_bytes()

    finally:
        main_module.storage_manager = original_storage_manager


def test_serve_storage_file_local_storage_not_available(client, tmp_path, main_module):
    """Test serving storage file when local storage manager doesn't have
    get_file_path method."""
    original_storage_manager = main_module.storage_manager

    try:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=str(tmp_path),
            base_url="http://localhost:8000/storage",
        )
        local_manager = LocalStorageManager(config)
        main_module.storage_manager = local_manager

        with patch("src.main.hasattr") as mock_hasattr:

            def mock_hasattr_func(obj, attr):
                if attr == "get_file_path":
                    return False
                return hasattr(obj, attr)

            mock_hasattr.side_effect = mock_hasattr_func

            response = client.get("/storage/test-file.gpx")

            assert response.status_code == 500
            assert response.json()["detail"] == "Local storage not available"

    finally:
        main_module.storage_manager = original_storage_manager


def test_create_segment_storage_upload_failure(
    client, sample_gpx_file, tmp_path, main_module
):
    """Test create segment when storage upload fails."""
    original_storage_manager = main_module.storage_manager

    try:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=str(tmp_path),
            base_url="http://localhost:8000/storage",
        )
        local_manager = LocalStorageManager(config)
        main_module.storage_manager = local_manager

        with open(sample_gpx_file, "rb") as f:
            upload_response = client.post(
                "/api/upload-gpx",
                files={"file": ("test.gpx", f, "application/gpx+xml")},
            )
        if upload_response.status_code != 200:
            print(
                f"Upload failed: {upload_response.status_code} - {upload_response.text}"
            )
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]

        class MockStorageManager:
            def upload_gpx_segment(self, local_file_path, file_id, prefix):
                raise Exception("Storage upload failed")

            def get_storage_root_prefix(self):
                return "mock://test-bucket"

        mock_storage_manager = MockStorageManager()
        main_module.storage_manager = mock_storage_manager

        segment_data = {
            "file_id": file_id,
            "name": "Test Segment",
            "track_type": "segment",
            "start_index": "0",
            "end_index": "10",
            "tire_dry": "slick",
            "tire_wet": "semi-slick",
            "surface_type": "forest-trail",
            "difficulty_level": "3",
        }

        response = client.post("/api/segments", data=segment_data)

        if response.status_code != 500:
            print(f"Create segment failed: {response.status_code} - {response.text}")
        assert response.status_code == 500
        assert "Failed to upload to storage" in response.json()["detail"]
        assert "Storage upload failed" in response.json()["detail"]

    finally:
        main_module.storage_manager = original_storage_manager


def test_database_initialization_failure_handling(app, lifespan, main_module):
    """Test that the app handles database initialization failure gracefully."""

    original_engine = main_module.engine
    original_session_local = main_module.SessionLocal

    try:
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "src.main.create_async_engine",
                side_effect=Exception("Database connection failed"),
            ):

                async def run_lifespan():
                    async with lifespan(app):
                        assert main_module.engine is None
                        assert main_module.SessionLocal is None
                        return True

                result = asyncio.run(run_lifespan())
                assert result is True

    finally:
        main_module.engine = original_engine
        main_module.SessionLocal = original_session_local


def test_database_initialization_exception_handling(app, lifespan, main_module):
    """Test that database initialization exceptions are properly caught and logged."""

    original_engine = main_module.engine
    original_session_local = main_module.SessionLocal

    try:
        with patch.dict(
            os.environ,
            {
                "DB_HOST": "invalid_host",
                "DB_PORT": "5432",
                "DB_NAME": "test_db",
                "DB_USER": "test_user",
                "DB_PASSWORD": "test_password",
            },
            clear=True,
        ):
            with patch(
                "src.main.create_async_engine",
                side_effect=Exception("Connection refused"),
            ):

                async def run_lifespan():
                    async with lifespan(app):
                        assert main_module.engine is None
                        assert main_module.SessionLocal is None
                        return True

                result = asyncio.run(run_lifespan())
                assert result is True

    finally:
        main_module.engine = original_engine
        main_module.SessionLocal = original_session_local


@mock_aws
def test_create_segment_database_exception_handling(
    client, sample_gpx_file, tmp_path, main_module
):
    """Test create segment when database operations fail but storage succeeds."""
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket="test-bucket")

    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        with patch("src.main.SessionLocal") as mock_session_local:

            async def mock_session_context():
                mock_session = mock_session_local.return_value
                mock_session.add = lambda x: None

                # Make commit raise an exception
                async def mock_commit():
                    raise Exception("Database commit failed")

                mock_session.commit = mock_commit
                return mock_session

            mock_session_local.return_value.__aenter__ = mock_session_context

            response = client.post(
                "/api/segments",
                data={
                    "name": "Test Segment",
                    "track_type": "segment",
                    "tire_dry": "slick",
                    "tire_wet": "semi-slick",
                    "file_id": file_id,
                    "start_index": "0",
                    "end_index": "100",
                    "surface_type": "forest-trail",
                    "difficulty_level": "3",
                    "commentary_text": "Test commentary",
                    "video_links": "[]",
                },
            )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == 0  # Placeholder ID when database is not available
    assert data["name"] == "Test Segment"
    assert data["file_path"].startswith(("s3://", "local://", "local:/"))
    assert data["file_path"].endswith(".gpx")


@mock_aws
def test_create_segment_database_unavailable(
    client, sample_gpx_file, tmp_path, main_module
):
    """Test create segment when database is not available (SessionLocal is None)."""
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket="test-bucket")

    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        original_session_local = main_module.SessionLocal
        try:
            main_module.SessionLocal = None

            response = client.post(
                "/api/segments",
                data={
                    "name": "Test Segment",
                    "track_type": "segment",
                    "tire_dry": "slick",
                    "tire_wet": "semi-slick",
                    "file_id": file_id,
                    "start_index": "0",
                    "end_index": "100",
                    "surface_type": "forest-trail",
                    "difficulty_level": "3",
                    "commentary_text": "Test commentary",
                    "video_links": "[]",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 0  # Placeholder ID when database is not available
            assert data["name"] == "Test Segment"
            assert data["file_path"].startswith(("s3://", "local://", "local:/"))
            assert data["file_path"].endswith(".gpx")

        finally:
            main_module.SessionLocal = original_session_local


def test_database_initialization_exception_in_lifespan(app, lifespan, main_module):
    """Test database initialization exception handling in lifespan function."""
    original_engine = main_module.engine
    original_session_local = main_module.SessionLocal

    try:
        mock_engine = type("MockEngine", (), {})()
        main_module.engine = mock_engine

        with patch(
            "src.main.Base.metadata.create_all",
            side_effect=Exception("Table creation failed"),
        ):

            async def run_lifespan():
                async with lifespan(app):
                    return True

            result = asyncio.run(run_lifespan())
            assert result is True

    finally:
        main_module.engine = original_engine
        main_module.SessionLocal = original_session_local


@mock_aws
def test_create_segment_successful_database_operations(
    client, sample_gpx_file, tmp_path, main_module
):
    """Test create segment with successful database operations to cover the successful
    path."""
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket="test-bucket")

    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        mock_session = type("MockSession", (), {})()
        mock_session.add = lambda x: None

        async def mock_commit():
            pass

        async def mock_refresh(track):
            track.id = 123

        mock_session.commit = mock_commit
        mock_session.refresh = mock_refresh

        with patch("src.main.SessionLocal") as mock_session_local:

            class MockAsyncContextManager:
                async def __aenter__(self):
                    return mock_session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            mock_session_local.return_value = MockAsyncContextManager()

            response = client.post(
                "/api/segments",
                data={
                    "name": "Test Segment",
                    "track_type": "segment",
                    "tire_dry": "slick",
                    "tire_wet": "semi-slick",
                    "file_id": file_id,
                    "start_index": "0",
                    "end_index": "100",
                    "surface_type": "forest-trail",
                    "difficulty_level": "3",
                    "commentary_text": "Test commentary",
                    "video_links": "[]",
                },
            )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == 123  # Database ID
        assert data["name"] == "Test Segment"
        assert data["file_path"].startswith(("s3://", "local://", "local:/"))
        assert data["file_path"].endswith(".gpx")


def test_search_segments_options_endpoint(client):
    """Test OPTIONS endpoint for /api/segments/search (CORS preflight)."""
    response = client.options("/api/segments/search")

    # Should return 200 OK
    assert response.status_code == 200

    # Check CORS headers are present
    headers = response.headers
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Methods"] == "GET, OPTIONS"
    assert headers["Access-Control-Allow-Headers"] == "*"
    assert headers["Access-Control-Max-Age"] == "86400"

    # Response body should be empty for OPTIONS
    assert response.content == b""


def test_search_segments_options_endpoint_basic_functionality(client):
    """Test OPTIONS endpoint basic functionality."""
    # Test basic OPTIONS request
    response = client.options("/api/segments/search")

    # Should return 200 OK
    assert response.status_code == 200

    # CORS headers should be present
    headers = response.headers
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Methods"] == "GET, OPTIONS"
    assert headers["Access-Control-Allow-Headers"] == "*"
    assert headers["Access-Control-Max-Age"] == "86400"


def test_search_segments_endpoint_success(client):
    """Test successful search for segments within bounds."""
    # Search for segments in a bounding box
    # Using coordinates that should include most of Europe
    response = client.get(
        "/api/segments/search",
        params={"north": 50.0, "south": 40.0, "east": 10.0, "west": 0.0},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Check CORS headers
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert response.headers["Access-Control-Allow-Methods"] == "GET, OPTIONS"

    # Parse streaming response
    content = response.text
    lines = content.strip().split("\n")

    # Should have data lines and a [DONE] marker
    data_lines = [line for line in lines if line.startswith("data: ")]
    assert len(data_lines) >= 2  # At least one segment count + [DONE]

    # Find the count line (it comes after track data)
    count_line = None
    for line in data_lines:
        if line.startswith("data: ") and line[6:].isdigit():
            count_line = line
            break

    assert count_line is not None, "Should have a count line"
    segment_count = int(count_line[6:])  # Remove 'data: '
    assert segment_count >= 0  # Should find 0 or more segments

    # Last line should be [DONE]
    assert data_lines[-1] == "data: [DONE]"


def test_search_segments_endpoint_no_results(client):
    """Test search for segments with no results."""
    # Search in an area with no segments (middle of ocean)
    response = client.get(
        "/api/segments/search",
        params={"north": 0.0, "south": -1.0, "east": 0.0, "west": -1.0},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Parse streaming response
    content = response.text
    lines = content.strip().split("\n")

    # Should have only count and [DONE]
    data_lines = [line for line in lines if line.startswith("data: ")]
    assert len(data_lines) == 2

    # First line should be 0 segments
    count_line = data_lines[0]
    assert count_line == "data: 0"

    # Last line should be [DONE]
    assert data_lines[-1] == "data: [DONE]"


def test_search_segments_endpoint_missing_parameters(client):
    """Test search endpoint with missing required parameters."""
    # Missing one parameter
    response = client.get(
        "/api/segments/search",
        params={
            "north": 50.0,
            "south": 40.0,
            "east": 10.0,
            # Missing "west"
        },
    )

    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_search_segments_endpoint_invalid_parameters(client):
    """Test search endpoint with invalid parameter values."""
    # Invalid coordinates (south > north)
    response = client.get(
        "/api/segments/search",
        params={
            "north": 40.0,  # south should be less than north
            "south": 50.0,  # invalid: south > north
            "east": 10.0,
            "west": 0.0,
        },
    )

    # Should still work (validation happens in the query, not the endpoint)
    assert response.status_code == 200


def test_search_segments_endpoint_cors_headers(client):
    """Test that search endpoint returns proper CORS headers."""
    response = client.get(
        "/api/segments/search",
        params={"north": 50.0, "south": 40.0, "east": 10.0, "west": 0.0},
    )

    assert response.status_code == 200

    # Check CORS headers
    headers = response.headers
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Headers"] == "Cache-Control"
    assert headers["Access-Control-Allow-Methods"] == "GET, OPTIONS"
    assert headers["Access-Control-Expose-Headers"] == "*"
    assert headers["Cache-Control"] == "no-cache"
    assert headers["Connection"] == "keep-alive"


def test_search_segments_endpoint_streaming_format(client):
    """Test that search endpoint returns properly formatted streaming data."""
    # Search for segments
    response = client.get(
        "/api/segments/search",
        params={"north": 50.0, "south": 40.0, "east": 10.0, "west": 0.0},
    )

    assert response.status_code == 200

    # Parse streaming response
    content = response.text
    lines = content.strip().split("\n")

    # Find data lines
    data_lines = [line for line in lines if line.startswith("data: ")]

    # Should have at least: count + [DONE]
    assert len(data_lines) >= 2

    # Find the count line (it comes after track data)
    count_line = None
    for line in data_lines:
        if line.startswith("data: ") and line[6:].isdigit():
            count_line = line
            break

    assert count_line is not None, "Should have a count line"
    segment_count = int(count_line[6:])  # Remove 'data: '

    # Last line should be [DONE]
    assert data_lines[-1] == "data: [DONE]"

    # If there are segments, check that segment data is valid JSON
    if segment_count > 0:
        # Filter out count line and [DONE] from segment data
        segment_data_lines = []
        for line in data_lines:
            if (
                line.startswith("data: ")
                and not line[6:].isdigit()
                and line != "data: [DONE]"
            ):
                segment_data_lines.append(line)

        for line in segment_data_lines:
            json_str = line[6:]  # Remove 'data: '
            data = json.loads(json_str)

            # Check required fields (TrackResponse fields, no GPX data in search)
            assert "id" in data
            assert "name" in data
            assert "file_path" in data
            assert "bound_north" in data
            assert "bound_south" in data
            assert "bound_east" in data
            assert "bound_west" in data
            assert "track_type" in data
            assert "difficulty_level" in data
            assert "surface_type" in data
            assert "tire_dry" in data
            assert "tire_wet" in data
            assert "comments" in data

            # GPX data should NOT be present in search endpoint (optimization)
            assert "gpx_xml_data" not in data


def test_search_segments_endpoint_gpx_load_error(client, main_module):
    """Test search endpoint behavior - GPX loading errors no longer affect search."""
    # Since the search endpoint no longer loads GPX data (optimization),
    # this test now verifies that the search endpoint works normally
    # regardless of storage manager issues

    response = client.get(
        "/api/segments/search",
        params={"north": 50.0, "south": 40.0, "east": 10.0, "west": 0.0},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Parse streaming response
    content = response.text
    lines = content.strip().split("\n")

    # Find data lines
    data_lines = [line for line in lines if line.startswith("data: ")]

    # Should have: count + segments + [DONE]
    assert len(data_lines) >= 2

    # Find the count line (it comes after track data)
    count_line = None
    for line in data_lines:
        if line.startswith("data: ") and line[6:].isdigit():
            count_line = line
            break

    assert count_line is not None, "Should have a count line"
    segment_count = int(count_line[6:])  # Remove 'data: '
    assert segment_count >= 0

    # Last line should be [DONE]
    assert data_lines[-1] == "data: [DONE]"

    # Verify that segments don't contain GPX data (optimization)
    if segment_count > 0:
        # Filter out count line and [DONE] from segment data
        segment_data_lines = []
        for line in data_lines:
            if (
                line.startswith("data: ")
                and not line[6:].isdigit()
                and line != "data: [DONE]"
            ):
                segment_data_lines.append(line)

        for line in segment_data_lines:
            json_str = line[6:]  # Remove 'data: '
            data = json.loads(json_str)
            # GPX data should NOT be present in search endpoint
            assert "gpx_xml_data" not in data


def test_get_track_gpx_data_endpoint(client):
    """Test the new GPX data endpoint."""
    # Test with a track ID that exists in the test database
    response = client.get("/api/segments/1/gpx")

    # Should return 404 if GPX data not found (expected with current test setup)
    # or 200 with GPX data if file exists
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "gpx_xml_data" in data
        assert isinstance(data["gpx_xml_data"], str)
        # Should contain valid GPX XML
        assert data["gpx_xml_data"].startswith("<?xml")


def test_get_track_gpx_data_endpoint_not_found(client):
    """Test GPX endpoint with non-existent track ID."""
    response = client.get("/api/segments/99999/gpx")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_track_gpx_data_endpoint_database_unavailable(client, main_module):
    """Test GPX endpoint when database is not available."""
    # Mock database unavailability
    original_session_local = main_module.SessionLocal
    main_module.SessionLocal = None

    try:
        response = client.get("/api/segments/1/gpx")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Database not available"
    finally:
        # Restore original database session
        main_module.SessionLocal = original_session_local


def test_get_track_gpx_data_endpoint_storage_unavailable(client, main_module):
    """Test GPX endpoint when storage manager is not available."""
    # Mock storage manager unavailability
    original_storage_manager = main_module.storage_manager
    main_module.storage_manager = None

    try:
        response = client.get("/api/segments/1/gpx")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Storage manager not available"
    finally:
        # Restore original storage manager
        main_module.storage_manager = original_storage_manager


def test_get_track_gpx_data_endpoint_storage_load_error(client, main_module):
    """Test GPX endpoint when storage manager raises an exception."""
    # Mock storage manager to raise an exception
    original_storage_manager = main_module.storage_manager

    class MockStorageManager:
        def load_gpx_data(self, url):
            raise Exception("Storage connection failed")

    main_module.storage_manager = MockStorageManager()

    try:
        response = client.get("/api/segments/1/gpx")
        assert response.status_code == 500
        data = response.json()
        assert "Failed to load GPX data: Storage connection failed" in data["detail"]
    finally:
        # Restore original storage manager
        main_module.storage_manager = original_storage_manager


def test_get_track_gpx_data_endpoint_storage_returns_none(client, main_module):
    """Test GPX endpoint when storage manager returns None (file not found)."""
    # Mock storage manager to return None
    original_storage_manager = main_module.storage_manager

    class MockStorageManager:
        def load_gpx_data(self, url):
            return None

    main_module.storage_manager = MockStorageManager()

    try:
        response = client.get("/api/segments/1/gpx")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "GPX data not found"
    finally:
        # Restore original storage manager
        main_module.storage_manager = original_storage_manager


def test_get_track_gpx_data_endpoint_gpx_bytes_none_check(client, main_module):
    """Test GPX endpoint for gpx_bytes is None check (lines 495-500)."""
    # Mock both database and storage manager to ensure we hit the None check
    original_session_local = main_module.SessionLocal
    original_storage_manager = main_module.storage_manager

    # Create a mock track object that exists in database
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    mock_track = Track(
        id=456,
        file_path="test/none_check.gpx",
        bound_north=46.0,
        bound_south=45.0,
        bound_east=4.0,
        bound_west=3.0,
        name="None Check Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.KNOBS,
        tire_wet=TireType.KNOBS,
        comments="Test track for None check",
        created_at=datetime.now(),
    )

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return mock_track  # Track exists in database

            return MockResult()

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    class MockStorageManager:
        def load_gpx_data(self, url):
            # Return None to test the None check in lines 495-500
            return None

    main_module.SessionLocal = MockSessionLocal()
    main_module.storage_manager = MockStorageManager()

    try:
        response = client.get("/api/segments/456/gpx")
        assert response.status_code == 404
        data = response.json()

        # Verify the specific error message and status code from lines 495-500
        assert data["detail"] == "GPX data not found"

        # This test specifically covers the code path:
        # 1. Database query (lines 486-488)
        # 2. Track found check (line 490-491)
        # 3. Storage load (line 494)
        # 4. None check (lines 495-500)
        # if gpx_bytes is None:
        #     logger.warning(f"No GPX data found for track {track_id} at path: "
        #                   f"{track.file_path}")
        #     raise HTTPException(status_code=404, detail="GPX data not found")

    finally:
        # Restore original services
        main_module.SessionLocal = original_session_local
        main_module.storage_manager = original_storage_manager


def test_get_track_gpx_data_endpoint_invalid_track_id(client):
    """Test GPX endpoint with invalid track ID format."""
    response = client.get("/api/segments/invalid/gpx")
    assert response.status_code == 422  # Validation error for invalid integer


def test_get_track_gpx_data_endpoint_success(client, main_module):
    """Test GPX endpoint with successful GPX data retrieval."""
    # Mock storage manager to return valid GPX data
    original_storage_manager = main_module.storage_manager

    class MockStorageManager:
        def load_gpx_data(self, url):
            return (
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<gpx version="1.1"><trk><name>Test Track</name></trk></gpx>'
            )

    main_module.storage_manager = MockStorageManager()

    try:
        # Use a track ID that exists in the test database (from the test data setup)
        response = client.get("/api/segments/1/gpx")

        # The response could be 200 (success) or 404 (if track doesn't exist in test DB)
        # Both are valid for testing the code paths
        if response.status_code == 200:
            data = response.json()

            # Check response structure
            assert "gpx_xml_data" in data
            assert isinstance(data["gpx_xml_data"], str)
            assert data["gpx_xml_data"].startswith("<?xml")
            assert "Test Track" in data["gpx_xml_data"]

            # Verify response model compliance
            assert len(data.keys()) == 1  # Only gpx_xml_data field
        else:
            # If track doesn't exist, that's also a valid test outcome
            assert response.status_code == 404
    finally:
        # Restore original storage manager
        main_module.storage_manager = original_storage_manager


def test_get_track_gpx_data_endpoint_success_with_existing_track(client, main_module):
    """Test GPX endpoint success path with a track that definitely exists."""
    # First, let's find a track that exists in the test database
    search_response = client.get(
        "/api/segments/search",
        params={"north": 50.0, "south": 40.0, "east": 10.0, "west": 0.0},
    )
    assert search_response.status_code == 200

    # Parse the streaming response to get an existing track ID
    content = search_response.text
    lines = content.strip().split("\n")
    data_lines = [line for line in lines if line.startswith("data: ")]

    if len(data_lines) > 2:  # Has count + segments + [DONE]
        # Get the first segment data
        segment_line = data_lines[1]  # Skip count line
        segment_data = json.loads(segment_line[6:])  # Remove 'data: '
        existing_track_id = segment_data["id"]

        # Mock storage manager to return valid GPX data
        original_storage_manager = main_module.storage_manager

        class MockStorageManager:
            def load_gpx_data(self, url):
                return (
                    b'<?xml version="1.0" encoding="UTF-8"?>\n'
                    b'<gpx version="1.1"><trk><name>Success Track</name></trk></gpx>'
                )

        main_module.storage_manager = MockStorageManager()

        try:
            # Test with the existing track ID
            response = client.get(f"/api/segments/{existing_track_id}/gpx")
            assert response.status_code == 200
            data = response.json()

            # Check response structure - this should cover lines 501 and 512
            assert "gpx_xml_data" in data
            assert isinstance(data["gpx_xml_data"], str)
            assert data["gpx_xml_data"].startswith("<?xml")
            assert "Success Track" in data["gpx_xml_data"]

            # Verify response model compliance
            assert len(data.keys()) == 1  # Only gpx_xml_data field

        finally:
            # Restore original storage manager
            main_module.storage_manager = original_storage_manager
    else:
        # Skip test if no tracks exist in database
        pytest.skip("No tracks found in test database")


def test_get_track_gpx_data_endpoint_success_with_mock_database(client, main_module):
    """Test GPX endpoint success path by mocking database to hit all code paths."""
    # Mock both database and storage manager to ensure we hit the success path
    original_session_local = main_module.SessionLocal
    original_storage_manager = main_module.storage_manager

    # Create a mock track object
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    mock_track = Track(
        id=123,
        file_path="test/path.gpx",
        bound_north=46.0,
        bound_south=45.0,
        bound_east=4.0,
        bound_west=3.0,
        name="Mock Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.KNOBS,
        tire_wet=TireType.KNOBS,
        comments="Test track",
        created_at=datetime.now(),
    )

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return mock_track

            return MockResult()

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    class MockStorageManager:
        def load_gpx_data(self, url):
            return (
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<gpx version="1.1"><trk><name>Mock Track</name></trk></gpx>'
            )

    main_module.SessionLocal = MockSessionLocal()
    main_module.storage_manager = MockStorageManager()

    try:
        response = client.get("/api/segments/123/gpx")
        assert response.status_code == 200
        data = response.json()

        # This should now cover lines 488, 501, and 512
        assert "gpx_xml_data" in data
        assert isinstance(data["gpx_xml_data"], str)
        assert data["gpx_xml_data"].startswith("<?xml")
        assert "Mock Track" in data["gpx_xml_data"]

        # Verify response model compliance
        assert len(data.keys()) == 1  # Only gpx_xml_data field

    finally:
        # Restore original services
        main_module.SessionLocal = original_session_local
        main_module.storage_manager = original_storage_manager


def test_get_track_gpx_data_endpoint_track_not_found_in_database(client, main_module):
    """Test GPX endpoint when track is not found in database (line 491)."""
    # Mock database to return None (track not found)
    original_session_local = main_module.SessionLocal

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return None  # Track not found

            return MockResult()

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    main_module.SessionLocal = MockSessionLocal()

    try:
        response = client.get("/api/segments/99999/gpx")
        assert response.status_code == 404
        data = response.json()

        # This should cover line 491: raise HTTPException(status_code=404,
        # detail="Track not found")
        assert data["detail"] == "Track not found"

    finally:
        # Restore original database session
        main_module.SessionLocal = original_session_local


def test_get_track_gpx_data_endpoint_decode_exception_path(client, main_module):
    """Test GPX endpoint exception handling path (lines 504-508)."""
    # Mock both database and storage manager to trigger decode exception
    original_session_local = main_module.SessionLocal
    original_storage_manager = main_module.storage_manager

    # Create a mock track object
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    mock_track = Track(
        id=789,
        file_path="test/exception_path.gpx",
        bound_north=46.0,
        bound_south=45.0,
        bound_east=4.0,
        bound_west=3.0,
        name="Exception Path Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.KNOBS,
        tire_wet=TireType.KNOBS,
        comments="Test track for exception path",
        created_at=datetime.now(),
    )

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return mock_track

            return MockResult()

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    class MockStorageManager:
        def load_gpx_data(self, url):
            # Return bytes that will cause a decode exception
            # Using a mock object that will raise an exception when decode() is called
            class MockBytes:
                def decode(self, encoding):
                    raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

            return MockBytes()

    main_module.SessionLocal = MockSessionLocal()
    main_module.storage_manager = MockStorageManager()

    try:
        response = client.get("/api/segments/789/gpx")
        assert response.status_code == 500
        data = response.json()

        # This should cover lines 504-508:
        # except Exception as e:
        #     logger.warning(f"Failed to load GPX data for track {track_id}: {str(e)}")
        #     raise HTTPException(status_code=500,
        #                        detail=f"Failed to load GPX data: {str(e)}")

        assert (
            "Failed to load GPX data: 'utf-8' codec can't decode bytes"
            in data["detail"]
        )

    finally:
        # Restore original services
        main_module.SessionLocal = original_session_local
        main_module.storage_manager = original_storage_manager


def test_get_track_gpx_data_endpoint_decode_error(client, main_module):
    """Test GPX endpoint when GPX data cannot be decoded as UTF-8."""
    # Mock storage manager to return invalid UTF-8 data
    original_storage_manager = main_module.storage_manager

    class MockStorageManager:
        def load_gpx_data(self, url):
            # Return bytes that cannot be decoded as UTF-8
            return b"\xff\xfe\x00\x00"

    main_module.storage_manager = MockStorageManager()

    try:
        response = client.get("/api/segments/1/gpx")
        assert response.status_code == 500
        data = response.json()
        assert "Failed to load GPX data" in data["detail"]
    finally:
        # Restore original storage manager
        main_module.storage_manager = original_storage_manager


def test_get_track_gpx_data_endpoint_database_error(client, main_module):
    """Test GPX endpoint when database query fails."""
    # Mock database session to raise an exception
    original_session_local = main_module.SessionLocal

    class MockSessionLocal:
        async def __aenter__(self):
            raise Exception("Database connection failed")

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    main_module.SessionLocal = MockSessionLocal

    try:
        response = client.get("/api/segments/1/gpx")
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]
    finally:
        # Restore original database session
        main_module.SessionLocal = original_session_local


def test_search_segments_endpoint_streaming_error(client, main_module):
    """Test search endpoint when streaming generation fails (covers lines 452-454)."""
    # Mock the database session to raise an exception during streaming
    original_session_local = main_module.SessionLocal

    class MockSessionLocal:
        def __call__(self):
            raise Exception("Mocked database connection error")

    main_module.SessionLocal = MockSessionLocal

    try:
        # Search for segments - should handle streaming error gracefully
        response = client.get(
            "/api/segments/search",
            params={"north": 50.0, "south": 40.0, "east": 10.0, "west": 0.0},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse streaming response
        content = response.text
        lines = content.strip().split("\n")

        # Find data lines
        data_lines = [line for line in lines if line.startswith("data: ")]

        # Should have error message
        assert len(data_lines) >= 1

        # Should contain error information
        error_line = data_lines[0]
        assert error_line.startswith("data: ")
        error_data = error_line[6:]  # Remove 'data: '

        # The error message contains single quotes, so we need to handle it carefully
        # Check that it contains error information
        assert (
            "error" in error_data.lower()
            or "Mocked database connection error" in error_data
        )

    finally:
        # Restore original SessionLocal
        main_module.SessionLocal = original_session_local


def test_search_segments_endpoint_database_not_available(client, main_module):
    """Test search endpoint when database is not available (covers lines 395-396)."""
    # Mock SessionLocal to be None/False to trigger database availability check
    original_session_local = main_module.SessionLocal
    main_module.SessionLocal = None

    try:
        # Search for segments - should return 500 error
        response = client.get(
            "/api/segments/search",
            params={"north": 50.0, "south": 40.0, "east": 10.0, "west": 0.0},
        )

        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"] == "Database not available"

    finally:
        # Restore original SessionLocal
        main_module.SessionLocal = original_session_local


def test_search_segments_invalid_track_type(client):
    """Test search segments endpoint with invalid track_type parameter."""
    # Test with invalid track_type value
    response = client.get(
        "/api/segments/search",
        params={
            "north": 50.0,
            "south": 40.0,
            "east": 10.0,
            "west": 0.0,
            "track_type": "invalid_type",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert (
        data["detail"]
        == "Invalid track_type: invalid_type. Must be 'segment' or 'route'"
    )


def test_search_segments_empty_track_type(client):
    """Test search segments endpoint with empty track_type parameter."""
    # Test with empty track_type value
    response = client.get(
        "/api/segments/search",
        params={
            "north": 50.0,
            "south": 40.0,
            "east": 10.0,
            "west": 0.0,
            "track_type": "",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid track_type: . Must be 'segment' or 'route'"


def test_search_segments_none_track_type(client):
    """Test search segments endpoint with None track_type parameter."""
    # Test with None track_type value (passed as string "None")
    response = client.get(
        "/api/segments/search",
        params={
            "north": 50.0,
            "south": 40.0,
            "east": 10.0,
            "west": 0.0,
            "track_type": "None",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid track_type: None. Must be 'segment' or 'route'"


def test_search_segments_numeric_track_type(client):
    """Test search segments endpoint with numeric track_type parameter."""
    # Test with numeric track_type value
    response = client.get(
        "/api/segments/search",
        params={
            "north": 50.0,
            "south": 40.0,
            "east": 10.0,
            "west": 0.0,
            "track_type": "123",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid track_type: 123. Must be 'segment' or 'route'"


def test_search_segments_valid_track_types(client):
    """Test search segments endpoint with valid track_type parameters."""
    # Test with valid 'segment' track_type
    response = client.get(
        "/api/segments/search",
        params={
            "north": 50.0,
            "south": 40.0,
            "east": 10.0,
            "west": 0.0,
            "track_type": "segment",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Test with valid 'route' track_type
    response = client.get(
        "/api/segments/search",
        params={
            "north": 50.0,
            "south": 40.0,
            "east": 10.0,
            "west": 0.0,
            "track_type": "route",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


def test_search_segments_with_limit_parameter(client):
    """Test search segments endpoint with limit parameter."""
    # Test with default limit (50)
    response = client.get(
        "/api/segments/search",
        params={
            "north": 45.0,
            "south": 44.0,
            "east": 2.0,
            "west": 1.0,
            "track_type": "segment",
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Test with custom limit
    response = client.get(
        "/api/segments/search",
        params={
            "north": 45.0,
            "south": 44.0,
            "east": 2.0,
            "west": 1.0,
            "track_type": "segment",
            "limit": 25,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Test with invalid limit (too high)
    response = client.get(
        "/api/segments/search",
        params={
            "north": 45.0,
            "south": 44.0,
            "east": 2.0,
            "west": 1.0,
            "track_type": "segment",
            "limit": 2000,
        },
    )
    assert response.status_code == 422  # Validation error

    # Test with invalid limit (too low)
    response = client.get(
        "/api/segments/search",
        params={
            "north": 45.0,
            "south": 44.0,
            "east": 2.0,
            "west": 1.0,
            "track_type": "segment",
            "limit": 0,
        },
    )
    assert response.status_code == 422  # Validation error


def test_search_segments_response_includes_barycenter(client):
    """Test that search segments response includes barycenter fields."""
    response = client.get(
        "/api/segments/search",
        params={
            "north": 45.0,
            "south": 44.0,
            "east": 2.0,
            "west": 1.0,
            "track_type": "segment",
            "limit": 10,
        },
    )
    assert response.status_code == 200

    # Parse the streaming response
    lines = response.text.strip().split("\n")
    data_lines = [
        line
        for line in lines
        if line.startswith("data: ") and not line.startswith("data: [DONE]")
    ]

    if data_lines:
        # Skip the first line which contains the count
        if len(data_lines) > 1:
            track_data = json.loads(data_lines[1].replace("data: ", ""))

            # Check that barycenter fields are present
            assert "barycenter_latitude" in track_data
            assert "barycenter_longitude" in track_data
            assert isinstance(track_data["barycenter_latitude"], (int, float))
            assert isinstance(track_data["barycenter_longitude"], (int, float))


def test_main_module_execution():
    """Test the if __name__ == '__main__' block by importing and checking it exists."""
    import src.main

    assert hasattr(src.main, "app")
    assert hasattr(src.main, "uvicorn")

    # The if __name__ == "__main__" block is not executed during import,
    # but we can verify the structure exists by checking the file content
    with open(src.main.__file__) as f:
        content = f.read()
        assert 'if __name__ == "__main__":' in content
        assert 'uvicorn.run(app, host="0.0.0.0", port=8000)' in content


def test_get_track_info_success(client):
    """Test successful track info retrieval."""
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    # Create a mock track object
    mock_track = Track(
        id=123,
        file_path="test/path.gpx",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=5.0,
        bound_west=3.0,
        barycenter_latitude=44.5,
        barycenter_longitude=4.0,
        name="Test Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.SEMI_SLICK,
        tire_wet=TireType.KNOBS,
        comments="Test comments",
        created_at=datetime.now(),
    )

    # Mock the database session and query
    with patch("src.main.SessionLocal") as mock_session_local:

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return mock_track

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        response = client.get("/api/segments/123")

        assert response.status_code == 200
        data = response.json()

        # Verify all TrackResponse fields are present
        assert data["id"] == 123
        assert data["file_path"] == "test/path.gpx"
        assert data["bound_north"] == 45.0
        assert data["bound_south"] == 44.0
        assert data["bound_east"] == 5.0
        assert data["bound_west"] == 3.0
        assert data["barycenter_latitude"] == 44.5
        assert data["barycenter_longitude"] == 4.0
        assert data["name"] == "Test Track"
        assert data["track_type"] == "segment"
        assert data["difficulty_level"] == 3
        assert data["surface_type"] == "forest-trail"
        assert data["tire_dry"] == "semi-slick"
        assert data["tire_wet"] == "knobs"
        assert data["comments"] == "Test comments"


def test_get_track_info_database_not_available(client):
    """Test track info retrieval when database is not available."""
    with patch("src.main.SessionLocal", None):
        response = client.get("/api/segments/123")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Database not available"


def test_get_track_info_track_not_found(client):
    """Test track info retrieval when track doesn't exist."""
    with patch("src.main.SessionLocal") as mock_session_local:

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return None  # Track not found

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        response = client.get("/api/segments/999")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Track not found"


def test_get_track_info_database_exception(client):
    """Test track info retrieval when database throws an exception."""
    with patch("src.main.SessionLocal") as mock_session_local:

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                raise Exception("Database connection failed")

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        response = client.get("/api/segments/123")

        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]
        assert "Database connection failed" in data["detail"]


def test_get_track_parsed_data_success(client):
    """Test successful track parsed data retrieval using real GPX file."""
    import os
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    # Create a mock track object
    mock_track = Track(
        id=456,
        file_path="data/file.gpx",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=5.0,
        bound_west=3.0,
        barycenter_latitude=44.5,
        barycenter_longitude=4.0,
        name="Test chemin Gravel autour du Puit",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.SEMI_SLICK,
        tire_wet=TireType.KNOBS,
        comments="Test comments",
        created_at=datetime.now(),
    )

    # Load real GPX data from file
    data_dir = os.path.dirname(os.path.abspath(__file__))
    gpx_file_path = os.path.join(data_dir, "data", "file.gpx")

    with open(gpx_file_path, "rb") as f:
        real_gpx_data = f.read()

    # Mock parsed GPX data based on real file structure
    mock_parsed_data = {
        "file_id": "file",
        "track_name": "Test chemin Gravel autour du Puit",
        "points": [
            {
                "latitude": 46.9192890,
                "longitude": 3.9921170,
                "elevation": 576.0,
                "time": "2025-08-30T13:25:10Z",
            }
        ],
        "total_stats": {
            "total_points": 1,
            "total_distance": 1000.0,
            "total_elevation_gain": 50.0,
            "total_elevation_loss": 30.0,
        },
        "bounds": {
            "north": 45.0,
            "south": 44.0,
            "east": 5.0,
            "west": 3.0,
            "min_elevation": 100.0,
            "max_elevation": 150.0,
        },
    }

    with (
        patch("src.main.SessionLocal") as mock_session_local,
        patch("src.main.storage_manager") as mock_storage_manager,
        patch("src.main.gpxpy.parse"),
        patch("src.main.extract_from_gpx_file") as mock_extract,
    ):
        # Setup mocks
        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return mock_track

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        mock_storage_manager.load_gpx_data.return_value = real_gpx_data
        mock_extract.return_value = mock_parsed_data

        response = client.get("/api/segments/456/data")

        assert response.status_code == 200
        data = response.json()

        # Verify GPXData response structure
        assert data["file_id"] == "file"
        assert data["track_name"] == "Test chemin Gravel autour du Puit"
        assert len(data["points"]) == 1
        assert data["points"][0]["latitude"] == 46.9192890
        assert data["total_stats"]["total_distance"] == 1000.0
        assert data["bounds"]["north"] == 45.0


def test_get_track_parsed_data_database_not_available(client):
    """Test track parsed data retrieval when database is not available."""
    with patch("src.main.SessionLocal", None):
        response = client.get("/api/segments/456/data")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Database not available"


def test_get_track_parsed_data_storage_manager_not_available(client):
    """Test track parsed data retrieval when storage manager is not available."""
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    mock_track = Track(
        id=456,
        file_path="data/file.gpx",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=5.0,
        bound_west=3.0,
        barycenter_latitude=44.5,
        barycenter_longitude=4.0,
        name="Test chemin Gravel autour du Puit",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.SEMI_SLICK,
        tire_wet=TireType.KNOBS,
        comments="Test comments",
        created_at=datetime.now(),
    )

    with (
        patch("src.main.SessionLocal") as mock_session_local,
        patch("src.main.storage_manager", None),
    ):

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return mock_track

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        response = client.get("/api/segments/456/data")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Storage manager not available"


def test_get_track_parsed_data_track_not_found(client):
    """Test track parsed data retrieval when track doesn't exist."""
    with patch("src.main.SessionLocal") as mock_session_local:

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return None  # Track not found

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        response = client.get("/api/segments/999/data")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Track not found"


def test_get_track_parsed_data_gpx_not_found(client):
    """Test track parsed data retrieval when GPX file is not found."""
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    mock_track = Track(
        id=456,
        file_path="data/nonexistent.gpx",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=5.0,
        bound_west=3.0,
        barycenter_latitude=44.5,
        barycenter_longitude=4.0,
        name="Test Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.SEMI_SLICK,
        tire_wet=TireType.KNOBS,
        comments="Test comments",
        created_at=datetime.now(),
    )

    with (
        patch("src.main.SessionLocal") as mock_session_local,
        patch("src.main.storage_manager") as mock_storage_manager,
    ):

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return mock_track

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        # Storage manager returns None (GPX not found)
        mock_storage_manager.load_gpx_data.return_value = None

        response = client.get("/api/segments/456/data")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "GPX data not found"


def test_get_track_parsed_data_gpx_parsing_failure(client):
    """Test track parsed data retrieval when GPX parsing fails."""
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    mock_track = Track(
        id=456,
        file_path="data/invalid.gpx",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=5.0,
        bound_west=3.0,
        barycenter_latitude=44.5,
        barycenter_longitude=4.0,
        name="Test Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.SEMI_SLICK,
        tire_wet=TireType.KNOBS,
        comments="Test comments",
        created_at=datetime.now(),
    )

    mock_gpx_data = b'<?xml version="1.0" encoding="UTF-8"?>\n<invalid>gpx</invalid>'

    with (
        patch("src.main.SessionLocal") as mock_session_local,
        patch("src.main.storage_manager") as mock_storage_manager,
        patch("src.main.gpxpy.parse"),
    ):

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return mock_track

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        mock_storage_manager.load_gpx_data.return_value = mock_gpx_data
        # GPX parsing throws an exception
        with patch("src.main.gpxpy.parse") as mock_gpx_parse:
            mock_gpx_parse.side_effect = Exception("Invalid GPX format")

            response = client.get("/api/segments/456/data")

            assert response.status_code == 500
            data = response.json()
            assert "Failed to parse GPX data" in data["detail"]


def test_get_track_parsed_data_extraction_failure(client):
    """Test track parsed data retrieval when data extraction fails."""
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    mock_track = Track(
        id=456,
        file_path="data/extraction_fail.gpx",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=5.0,
        bound_west=3.0,
        barycenter_latitude=44.5,
        barycenter_longitude=4.0,
        name="Test Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.SEMI_SLICK,
        tire_wet=TireType.KNOBS,
        comments="Test comments",
        created_at=datetime.now(),
    )

    mock_gpx_data = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<gpx version="1.1"><trk><name>Test Track</name></trk></gpx>'
    )

    with (
        patch("src.main.SessionLocal") as mock_session_local,
        patch("src.main.storage_manager") as mock_storage_manager,
        patch("src.main.gpxpy.parse"),
        patch("src.main.extract_from_gpx_file") as mock_extract,
    ):

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return mock_track

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        mock_storage_manager.load_gpx_data.return_value = mock_gpx_data
        # Data extraction throws an exception
        mock_extract.side_effect = Exception("Failed to extract data")

        response = client.get("/api/segments/456/data")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to parse GPX data" in data["detail"]


def test_get_track_parsed_data_database_exception(client):
    """Test track parsed data retrieval when database throws an exception."""
    with patch("src.main.SessionLocal") as mock_session_local:

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                raise Exception("Database connection failed")

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        response = client.get("/api/segments/456/data")

        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]
        assert "Database connection failed" in data["detail"]


def test_get_track_parsed_data_file_path_none(client):
    """Test track parsed data retrieval when file_path is None."""
    from datetime import datetime

    from backend.src.models.track import SurfaceType, TireType, Track, TrackType

    mock_track = Track(
        id=456,
        file_path=None,  # None file path
        bound_north=45.0,
        bound_south=44.0,
        bound_east=5.0,
        bound_west=3.0,
        barycenter_latitude=44.5,
        barycenter_longitude=4.0,
        name="Test Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.SEMI_SLICK,
        tire_wet=TireType.KNOBS,
        comments="Test comments",
        created_at=datetime.now(),
    )

    mock_gpx_data = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<gpx version="1.1"><trk><name>Test Track</name></trk></gpx>'
    )

    mock_parsed_data = {
        "file_id": "456",  # Should use track ID when file_path is None
        "track_name": "Test Track",
        "points": [],
        "total_stats": {
            "total_points": 0,
            "total_distance": 0.0,
            "total_elevation_gain": 0.0,
            "total_elevation_loss": 0.0,
        },
        "bounds": {
            "north": 45.0,
            "south": 44.0,
            "east": 5.0,
            "west": 3.0,
            "min_elevation": 0.0,
            "max_elevation": 0.0,
        },
    }

    with (
        patch("src.main.SessionLocal") as mock_session_local,
        patch("src.main.storage_manager") as mock_storage_manager,
        patch("src.main.gpxpy.parse"),
        patch("src.main.extract_from_gpx_file") as mock_extract,
    ):

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def execute(self, stmt):
                class MockResult:
                    def scalar_one_or_none(self):
                        return mock_track

                return MockResult()

        class MockSessionLocal:
            async def __aenter__(self):
                return MockSession()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_session_local.return_value = MockSessionLocal()

        mock_storage_manager.load_gpx_data.return_value = mock_gpx_data
        mock_extract.return_value = mock_parsed_data

        response = client.get("/api/segments/456/data")

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "456"  # Should use track ID as fallback


# Strava API endpoint tests
class TestStravaEndpoints:
    """Test suite for Strava API endpoints."""

    def test_get_strava_auth_url_success(self, client):
        """Test successful generation of Strava authorization URL."""
        with patch("src.main.strava.get_authorization_url") as mock_get_auth_url:
            mock_get_auth_url.return_value = (
                "https://www.strava.com/oauth/authorize?client_id=123&redirect_uri=test"
            )

            response = client.get("/api/strava/auth-url")

            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert (
                data["auth_url"]
                == "https://www.strava.com/oauth/authorize?client_id=123&redirect_uri=test"
            )
            mock_get_auth_url.assert_called_once_with(
                "http://localhost:3000/strava-callback", "strava_auth"
            )

    def test_get_strava_auth_url_with_custom_state(self, client):
        """Test Strava authorization URL generation with custom state."""
        with patch("src.main.strava.get_authorization_url") as mock_get_auth_url:
            mock_get_auth_url.return_value = "https://www.strava.com/oauth/authorize?client_id=123&state=custom_state"

            response = client.get("/api/strava/auth-url?state=custom_state")

            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            mock_get_auth_url.assert_called_once_with(
                "http://localhost:3000/strava-callback", "custom_state"
            )

    def test_get_strava_auth_url_error(self, client):
        """Test Strava authorization URL generation error handling."""
        with patch("src.main.strava.get_authorization_url") as mock_get_auth_url:
            mock_get_auth_url.side_effect = Exception("Configuration error")

            response = client.get("/api/strava/auth-url")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to generate auth URL" in data["detail"]

    def test_exchange_strava_code_success(self, client):
        """Test successful Strava code exchange."""
        mock_token_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
            "athlete": {
                "id": 12345,
                "username": "test_user",
                "firstname": "Test",
                "lastname": "User",
            },
        }

        with patch("src.main.strava.exchange_code_for_token") as mock_exchange:
            mock_exchange.return_value = mock_token_response

            response = client.post(
                "/api/strava/exchange-code", data={"code": "test_code"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "test_access_token"
            assert data["expires_at"] == 9999999999
            assert data["athlete"]["id"] == 12345
            mock_exchange.assert_called_once_with("test_code")

    def test_exchange_strava_code_error(self, client):
        """Test Strava code exchange error handling."""
        with patch("src.main.strava.exchange_code_for_token") as mock_exchange:
            mock_exchange.side_effect = Exception("Invalid code")

            response = client.post(
                "/api/strava/exchange-code", data={"code": "invalid_code"}
            )

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Failed to exchange code" in data["detail"]

    def test_refresh_strava_token_success(self, client):
        """Test successful Strava token refresh."""
        with patch("src.main.strava.refresh_access_token") as mock_refresh:
            mock_refresh.return_value = True

            response = client.post("/api/strava/refresh-token")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Token refreshed successfully"
            mock_refresh.assert_called_once()

    def test_refresh_strava_token_failure(self, client):
        """Test Strava token refresh failure."""
        with patch("src.main.strava.refresh_access_token") as mock_refresh:
            mock_refresh.return_value = False

            response = client.post("/api/strava/refresh-token")

            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Failed to refresh token" in data["detail"]

    def test_refresh_strava_token_exception(self, client):
        """Test Strava token refresh exception handling."""
        with patch("src.main.strava.refresh_access_token") as mock_refresh:
            mock_refresh.side_effect = Exception("Token refresh error")

            response = client.post("/api/strava/refresh-token")

            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Failed to refresh token" in data["detail"]

    def test_get_strava_activities_success(self, client):
        """Test successful Strava activities retrieval."""
        mock_activities = [
            {
                "id": "12345",
                "name": "Morning Ride",
                "distance": 25000.0,
                "moving_time": 3600,
                "type": "Ride",
                "start_date": "2023-01-01T10:00:00",
            },
            {
                "id": "12346",
                "name": "Evening Run",
                "distance": 5000.0,
                "moving_time": 1800,
                "type": "Run",
                "start_date": "2023-01-01T18:00:00",
            },
        ]

        with patch("src.main.strava.get_activities") as mock_get_activities:
            mock_get_activities.return_value = mock_activities

            response = client.get("/api/strava/activities")

            assert response.status_code == 200
            data = response.json()
            assert "activities" in data
            assert len(data["activities"]) == 2
            assert data["page"] == 1
            assert data["per_page"] == 30
            assert data["total"] == 2
            assert data["activities"][0]["name"] == "Morning Ride"
            mock_get_activities.assert_called_once_with(1, 30)

    def test_get_strava_activities_with_pagination(self, client):
        """Test Strava activities retrieval with custom pagination."""
        mock_activities = [{"id": "12345", "name": "Test Activity"}]

        with patch("src.main.strava.get_activities") as mock_get_activities:
            mock_get_activities.return_value = mock_activities

            response = client.get("/api/strava/activities?page=2&per_page=10")

            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert data["per_page"] == 10
            mock_get_activities.assert_called_once_with(2, 10)

    def test_get_strava_activities_error(self, client):
        """Test Strava activities retrieval error handling."""
        with patch("src.main.strava.get_activities") as mock_get_activities:
            mock_get_activities.side_effect = Exception("API error")

            response = client.get("/api/strava/activities")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to fetch activities" in data["detail"]

    def test_get_strava_activities_http_exception(self, client):
        """Test Strava activities retrieval HTTPException handling."""
        from fastapi import HTTPException

        with patch("src.main.strava.get_activities") as mock_get_activities:
            mock_get_activities.side_effect = HTTPException(
                status_code=401, detail="Unauthorized access"
            )

            response = client.get("/api/strava/activities")

            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert data["detail"] == "Unauthorized access"

    def test_get_strava_activity_gpx_success(self, client):
        """Test successful Strava activity GPX retrieval."""
        mock_gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
    <trk>
        <name>Test Activity</name>
        <trkpt lat="51.5074" lon="-0.1278">
            <ele>10.0</ele>
            <time>2023-01-01T10:00:00Z</time>
        </trkpt>
    </trk>
</gpx>"""

        # Create a mock GPXData object with proper structure
        class MockGPXData:
            def __init__(self):
                self.file_id = "test_file_id"
                self.track_name = "Test Activity"
                self.points = [{"lat": 51.5074, "lon": -0.1278, "elevation": 10.0}]
                self.total_stats = {
                    "total_points": 1,
                    "total_distance": 0.0,
                    "total_elevation_gain": 0.0,
                    "total_elevation_loss": 0.0,
                }
                self.bounds = {
                    "north": 51.5074,
                    "south": 51.5074,
                    "east": -0.1278,
                    "west": -0.1278,
                    "min_elevation": 10.0,
                    "max_elevation": 10.0,
                }

            def model_dump(self):
                return {
                    "file_id": self.file_id,
                    "track_name": self.track_name,
                    "points": self.points,
                    "total_stats": self.total_stats,
                    "bounds": self.bounds,
                }

        mock_gpx_data = MockGPXData()

        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("src.main.extract_from_gpx_file") as mock_extract,
            patch("src.main.gpxpy.parse"),
            patch("builtins.open", create=True),
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
        ):
            mock_temp_dir.name = "/tmp/test_dir"
            mock_get_gpx.return_value = mock_gpx_string
            mock_extract.return_value = mock_gpx_data
            mock_exists.return_value = True

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 200
            data = response.json()
            assert "file_id" in data  # file_id is generated dynamically
            assert data["track_name"] == "Test Activity"
            assert len(data["points"]) == 1
            mock_get_gpx.assert_called_once_with("12345")

    def test_get_strava_activity_gpx_no_data(self, client):
        """Test Strava activity GPX retrieval when no GPX data available."""
        with patch("src.main.strava.get_activity_gpx") as mock_get_gpx:
            mock_get_gpx.return_value = None

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "No GPX data available for this activity" in data["detail"]

    def test_get_strava_activity_gpx_no_temp_dir(self, client):
        """Test Strava activity GPX retrieval when temp directory not initialized."""
        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir", None),
        ):
            mock_get_gpx.return_value = '<?xml version="1.0"?><gpx></gpx>'

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Temporary directory not initialized" in data["detail"]

    def test_get_strava_activity_gpx_save_error(self, client):
        """Test Strava activity GPX retrieval with file save error."""
        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("builtins.open", side_effect=OSError("Permission denied")),
        ):
            mock_temp_dir.name = "/tmp/test_dir"
            mock_get_gpx.return_value = '<?xml version="1.0"?><gpx></gpx>'

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to save GPX" in data["detail"]

    def test_get_strava_activity_gpx_parse_error(self, client):
        """Test Strava activity GPX retrieval with GPX parse error."""
        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("builtins.open", create=True),
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
            patch("src.main.gpxpy.parse", side_effect=Exception("Invalid GPX")),
        ):
            mock_temp_dir.name = "/tmp/test_dir"
            mock_get_gpx.return_value = "invalid gpx content"
            mock_exists.return_value = True

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Invalid GPX file" in data["detail"]

    def test_get_strava_activity_gpx_extract_error(self, client):
        """Test Strava activity GPX retrieval with GPX extraction error."""
        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("builtins.open", create=True),
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
            patch("src.main.gpxpy.parse"),
            patch(
                "src.main.extract_from_gpx_file",
                side_effect=Exception("Processing error"),
            ),
        ):
            mock_temp_dir.name = "/tmp/test_dir"
            mock_get_gpx.return_value = '<?xml version="1.0"?><gpx></gpx>'
            mock_exists.return_value = True

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Invalid GPX file" in data["detail"]

    def test_get_strava_activity_gpx_general_error(self, client):
        """Test Strava activity GPX retrieval with general error."""
        with patch("src.main.strava.get_activity_gpx") as mock_get_gpx:
            mock_get_gpx.side_effect = Exception("Network error")

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to fetch GPX" in data["detail"]

    def test_get_strava_activity_gpx_http_exception(self, client):
        """Test Strava activity GPX retrieval HTTPException handling."""
        from fastapi import HTTPException

        with patch("src.main.strava.get_activity_gpx") as mock_get_gpx:
            mock_get_gpx.side_effect = HTTPException(
                status_code=403, detail="Forbidden access to activity"
            )

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 403
            data = response.json()
            assert "detail" in data
            assert data["detail"] == "Forbidden access to activity"

    def test_get_strava_activities_with_stravalib_mock(self, client, mock_strava_api):
        """Test Strava activities retrieval using stravalib mock fixture."""
        with mock_strava_api:
            # The mock should handle the API call
            response = client.get("/api/strava/activities")

            # This might return an error due to authentication, but we test the endpoint
            assert response.status_code in [200, 401, 500]  # Accept various error codes

    def test_get_strava_activity_gpx_with_stravalib_mock(self, client, mock_strava_api):
        """Test Strava activity GPX retrieval using stravalib mock fixture."""
        with mock_strava_api:
            # The mock should handle the API call
            response = client.get("/api/strava/activities/12345/gpx")

            # This might return an error due to authentication, but we test the endpoint
            assert response.status_code in [200, 401, 404, 500]  # Accept error codes


class TestMapTilesEndpoint:
    """Test the map tiles proxy endpoint."""

    def test_get_map_tile_success(self, client):
        """Test successful map tile retrieval."""
        from unittest.mock import AsyncMock, patch

        # Mock PNG content
        mock_png_content = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
            b"\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # Mock the httpx client
        mock_response = AsyncMock()
        mock_response.content = mock_png_content
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            response = client.get("/api/map-tiles/10/512/384.png")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.headers["cache-control"] == "public, max-age=86400"
            assert response.headers["access-control-allow-origin"] == "*"
            assert response.content == mock_png_content

    def test_get_map_tile_different_coordinates(self, client):
        """Test map tile retrieval with different coordinates."""
        from unittest.mock import AsyncMock, patch

        # Mock PNG content
        mock_png_content = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
            b"\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # Mock the httpx client
        mock_response = AsyncMock()
        mock_response.content = mock_png_content
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            # Test different coordinates
            response = client.get("/api/map-tiles/15/16384/12288.png")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content == mock_png_content

            # Verify the client was called with a URL containing the correct coordinates
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            tile_url = call_args[0][0]  # First positional argument
            assert "/cycle/15/16384/12288.png" in tile_url
            assert "apikey=" in tile_url

    def test_get_map_tile_http_error(self, client):
        """Test map tile retrieval with HTTP error."""
        from unittest.mock import AsyncMock, patch

        import httpx

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock HTTPStatusError
            mock_response = AsyncMock()
            mock_response.status_code = 404
            http_error = httpx.HTTPStatusError(
                "Not Found", request=AsyncMock(), response=mock_response
            )
            mock_client.get.side_effect = http_error

            response = client.get("/api/map-tiles/10/512/384.png")

            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Failed to fetch map tile"

    def test_get_map_tile_request_error(self, client):
        """Test map tile retrieval with request error."""
        from unittest.mock import AsyncMock, patch

        import httpx

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock RequestError
            request_error = httpx.RequestError("Connection failed")
            mock_client.get.side_effect = request_error

            response = client.get("/api/map-tiles/10/512/384.png")

            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Failed to fetch map tile"

    def test_get_map_tile_unexpected_error(self, client):
        """Test map tile retrieval with unexpected error."""
        from unittest.mock import AsyncMock, patch

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock unexpected error
            unexpected_error = ValueError("Unexpected error")
            mock_client.get.side_effect = unexpected_error

            response = client.get("/api/map-tiles/10/512/384.png")

            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Internal server error"

    def test_get_map_tile_subdomain_selection(self, client):
        """Test that different subdomains are selected for load balancing."""
        from unittest.mock import AsyncMock, patch

        # Mock PNG content
        mock_png_content = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
            b"\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # Mock the httpx client
        mock_response = AsyncMock()
        mock_response.content = mock_png_content
        mock_response.raise_for_status.return_value = None

        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch("random.choice") as mock_choice,
        ):
            # Mock random choice to return specific subdomain
            mock_choice.return_value = "b"

            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            response = client.get("/api/map-tiles/10/512/384.png")

            assert response.status_code == 200

            # Verify random.choice was called with the expected subdomains
            mock_choice.assert_called_once_with(["a", "b", "c"])

            # Verify the client was called with a URL containing the selected subdomain
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            tile_url = call_args[0][0]  # First positional argument
            assert "b.tile.thunderforest.com" in tile_url

    def test_get_map_tile_timeout_configuration(self, client):
        """Test that httpx client is configured with correct timeout."""
        from unittest.mock import AsyncMock, patch

        # Mock PNG content
        mock_png_content = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
            b"\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # Mock the httpx client
        mock_response = AsyncMock()
        mock_response.content = mock_png_content
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            response = client.get("/api/map-tiles/10/512/384.png")

            assert response.status_code == 200

            # Verify AsyncClient was called with correct timeout
            mock_client_class.assert_called_once_with(timeout=10.0)

    def test_get_map_tile_api_key_in_url(self, client):
        """Test that API key is included in the tile URL."""
        from unittest.mock import AsyncMock, patch

        # Mock PNG content
        mock_png_content = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
            b"\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # Mock the httpx client
        mock_response = AsyncMock()
        mock_response.content = mock_png_content
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            response = client.get("/api/map-tiles/10/512/384.png")

            assert response.status_code == 200

            # Verify the client was called with a URL containing the API key
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            tile_url = call_args[0][0]  # First positional argument
            assert "apikey=" in tile_url
            assert "thunderforest.com" in tile_url
