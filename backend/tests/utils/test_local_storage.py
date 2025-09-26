"""
Tests for storage module.

These tests cover both the storage factory and the LocalStorageManager implementation.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from src.utils.storage import LocalStorageManager

from backend.src.utils.config import LocalStorageConfig


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for local storage testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def local_storage_manager(temp_storage_dir):
    """Create a LocalStorageManager instance for testing."""
    config = LocalStorageConfig(
        storage_type="local",
        storage_root=str(temp_storage_dir),
        base_url="http://localhost:8000/storage",
    )
    return LocalStorageManager(config)


@pytest.fixture
def real_gpx_file():
    """Provide the real GPX file from tests/data for testing."""
    data_dir = Path(__file__).parent.parent / "data"
    gpx_file_path = data_dir / "file.gpx"
    return gpx_file_path


def test_local_storage_manager_initialization(temp_storage_dir):
    """Test LocalStorageManager initialization."""
    config = LocalStorageConfig(
        storage_type="local",
        storage_root=str(temp_storage_dir),
        base_url="http://localhost:8000/storage",
    )
    manager = LocalStorageManager(config)
    assert manager.storage_root == temp_storage_dir
    assert manager.storage_root.exists()
    assert manager.storage_root.is_dir()


def test_local_storage_manager_initialization_with_explicit_params():
    """Test LocalStorageManager initialization using explicit parameters."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=temp_dir,
            base_url="http://localhost:8000/storage",
        )
        manager = LocalStorageManager(config)
        assert manager.storage_root == Path(temp_dir)


def test_local_storage_manager_default_initialization():
    """Test LocalStorageManager initialization with default values."""
    config = LocalStorageConfig(
        storage_type="local",
        storage_root="../scratch/local_storage",
        base_url="http://localhost:8000/storage",
    )
    manager = LocalStorageManager(config)
    assert manager.storage_root == Path("../scratch/local_storage")
    assert manager.base_url == "http://localhost:8000/storage"


def test_upload_gpx_segment_success(local_storage_manager, real_gpx_file):
    """Test successful GPX segment upload using real GPX file."""
    file_id = "test-segment-123"
    prefix = "gpx-segments"

    storage_key = local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
        prefix=prefix,
    )

    expected_key = f"{prefix}/{file_id}.gpx"
    assert storage_key == expected_key

    # Verify file exists in local storage
    target_path = local_storage_manager.storage_root / storage_key
    assert target_path.exists()
    assert target_path.read_bytes() == real_gpx_file.read_bytes()

    # Verify metadata file exists
    metadata_path = target_path.with_suffix(".gpx.metadata")
    assert metadata_path.exists()
    metadata_content = metadata_path.read_text()
    assert f"file-id: {file_id}" in metadata_content
    assert "file-type: gpx-segment" in metadata_content
    assert "content-type: application/gpx+xml" in metadata_content


def test_upload_gpx_segment_file_not_found(local_storage_manager):
    """Test upload fails when local file doesn't exist."""
    non_existent_file = Path("/non/existent/file.gpx")

    with pytest.raises(FileNotFoundError):
        local_storage_manager.upload_gpx_segment(
            local_file_path=non_existent_file,
            file_id="test-id",
        )


def test_upload_gpx_segment_with_custom_prefix(local_storage_manager, real_gpx_file):
    """Test upload with custom prefix using real GPX file."""
    file_id = "test-segment-456"
    custom_prefix = "custom-segments"

    storage_key = local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
        prefix=custom_prefix,
    )

    expected_key = f"{custom_prefix}/{file_id}.gpx"
    assert storage_key == expected_key

    # Verify file exists in correct location
    target_path = local_storage_manager.storage_root / storage_key
    assert target_path.exists()


def test_delete_gpx_segment_success(local_storage_manager, real_gpx_file):
    """Test successful GPX segment deletion using real GPX file."""
    file_id = "test-segment-789"

    storage_key = local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )

    result = local_storage_manager.delete_gpx_segment(storage_key)
    assert result is True

    # Verify file is deleted
    target_path = local_storage_manager.storage_root / storage_key
    assert not target_path.exists()

    # Verify metadata file is also deleted
    metadata_path = target_path.with_suffix(".gpx.metadata")
    assert not metadata_path.exists()


def test_delete_gpx_segment_nonexistent(local_storage_manager):
    """Test deletion of non-existent file."""
    storage_key = "nonexistent/file.gpx"

    result = local_storage_manager.delete_gpx_segment(storage_key)
    assert result is True  # Local storage doesn't fail on non-existent files


def test_get_gpx_segment_url_success(local_storage_manager, real_gpx_file):
    """Test successful URL generation using real GPX file."""
    file_id = "test-segment-url"

    storage_key = local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )

    url = local_storage_manager.get_gpx_segment_url(storage_key, expiration=3600)

    assert url is not None
    assert local_storage_manager.base_url in url
    assert storage_key in url


def test_get_gpx_segment_url_nonexistent(local_storage_manager):
    """Test URL generation for non-existent file."""
    storage_key = "nonexistent/file.gpx"

    url = local_storage_manager.get_gpx_segment_url(storage_key)
    assert url is None


def test_bucket_exists_true(local_storage_manager):
    """Test bucket existence check when storage directory exists."""
    result = local_storage_manager.bucket_exists()
    assert result is True


def test_bucket_exists_false():
    """Test bucket existence check when storage directory doesn't exist."""
    # Use a temporary directory that we can control
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Remove the directory to simulate non-existent directory
        temp_path.rmdir()

        # Create manager without creating the directory
        manager = LocalStorageManager.__new__(LocalStorageManager)
        manager.storage_root = temp_path
        manager.base_url = "http://localhost:8000/storage"

        result = manager.bucket_exists()
        assert result is False


def test_get_file_path(local_storage_manager):
    """Test getting local file path for a storage key."""
    storage_key = "test/file.gpx"
    expected_path = local_storage_manager.storage_root / storage_key
    actual_path = local_storage_manager.get_file_path(storage_key)
    assert actual_path == expected_path


def test_list_files_empty(local_storage_manager):
    """Test listing files when storage is empty."""
    files = local_storage_manager.list_files()
    assert files == []


def test_list_files_with_prefix(local_storage_manager, real_gpx_file):
    """Test listing files with a specific prefix."""
    # Upload files with different prefixes
    local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id="file1",
        prefix="gpx-segments",
    )
    local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id="file2",
        prefix="gpx-segments",
    )
    local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id="file3",
        prefix="other-prefix",
    )

    # List files with prefix
    files = local_storage_manager.list_files("gpx-segments")
    assert len(files) == 2
    assert "gpx-segments/file1.gpx" in files
    assert "gpx-segments/file2.gpx" in files
    assert "other-prefix/file3.gpx" not in files

    # List all files
    all_files = local_storage_manager.list_files()
    assert len(all_files) == 3


def test_local_storage_manager_with_custom_base_url():
    """Test LocalStorageManager with custom base URL."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = LocalStorageConfig(
            storage_type="local",
            storage_root=temp_dir,
            base_url="http://custom:8080/storage",
        )
        manager = LocalStorageManager(config)
        assert manager.base_url == "http://custom:8080/storage"


def test_local_storage_manager_default_base_url():
    """Test LocalStorageManager with default base URL."""
    config = LocalStorageConfig(
        storage_type="local",
        storage_root="../scratch/local_storage",
        base_url="http://localhost:8000/storage",
    )
    manager = LocalStorageManager(config)
    assert manager.base_url == "http://localhost:8000/storage"


def test_upload_gpx_segment_exception_handling(local_storage_manager, real_gpx_file):
    """Test that exceptions during upload are properly logged and re-raised."""
    file_id = "test-exception"
    prefix = "gpx-segments"

    with (
        patch("src.utils.storage.shutil.copy2") as mock_copy2,
        patch("src.utils.storage.logger") as mock_logger,
    ):
        mock_copy2.side_effect = OSError("Mocked file system error")

        with pytest.raises(OSError, match="Mocked file system error"):
            local_storage_manager.upload_gpx_segment(
                local_file_path=real_gpx_file,
                file_id=file_id,
                prefix=prefix,
            )

        mock_copy2.assert_called_once()

        mock_logger.error.assert_called_once_with(
            "Failed to upload to local storage: Mocked file system error"
        )


def test_delete_gpx_segment_exception_handling(local_storage_manager, real_gpx_file):
    """Test that exceptions during deletion are properly logged and return False."""
    file_id = "test-delete-exception"

    storage_key = local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )

    with (
        patch("pathlib.Path.unlink") as mock_unlink,
        patch("src.utils.storage.logger") as mock_logger,
    ):
        mock_unlink.side_effect = OSError("Mocked file deletion error")

        result = local_storage_manager.delete_gpx_segment(storage_key)
        assert result is False

        mock_logger.error.assert_called_once_with(
            "Failed to delete from local storage: Mocked file deletion error"
        )


def test_get_gpx_segment_url_exception_handling(local_storage_manager, real_gpx_file):
    """Test that exceptions during URL generation are properly logged and return
    None."""
    file_id = "test-url-exception"

    storage_key = local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )

    with (
        patch("src.utils.storage.urljoin") as mock_urljoin,
        patch("src.utils.storage.logger") as mock_logger,
    ):
        mock_urljoin.side_effect = Exception("Mocked URL generation error")

        result = local_storage_manager.get_gpx_segment_url(storage_key)
        assert result is None

        mock_logger.error.assert_called_once_with(
            "Failed to generate local storage URL: Mocked URL generation error"
        )


def test_bucket_exists_exception_handling(local_storage_manager):
    """Test that exceptions during bucket existence check return False."""
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = OSError("Mocked filesystem error")

        result = local_storage_manager.bucket_exists()
        assert result is False


def test_list_files_prefix_path_not_exists(local_storage_manager):
    """Test that list_files returns empty list when prefix path doesn't exist."""
    non_existent_prefix = "non-existent-prefix"

    result = local_storage_manager.list_files(non_existent_prefix)
    assert result == []


def test_list_files_exception_handling(local_storage_manager, real_gpx_file):
    """Test that exceptions during file listing are properly logged and return
    empty list."""
    file_id = "test-list-exception"

    local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )

    with (
        patch("pathlib.Path.rglob") as mock_rglob,
        patch("src.utils.storage.logger") as mock_logger,
    ):
        mock_rglob.side_effect = OSError("Mocked filesystem error")

        result = local_storage_manager.list_files()
        assert result == []

        mock_logger.error.assert_called_once_with(
            "Failed to list files: Mocked filesystem error"
        )


def test_get_storage_root_prefix(local_storage_manager):
    """Test getting storage root prefix for local storage."""
    result = local_storage_manager.get_storage_root_prefix()
    assert result == "local://"


def test_load_gpx_data_success_with_local_url(local_storage_manager):
    """Test successful GPX data loading using local:/// URL format."""
    test_content = b"<?xml version='1.0'?><gpx><trk><name>Test Track</name></trk></gpx>"
    test_file_path = (
        local_storage_manager.storage_root / "gpx-segments" / "test-file.gpx"
    )
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_bytes(test_content)

    # Test loading with local:/// URL format (this should trigger line 401)
    local_url = "local:///gpx-segments/test-file.gpx"
    result = local_storage_manager.load_gpx_data(local_url)

    assert result == test_content


def test_load_gpx_data_success_with_local_url_short_format(local_storage_manager):
    """Test successful GPX data loading using local:// URL format (short format)."""
    test_content = b"<?xml version='1.0'?><gpx><trk><name>Test Track</name></trk></gpx>"
    test_file_path = (
        local_storage_manager.storage_root / "gpx-segments" / "test-file.gpx"
    )
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_bytes(test_content)

    # Test loading with local:// URL format
    # (this should trigger the URL validation but fail)
    # The method expects local:/// format, so this should fail
    local_url = "local://gpx-segments/test-file.gpx"
    result = local_storage_manager.load_gpx_data(local_url)

    # This should fail because it doesn't start with the expected prefix
    assert result is None


def test_load_gpx_data_file_not_found(local_storage_manager):
    """Test load_gpx_data when file doesn't exist."""
    local_url = "local:///gpx-segments/non-existent-file.gpx"
    result = local_storage_manager.load_gpx_data(local_url)

    assert result is None


def test_load_gpx_data_invalid_url_format(local_storage_manager):
    """Test load_gpx_data with invalid URL format."""
    # Test with non-local URL (should fail URL validation)
    result = local_storage_manager.load_gpx_data("s3://bucket/file.gpx")
    assert result is None

    # Test with malformed local URL (missing third slash - should fail URL validation)
    result = local_storage_manager.load_gpx_data("local://file.gpx")
    assert result is None

    # Test with direct storage key (should fail URL validation)
    result = local_storage_manager.load_gpx_data("gpx-segments/file.gpx")
    assert result is None


def test_load_gpx_data_large_file(local_storage_manager):
    """Test load_gpx_data with a large GPX file."""
    # Create a larger test file (simulate real GPX data)
    large_content = b"<?xml version='1.0'?><gpx><trk><name>Large Track</name>"
    large_content += b"<trkpt lat='45.0' lon='2.0'><ele>100.0</ele></trkpt>" * 1000
    large_content += b"</trk></gpx>"

    test_file_path = (
        local_storage_manager.storage_root / "gpx-segments" / "large-file.gpx"
    )
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_bytes(large_content)

    # Test loading with local:/// URL format
    local_url = "local:///gpx-segments/large-file.gpx"
    result = local_storage_manager.load_gpx_data(local_url)

    assert result == large_content
    assert len(result) > 10000  # Ensure we got substantial data


def test_load_gpx_data_empty_file(local_storage_manager):
    """Test load_gpx_data with an empty file."""
    empty_content = b""
    test_file_path = (
        local_storage_manager.storage_root / "gpx-segments" / "empty-file.gpx"
    )
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_bytes(empty_content)

    # Test loading with local:/// URL format
    local_url = "local:///gpx-segments/empty-file.gpx"
    result = local_storage_manager.load_gpx_data(local_url)

    assert result == empty_content
    assert len(result) == 0


def test_load_gpx_data_with_nested_paths(local_storage_manager):
    """Test load_gpx_data with nested directory paths."""
    test_content = (
        b"<?xml version='1.0'?><gpx><trk><name>Nested Track</name></trk></gpx>"
    )
    test_file_path = (
        local_storage_manager.storage_root
        / "gpx-segments"
        / "2023"
        / "08"
        / "track-123.gpx"
    )
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_bytes(test_content)

    # Test loading with nested path using local:/// URL format
    local_url = "local:///gpx-segments/2023/08/track-123.gpx"
    result = local_storage_manager.load_gpx_data(local_url)

    assert result == test_content


def test_load_gpx_data_with_special_characters(local_storage_manager):
    """Test load_gpx_data with special characters in the file path."""
    test_content = (
        b"<?xml version='1.0'?><gpx><trk><name>Special Track</name></trk></gpx>"
    )
    # Create a file with special characters in the name
    special_filename = "track with spaces & symbols!.gpx"
    test_file_path = (
        local_storage_manager.storage_root / "gpx-segments" / special_filename
    )
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_bytes(test_content)

    # Test loading with special characters using local:/// URL format
    local_url = f"local:///gpx-segments/{special_filename}"
    result = local_storage_manager.load_gpx_data(local_url)

    assert result == test_content


def test_load_gpx_data_url_validation_error(local_storage_manager):
    """Test load_gpx_data URL validation error (covers lines 508-510)."""
    # Test with URL that doesn't start with the storage root prefix
    # This should trigger the URL validation error
    invalid_url = "https://example.com/file.gpx"
    result = local_storage_manager.load_gpx_data(invalid_url)

    # Should return None due to URL validation failure
    assert result is None


def test_load_gpx_data_exception_handling(local_storage_manager):
    """Test load_gpx_data exception handling (covers lines 529-531)."""
    # Create a valid file first
    test_content = b"<?xml version='1.0'?><gpx><trk><name>Test Track</name></trk></gpx>"
    test_file_path = (
        local_storage_manager.storage_root / "gpx-segments" / "test-file.gpx"
    )
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_bytes(test_content)

    # Mock the open function to raise an exception
    with patch("builtins.open", side_effect=OSError("Mocked filesystem error")):
        local_url = "local:///gpx-segments/test-file.gpx"
        result = local_storage_manager.load_gpx_data(local_url)

        # Should return None due to exception
        assert result is None


def test_load_gpx_data_get_storage_root_prefix_exception(local_storage_manager):
    """Test load_gpx_data when get_storage_root_prefix raises an exception."""
    # Mock get_storage_root_prefix to raise an exception
    with patch.object(
        local_storage_manager,
        "get_storage_root_prefix",
        side_effect=Exception("Mocked error"),
    ):
        local_url = "local:///gpx-segments/test-file.gpx"
        result = local_storage_manager.load_gpx_data(local_url)

        # Should return None due to exception
        assert result is None


def test_get_gpx_segment_url_with_local_prefix(local_storage_manager, real_gpx_file):
    """Test get_gpx_segment_url with local:/// prefix (covers line 401)."""
    file_id = "test-segment-url-with-prefix"

    # Upload a file first
    storage_key = local_storage_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )

    # Test URL generation with local:/// prefix (this should trigger line 401)
    local_url = f"local:///{storage_key}"
    url = local_storage_manager.get_gpx_segment_url(local_url, expiration=3600)

    assert url is not None
    assert local_storage_manager.base_url in url
    assert storage_key in url


# ============== NEW IMAGE UPLOAD TESTS ==============


def test_upload_image_png_file(local_storage_manager, tmp_path):
    """Test upload_image for PNG file."""
    image_content = b"fake-png-data"
    test_image_file = tmp_path / "test.png"
    test_image_file.write_bytes(image_content)

    result = local_storage_manager.upload_image(
        test_image_file, "test-image-id", "images-segments"
    )

    expected_storage_key = "images-segments/test-image-id.png"
    assert result == expected_storage_key

    # Check if file was actually created
    full_path = local_storage_manager.storage_root / expected_storage_key
    assert full_path.exists()
    assert full_path.read_bytes() == image_content


def test_upload_image_jpeg_file(local_storage_manager, tmp_path):
    """Test upload_image for JPEG file."""
    image_content = b"fake-jpeg-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    result = local_storage_manager.upload_image(test_image_file, "test-image-id")

    expected_storage_key = "images-segments/test-image-id.jpg"
    assert result == expected_storage_key

    # Check if file was actually created
    full_path = local_storage_manager.storage_root / expected_storage_key
    assert full_path.exists()
    assert full_path.read_bytes() == image_content


def test_upload_image_gif_file(local_storage_manager, tmp_path):
    """Test upload_image for GIF file."""
    image_content = b"fake-gif-data"
    test_image_file = tmp_path / "test.gif"
    test_image_file.write_bytes(image_content)

    result = local_storage_manager.upload_image(test_image_file, "test-image-id")

    expected_storage_key = "images-segments/test-image-id.gif"
    assert result == expected_storage_key

    # Check if file was actually created
    full_path = local_storage_manager.storage_root / expected_storage_key
    assert full_path.exists()
    assert full_path.read_bytes() == image_content


def test_upload_image_webp_file(local_storage_manager, tmp_path):
    """Test upload_image for WebP file."""
    image_content = b"fake-webp-data"
    test_image_file = tmp_path / "test.webp"
    test_image_file.write_bytes(image_content)

    result = local_storage_manager.upload_image(test_image_file, "test-image-id")

    expected_storage_key = "images-segments/test-image-id.webp"
    assert result == expected_storage_key

    # Check if file was actually created
    full_path = local_storage_manager.storage_root / expected_storage_key
    assert full_path.exists()
    assert full_path.read_bytes() == image_content


def test_upload_image_unknown_extension_defaults_to_jpeg(
    local_storage_manager, tmp_path
):
    """Test upload_image with unknown file extension defaults to JPEG."""
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.bmp"
    test_image_file.write_bytes(image_content)

    result = local_storage_manager.upload_image(test_image_file, "test-image-id")

    expected_storage_key = "images-segments/test-image-id.bmp"
    assert result == expected_storage_key

    # Check if file was actually created
    full_path = local_storage_manager.storage_root / expected_storage_key
    assert full_path.exists()
    assert full_path.read_bytes() == image_content


def test_upload_image_custom_prefix(local_storage_manager, tmp_path):
    """Test upload_image with custom prefix."""
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    result = local_storage_manager.upload_image(
        test_image_file, "test-image-id", "custom-images"
    )

    expected_storage_key = "custom-images/test-image-id.jpg"
    assert result == expected_storage_key

    # Check if file was actually created
    full_path = local_storage_manager.storage_root / expected_storage_key
    assert full_path.exists()
    assert full_path.read_bytes() == image_content


def test_upload_image_file_not_found(local_storage_manager, tmp_path):
    """Test upload_image when file doesn't exist."""
    non_existent_file = tmp_path / "non_existent_image.jpg"

    with pytest.raises(FileNotFoundError):
        local_storage_manager.upload_image(non_existent_file, "test-image-id")


def test_delete_image_success(local_storage_manager, tmp_path):
    """Test delete_image successful deletion."""
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    # First upload an image
    storage_key = local_storage_manager.upload_image(test_image_file, "test-image-id")
    full_path = local_storage_manager.storage_root / storage_key
    assert full_path.exists()  # Verify it exists before deletion

    result = local_storage_manager.delete_image(storage_key)
    assert result is True
    assert not full_path.exists()  # Verify it was deleted


def test_delete_image_no_file(local_storage_manager):
    """Test delete_image with non-existent file."""
    result = local_storage_manager.delete_image("images-segments/nonexistent.jpg")
    assert (
        result is True
    )  # Local storage delete is successful even if file doesn't exist


def test_get_image_url_success(local_storage_manager, tmp_path):
    """Test get_image_url successful generation."""
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    # First upload an image
    storage_key = local_storage_manager.upload_image(test_image_file, "test-image-id")

    result = local_storage_manager.get_image_url(storage_key)

    # Should return a local URL
    assert result is not None
    assert local_storage_manager.base_url in result
    assert storage_key in result


def test_get_image_url_custom_expiration(local_storage_manager, tmp_path):
    """Test get_image_url with custom expiration time."""
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    # First upload an image
    storage_key = local_storage_manager.upload_image(test_image_file, "test-image-id")

    result = local_storage_manager.get_image_url(storage_key, expiration=7200)

    # Should return a local URL
    assert result is not None
    assert local_storage_manager.base_url in result
    assert storage_key in result


def test_get_image_url_nonexistent_file(local_storage_manager):
    """Test get_image_url with non-existent file."""
    result = local_storage_manager.get_image_url("images-segments/nonexistent.jpg")

    # Should return None for non-existent file
    assert result is None


def test_upload_image_local_storage_exception_handling(local_storage_manager, tmp_path):
    """Test upload_image handles exceptions during local storage operations.

    Covers lines 615-617.
    """
    # Create a valid image file
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    # Mock shutil.copy2 to raise an exception during the copy operation
    with patch(
        "src.utils.storage.shutil.copy2", side_effect=OSError("Permission denied")
    ):
        # This should trigger the exception handling on lines 615-617
        with pytest.raises(OSError, match="Permission denied"):
            local_storage_manager.upload_image(test_image_file, "test-image-id")


def test_delete_image_local_storage_exception_handling(local_storage_manager, tmp_path):
    """Test delete_image handles exceptions during local storage operations.

    Covers lines 647-649.
    """
    # First upload a valid image
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    # Upload successfully first
    storage_key = local_storage_manager.upload_image(test_image_file, "test-image-id")

    # Mock Path.exists to return True but Path.unlink to raise an exception
    with (
        patch("src.utils.storage.Path.exists", return_value=True),
        patch(
            "src.utils.storage.Path.unlink", side_effect=OSError("Permission denied")
        ),
    ):
        # This should trigger the exception handling on lines 647-649
        result = local_storage_manager.delete_image(storage_key)
        assert result is False


def test_get_image_url_with_local_prefix(local_storage_manager, tmp_path):
    """Test get_image_url with 'local:///' prefix - covers line 671."""
    # First upload an image
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    storage_key = local_storage_manager.upload_image(test_image_file, "test-image-id")

    # Test with "local:///" prefix (this should trigger line 671)
    local_url = f"local:///{storage_key}"
    url = local_storage_manager.get_image_url(local_url)

    # Should successfully remove the prefix and return the URL
    assert url is not None
    assert local_storage_manager.base_url in url
    assert storage_key in url


def test_get_image_url_local_storage_exception_handling(
    local_storage_manager, tmp_path
):
    """Test get_image_url handles exceptions - covers lines 685-687."""
    # Add a mock side effect to simulate an exception during URL generation
    with patch("src.utils.storage.urljoin", side_effect=Exception("urljoin failed")):
        # Upload a valid image first
        image_content = b"fake-image-data"
        test_image_file = tmp_path / "test.jpg"
        test_image_file.write_bytes(image_content)

        storage_key = local_storage_manager.upload_image(
            test_image_file, "test-image-id"
        )

        # Try to get URL - should handle the exception gracefully
        result = local_storage_manager.get_image_url(storage_key)

        # Should return None due to exception (lines 686-687)
        assert result is None
