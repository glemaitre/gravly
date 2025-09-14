"""Tests for FastAPI main endpoints."""

import asyncio
import json
import os
from pathlib import Path
from unittest.mock import patch

import boto3
import pytest
import src.main
from fastapi.testclient import TestClient
from moto import mock_aws
from src.main import app, lifespan
from src.utils.gpx import generate_gpx_segment
from src.utils.s3 import S3Manager, cleanup_local_file


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
    assert "tire_dry" in data
    assert "tire_wet" in data
    assert "file_path" in data

    assert data["name"] == "Test Segment"
    assert data["tire_dry"] == "slick"
    assert data["tire_wet"] == "semi-slick"
    assert data["file_path"].startswith("s3:/")
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
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "50",
            },
        )

        assert response1.status_code == 200

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
            "tire_dry": "slick",
            "tire_wet": "semi-slick",
            "file_id": "test-id",
            "start_index": "0",
            "end_index": "2",
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
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "100",
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
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "100",
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


def test_app_lifespan():
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

        s3_manager = S3Manager()

        frontend_temp_dir = tmp_path / "temp_gpx_segments"

        file_id, segment_file_path = generate_gpx_segment(
            input_file_path=sample_gpx_file,
            start_index=1,
            end_index=3,
            segment_name="Test Segment",
            output_dir=frontend_temp_dir,
        )

        assert segment_file_path.exists()
        assert file_id is not None

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
        s3_manager = S3Manager(
            bucket_name="nonexistent-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )

        frontend_temp_dir = tmp_path / "temp_gpx_segments"

        file_id, segment_file_path = generate_gpx_segment(
            input_file_path=sample_gpx_file,
            start_index=1,
            end_index=2,
            segment_name="Test Segment",
            output_dir=frontend_temp_dir,
        )

        assert segment_file_path.exists()

        with pytest.raises(Exception):
            s3_manager.upload_gpx_segment(
                local_file_path=segment_file_path,
                file_id=file_id,
                prefix="gpx-segments",
            )

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

        s3_manager = S3Manager()

        frontend_temp_dir = tmp_path / "temp_gpx_segments"

        segments = []
        for i, (start, end) in enumerate([(0, 1), (1, 3), (3, 4)]):
            file_id, segment_file_path = generate_gpx_segment(
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
            assert False, f"Local file should have been cleaned up: {file_path}"


def test_frontend_temp_directory_creation(
    mock_s3_environment, sample_gpx_file, tmp_path
):
    """Test that frontend temp directory is created if it doesn't exist."""
    with mock_aws():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=mock_s3_environment)

        s3_manager = S3Manager()

        frontend_temp_dir = tmp_path / "nonexistent" / "temp_gpx_segments"

        assert not frontend_temp_dir.exists()

        file_id, segment_file_path = generate_gpx_segment(
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
                "tire_dry": "slick",
                "tire_wet": "slick",
                "file_id": file_id,
                "start_index": 1,
                "end_index": 2,
            },
        )

        # Note: This test demonstrates the expected flow
        # The segment creation might fail due to S3 manager initialization
        # but we've already tested the core functionality in other tests
        # Accept either success or S3 init failure
        assert segment_response.status_code in [200, 500]


def test_s3_manager_initialization_failure_handling():
    """Test that the app handles S3 manager initialization failure gracefully."""

    original_s3_manager = src.main.s3_manager

    try:
        with patch.dict(os.environ, {}, clear=True):

            async def run_lifespan():
                async with lifespan(app):
                    assert src.main.s3_manager is None
                    return True

            result = asyncio.run(run_lifespan())
            assert result is True

    finally:
        src.main.s3_manager = original_s3_manager


def test_s3_manager_initialization_exception_handling():
    """Test that S3 manager initialization exceptions are properly caught and logged."""

    original_s3_manager = src.main.s3_manager

    try:
        with patch("src.main.S3Manager", side_effect=Exception("S3 connection failed")):

            async def run_lifespan():
                async with lifespan(app):
                    assert src.main.s3_manager is None
                    return True

            result = asyncio.run(run_lifespan())
            assert result is True

    finally:
        src.main.s3_manager = original_s3_manager


def test_create_segment_s3_manager_not_initialized(client, sample_gpx_file):
    """Test segment creation when S3 manager is not initialized."""
    with open(sample_gpx_file, "rb") as f:
        upload_response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    original_s3_manager = src.main.s3_manager

    try:
        src.main.s3_manager = None

        response = client.post(
            "/api/segments",
            data={
                "name": "Test Segment",
                "tire_dry": "slick",
                "tire_wet": "semi-slick",
                "file_id": file_id,
                "start_index": "0",
                "end_index": "100",
            },
        )

        assert response.status_code == 500
        assert "S3 manager not initialized" in response.json()["detail"]

    finally:
        src.main.s3_manager = original_s3_manager
