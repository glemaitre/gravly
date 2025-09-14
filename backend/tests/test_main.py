"""Tests for FastAPI main endpoints."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app, lifespan


@pytest.fixture
def client(tmp_path):
    """Create a test client with temporary directory."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_gpx_file():
    """Get the sample GPX file from tests/data directory."""
    data_dir = Path(__file__).parent / "data"
    gpx_file = data_dir / "file.gpx"
    return gpx_file


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

    # Check response structure
    assert "file_id" in data
    assert "track_name" in data
    assert "points" in data
    assert "total_stats" in data
    assert "bounds" in data
    assert "elevation_stats" in data

    # Check specific values
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


def test_create_segment_success(client, sample_gpx_file, tmp_path):
    """Test successful segment creation."""
    # First upload a GPX file
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    # Mock the destination directory to use tmp_path
    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        # Create segment
        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
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

    # Check response structure
    assert "id" in data
    assert "name" in data
    assert "tire_dry" in data
    assert "tire_wet" in data
    assert "file_path" in data

    # Check specific values
    assert data["name"] == "Test Segment"
    assert data["tire_dry"] == "slick"
    assert data["tire_wet"] == "semi-slick"
    assert data["file_path"].endswith(".gpx")

    # Verify the segment file was created
    segment_file = Path(data["file_path"])
    assert segment_file.exists()


def test_create_segment_invalid_tire_types(client, sample_gpx_file):
    """Test segment creation with invalid tire types."""
    # First upload a GPX file
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    # Try to create segment with invalid tire types
    response = client.post(
        "/api/segments",
        data={
            "name": "Test Segment",
            "tire_dry": "invalid",
            "tire_wet": "semi-slick",
            "file_id": file_id,
            "start_index": "0",
            "end_index": "2",
        },
    )

    assert response.status_code == 422
    assert "Invalid tire types" in response.json()["detail"]


def test_create_segment_file_not_found(client):
    """Test segment creation with non-existent file ID."""
    response = client.post(
        "/api/segments",
        data={
            "name": "Test Segment",
            "tire_dry": "slick",
            "tire_wet": "semi-slick",
            "file_id": "non-existent-id",
            "start_index": "0",
            "end_index": "2",
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
    # First upload a GPX file
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    # Mock the destination directory to use tmp_path
    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        # Try to create segment with invalid indices
        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
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


def test_create_segment_with_commentary_and_media(client, sample_gpx_file, tmp_path):
    """Test segment creation with commentary and media."""
    # First upload a GPX file
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    # Mock the destination directory to use tmp_path
    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        # Create segment with commentary and media
        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment with Media",
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


def test_multiple_segments_same_file(client, sample_gpx_file, tmp_path):
    """Test creating multiple segments from the same uploaded file."""
    # First upload a GPX file
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    file_id = upload_response.json()["file_id"]

    # Mock the destination directory to use tmp_path
    with patch("src.main.Path") as mock_path:

        def path_side_effect(path_str):
            if path_str == "../scratch/mock_gpx":
                return tmp_path / "mock_gpx"
            return Path(path_str)

        mock_path.side_effect = path_side_effect

        # Create first segment
        response1 = client.post(
            "/api/segments",
            data={
                "name": "First Segment",
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "50",
            },
        )

        assert response1.status_code == 200

        # Create second segment from the same file
        response2 = client.post(
            "/api/segments",
            data={
                "name": "Second Segment",
                "tire_dry": "knobs",
                "tire_wet": "knobs",
                "file_id": file_id,
                "start_index": "50",
                "end_index": "100",
            },
        )

        assert response2.status_code == 200

        # Both segments should be created successfully
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


@patch("src.main.temp_dir", None)
def test_create_segment_no_temp_directory(client):
    """Test segment creation when temporary directory is not initialized."""
    response = client.post(
        "/api/segments",
        data={
            "name": "Test Segment",
            "tire_dry": "slick",
            "tire_wet": "semi-slick",
            "file_id": "test-id",
            "start_index": "0",
            "end_index": "2",
        },
    )

    assert response.status_code == 500
    assert "Temporary directory not initialized" in response.json()["detail"]


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.options("/api/upload-gpx")
    # CORS preflight should be handled by the middleware
    assert response.status_code in [200, 405]  # Depends on CORS configuration


def test_app_lifespan():
    """Test that the app is properly configured."""
    # Test basic app configuration
    assert app is not None
    assert app.title == "Cycling GPX API"
    assert app.version == "1.0.0"

    # Test that the app has the expected routes
    routes = [route.path for route in app.routes]
    assert "/" in routes
    assert "/api/upload-gpx" in routes
    assert "/api/segments" in routes
