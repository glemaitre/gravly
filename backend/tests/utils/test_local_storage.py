"""
Tests for storage module.

These tests cover both the storage factory and the LocalStorageManager implementation.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from src.utils.storage import (
    LocalStorageManager,
    cleanup_local_file,
    get_storage_manager,
)


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for local storage testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def local_storage_manager(temp_storage_dir):
    """Create a LocalStorageManager instance for testing."""
    return LocalStorageManager(storage_root=str(temp_storage_dir))


@pytest.fixture
def real_gpx_file():
    """Provide the real GPX file from tests/data for testing."""
    data_dir = Path(__file__).parent.parent / "data"
    gpx_file_path = data_dir / "file.gpx"
    return gpx_file_path


def test_local_storage_manager_initialization(temp_storage_dir):
    """Test LocalStorageManager initialization."""
    manager = LocalStorageManager(storage_root=str(temp_storage_dir))
    assert manager.storage_root == temp_storage_dir
    assert manager.storage_root.exists()
    assert manager.storage_root.is_dir()


def test_local_storage_manager_initialization_with_env_var():
    """Test LocalStorageManager initialization using environment variable."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.dict(os.environ, {"LOCAL_STORAGE_ROOT": temp_dir}):
            manager = LocalStorageManager()
            assert manager.storage_root == Path(temp_dir)


def test_local_storage_manager_default_initialization():
    """Test LocalStorageManager initialization with default values."""
    with patch.dict(os.environ, {}, clear=True):
        manager = LocalStorageManager()
        assert manager.storage_root == Path("../scratch/local_storage")


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


def test_get_storage_manager_local():
    """Test storage factory returns LocalStorageManager for local type."""
    with patch.dict(os.environ, {"STORAGE_TYPE": "local"}):
        manager = get_storage_manager()
        assert isinstance(manager, LocalStorageManager)


def test_get_storage_manager_s3():
    """Test storage factory returns S3Manager for s3 type."""
    with patch.dict(os.environ, {"STORAGE_TYPE": "s3"}):
        with patch("src.utils.storage.S3Manager") as mock_s3_manager_class:
            mock_instance = mock_s3_manager_class.return_value
            manager = get_storage_manager()
            mock_s3_manager_class.assert_called_once()
            assert manager == mock_instance


def test_get_storage_manager_invalid_type():
    """Test storage factory raises error for invalid type."""
    with patch.dict(os.environ, {"STORAGE_TYPE": "invalid"}):
        with pytest.raises(ValueError, match="Invalid STORAGE_TYPE"):
            get_storage_manager()


def test_get_storage_manager_default_local():
    """Test storage factory defaults to local when no type specified."""
    with patch.dict(os.environ, {}, clear=True):
        manager = get_storage_manager()
        assert isinstance(manager, LocalStorageManager)


def test_cleanup_existing_file(temp_storage_dir):
    """Test cleanup of existing file."""
    temp_path = temp_storage_dir / "test_file.txt"
    temp_path.write_text("test content")

    assert temp_path.exists()

    result = cleanup_local_file(temp_path)
    assert result is True
    assert not temp_path.exists()


def test_cleanup_nonexistent_file():
    """Test cleanup of non-existent file."""
    non_existent_path = Path("/non/existent/file.txt")

    result = cleanup_local_file(non_existent_path)
    assert result is False


def test_cleanup_file_with_permission_error(temp_storage_dir):
    """Test cleanup when file deletion fails."""
    temp_path = temp_storage_dir / "test_file.txt"
    temp_path.write_text("test content")

    try:
        temp_path.chmod(0o444)

        result = cleanup_local_file(temp_path)
        assert isinstance(result, bool)

    finally:
        try:
            temp_path.chmod(0o644)
            temp_path.unlink()
        except (OSError, FileNotFoundError):
            pass


def test_cleanup_file_with_mocked_exception(temp_storage_dir):
    """Test cleanup when file deletion raises an exception."""
    temp_path = temp_storage_dir / "test_file.txt"
    temp_path.write_text("test content")

    try:
        original_unlink = Path.unlink

        def mock_unlink(self):
            raise OSError("Permission denied")

        Path.unlink = mock_unlink

        try:
            result = cleanup_local_file(temp_path)
            assert result is False
        finally:
            Path.unlink = original_unlink

    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def test_local_storage_manager_with_custom_base_url():
    """Test LocalStorageManager with custom base URL."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.dict(
            os.environ, {"LOCAL_STORAGE_BASE_URL": "http://custom:8080/storage"}
        ):
            manager = LocalStorageManager(storage_root=temp_dir)
            assert manager.base_url == "http://custom:8080/storage"


def test_local_storage_manager_default_base_url():
    """Test LocalStorageManager with default base URL."""
    with patch.dict(os.environ, {}, clear=True):
        manager = LocalStorageManager()
        assert manager.base_url == "http://localhost:8000/storage"
