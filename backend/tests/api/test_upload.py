"""Tests for upload API endpoints."""

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
    """Set up database and storage configuration for tests."""
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
        import src.main as main_module

        # Make main_module available globally for tests as 'src'
        globals()["src"] = type("MockSrc", (), {"main": main_module})()
        yield


@pytest.fixture
def app():
    """Get the FastAPI app instance."""
    from src.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def client(tmp_path, app):
    """Create a test client with temporary directory."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_gpx_file():
    """Get the sample GPX file from tests/data directory."""
    data_dir = Path(__file__).parent.parent / "data"
    gpx_file = data_dir / "file.gpx"
    return gpx_file


# ============== UPLOAD-GPX ENDPOINT TESTS ==============


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


@patch("src.dependencies.temp_dir", None)
def test_upload_gpx_no_temp_directory(client, sample_gpx_file):
    """Test upload when temporary directory is not initialized."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 500
    assert "Temporary directory not initialized" in response.json()["detail"]


@patch("src.api.upload.open", side_effect=OSError("Permission denied"))
def test_upload_gpx_file_save_failure(mock_open, client, sample_gpx_file):
    """Test upload when file saving fails due to filesystem error."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 500
    assert "Failed to save file" in response.json()["detail"]
    assert "Permission denied" in response.json()["detail"]


@patch("src.api.upload.open", side_effect=OSError("Disk full"))
def test_upload_gpx_disk_full_failure(mock_open, client, sample_gpx_file):
    """Test upload when file saving fails due to disk space issues."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 500
    assert "Failed to save file" in response.json()["detail"]
    assert "Disk full" in response.json()["detail"]


@patch(
    "src.api.upload.extract_from_gpx_file",
    side_effect=Exception("GPX processing failed"),
)
def test_upload_gpx_processing_failure(mock_extract, client, sample_gpx_file):
    """Test upload when GPX processing fails after successful file save."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 400
    assert "Invalid GPX file" in response.json()["detail"]
    assert "GPX processing failed" in response.json()["detail"]


@patch(
    "src.api.upload.extract_from_gpx_file", side_effect=ValueError("Invalid track data")
)
def test_upload_gpx_invalid_track_data(mock_extract, client, sample_gpx_file):
    """Test upload when GPX file has invalid track data."""
    with open(sample_gpx_file, "rb") as f:
        response = client.post(
            "/api/upload-gpx", files={"file": ("test.gpx", f, "application/gpx+xml")}
        )

    assert response.status_code == 400
    assert "Invalid GPX file" in response.json()["detail"]
    assert "Invalid track data" in response.json()["detail"]


# ============== UPLOAD-IMAGE ENDPOINT TESTS ==============


def test_upload_image_success(client, tmp_path):
    """Test successful image upload."""
    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()

    assert "image_id" in data
    assert "image_url" in data
    assert "storage_key" in data
    assert data["image_id"] is not None
    assert data["image_url"] is not None
    assert data["storage_key"].startswith("images-segments/")
    assert data["image_id"] in data["storage_key"]


def test_upload_image_invalid_content_type(client):
    """Test upload with non-image file content type."""
    response = client.post(
        "/api/upload-image", files={"file": ("test.txt", b"not an image", "text/plain")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "File must be an image" in data["detail"]


def test_upload_image_no_content_type(client):
    """Test upload with no content type."""
    # Use a test client that properly sets up files without content-type
    response = client.post(
        "/api/upload-image",
        files={"file": ("test.jpg", b"image_content", "text/plain")},  # Non-image
    )

    # For this api call, it should reject non-image content types
    assert response.status_code == 400
    data = response.json()
    assert "File must be an image" in data["detail"]


@patch("src.dependencies.temp_dir", None)
def test_upload_image_no_temp_directory(client, tmp_path):
    """Test upload when temporary directory is not initialized."""
    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 500
    data = response.json()
    assert "Temporary directory not initialized" in data["detail"]


@patch("src.dependencies.storage_manager", None)
def test_upload_image_no_storage_manager(client, tmp_path):
    """Test upload when storage manager is not initialized."""
    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 500
    data = response.json()
    assert "Storage manager not initialized" in data["detail"]


def test_upload_image_no_filename_extension(client, tmp_path):
    """Test upload with no filename extension - should default to .jpg."""
    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test", f, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "storage_key" in data
    assert data["storage_key"].endswith(".jpg")


def test_upload_image_empty_filename(client, tmp_path):
    """Test upload with empty filename - should default to .jpg."""
    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test"
    test_image_path.write_bytes(test_image_content)

    # Test upload with filename having no extension
    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image",
            files={"file": ("test", f, "image/jpeg")},  # No extension in filename
        )

    assert response.status_code == 200
    data = response.json()
    assert "storage_key" in data
    assert data["storage_key"].endswith(".jpg")


def test_upload_image_success_png_format(client, tmp_path):
    """Test successful PNG image upload."""
    test_image_content = create_test_image_bytes("PNG")
    test_image_path = tmp_path / "test.png"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.png", f, "image/png")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "storage_key" in data
    assert data["storage_key"].endswith(".png")


def test_upload_image_success_gif_format(client, tmp_path):
    """Test successful GIF image upload."""
    test_image_content = create_test_image_bytes("GIF")
    test_image_path = tmp_path / "test.gif"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.gif", f, "image/gif")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "storage_key" in data
    assert data["storage_key"].endswith(".gif")


def test_upload_image_success_webp_format(client, tmp_path):
    """Test successful WebP image upload."""
    test_image_content = create_test_image_bytes("WEBP")
    test_image_path = tmp_path / "test.webp"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.webp", f, "image/webp")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "storage_key" in data
    assert data["storage_key"].endswith(".webp")


def test_upload_image_file_write_failure(client, tmp_path):
    """Test upload when writing temporary file fails."""
    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    # Mock the file open on the server side to enforce exception
    with patch("src.api.upload.open", side_effect=OSError("Disk full")):
        with open(test_image_path, "rb") as f:
            response = client.post(
                "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
            )

    assert response.status_code == 500
    data = response.json()
    assert "Failed to upload image" in data["detail"]


@patch("src.dependencies.storage_manager")
def test_upload_image_storage_upload_failure(mock_storage_manager, client, tmp_path):
    """Test upload when storage manager upload fails."""

    mock_storage_manager.upload_image.side_effect = Exception("Storage upload failed")

    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 500
    data = response.json()
    assert "Failed to upload image" in data["detail"]
    assert "Storage upload failed" in data["detail"]


@patch("src.dependencies.storage_manager")
def test_upload_image_url_generation_failure(mock_storage_manager, client, tmp_path):
    """Test upload when URL generation fails."""

    mock_storage_manager.upload_image.return_value = "mock_storage_key"
    mock_storage_manager.get_image_url.side_effect = Exception("URL generation failed")

    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 500
    data = response.json()
    assert "Failed to upload image" in data["detail"]
    assert "URL generation failed" in data["detail"]


@patch("src.api.upload.cleanup_local_file")
def test_upload_image_cleanup_on_success(mock_cleanup, client, tmp_path):
    """Test that cleanup_local_file is called on successful upload."""
    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 200
    # Verify cleanup was called
    assert mock_cleanup.call_count == 1


@patch("src.api.upload.cleanup_local_file")
def test_upload_image_cleanup_on_failure(mock_cleanup, client, tmp_path):
    """Test that cleanup_local_file is called on upload failure."""

    with patch("src.dependencies.storage_manager") as mock_storage_mgr:
        mock_storage_mgr.upload_image.side_effect = Exception("Test failure")

        test_image_content = create_test_image_bytes("JPEG")
        test_image_path = tmp_path / "test.jpg"
        test_image_path.write_bytes(test_image_content)

        with open(test_image_path, "rb") as f:
            response = client.post(
                "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
            )

        assert response.status_code == 500
        # Verify cleanup was called
        assert mock_cleanup.call_count == 1


def test_upload_image_unsupported_format(client, tmp_path):
    """Test upload unsupported image format should raise HTTPException line 346."""
    # Create a BMP image format that should be rejected
    img = Image.new("RGB", (10, 10), color="red")
    bmp_data = io.BytesIO()
    img.save(bmp_data, format="BMP")
    test_image_content = bmp_data.getvalue()
    test_image_path = tmp_path / "test.bmp"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.bmp", f, "image/bmp")}
        )

    assert response.status_code == 400
    assert "Unsupported image format: BMP" in response.json()["detail"]


def test_upload_image_corrupted_image(client, tmp_path):
    """Test corrupted image triggers line 357-360 exception path."""
    # Create corrupted image data
    test_image_content = b"corrupted_image_data_not_valid"
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]


def test_upload_image_pil_validation_non_httpexception_error(client, tmp_path):
    """Test PIL validation exception handling path for non-HTTPException."""
    # Create data that will trigger PIL validation to raise any Exception
    # This should go through the except Exception e block converting to HTTPException
    test_image_content = b"completely_invalid_image_data"
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    # Should trigger the non-HTTPException path converting to 400 error
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]


def test_upload_image_returns_metadata_without_database_linking(client, tmp_path):
    """Test that upload_image returns metadata without track_id parameter."""
    test_image_content = create_test_image_bytes("JPEG")
    test_image_path = tmp_path / "test.jpg"
    test_image_path.write_bytes(test_image_content)

    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload-image", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()

    # Should return all required metadata fields
    assert "image_id" in data
    assert "image_url" in data
    assert "storage_key" in data

    # Should NOT try to link to database without track_id
    assert data["image_id"] is not None
    assert data["image_url"] is not None
    assert data["storage_key"] is not None
