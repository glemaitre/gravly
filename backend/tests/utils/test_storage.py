"""
Tests for common storage functionality and the StorageManager Protocol.

These tests cover functionality that is shared between different storage types
and the Protocol interface definition.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from src.utils.storage import (
    StorageManager,
    cleanup_local_file,
    get_storage_manager,
)

from backend.src.utils.config import LocalStorageConfig, S3StorageConfig


def test_cleanup_existing_file(tmp_path):
    """Test cleanup of existing file."""
    temp_path = tmp_path / "test_file.txt"
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


def test_cleanup_file_with_permission_error(tmp_path):
    """Test cleanup when file deletion fails."""
    temp_path = tmp_path / "test_file.txt"
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


def test_cleanup_file_with_mocked_exception(tmp_path):
    """Test cleanup when file deletion raises an exception."""
    temp_path = tmp_path / "test_file.txt"
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


def test_get_storage_manager_local():
    """Test storage factory returns LocalStorageManager for local type."""
    config = LocalStorageConfig(
        storage_type="local",
        storage_root="/tmp/test_storage",
        base_url="http://test:8080/storage",
    )
    manager = get_storage_manager(config)
    from src.utils.storage import LocalStorageManager

    assert isinstance(manager, LocalStorageManager)


def test_get_storage_manager_s3():
    """Test storage factory returns S3Manager for s3 type."""
    config = S3StorageConfig(
        storage_type="s3",
        bucket="test-bucket",
        access_key_id="test-key",
        secret_access_key="test-secret",
        region="us-west-2",
    )
    with patch("src.utils.storage.S3Manager") as mock_s3_manager_class:
        mock_instance = mock_s3_manager_class.return_value
        manager = get_storage_manager(config)
        mock_s3_manager_class.assert_called_once_with(config)
        assert manager == mock_instance


def test_get_storage_manager_invalid_type():
    """Test storage factory raises error for invalid type."""

    # Create a mock config with invalid storage type
    class InvalidStorageConfig:
        storage_type = "invalid"

    with pytest.raises(ValueError, match="Invalid STORAGE_TYPE"):
        get_storage_manager(InvalidStorageConfig())


def test_get_storage_manager_with_local_config():
    """Test storage factory with local configuration."""
    config = LocalStorageConfig(
        storage_type="local",
        storage_root="/tmp/test_storage",
        base_url="http://test:8080/storage",
    )
    manager = get_storage_manager(config)
    from src.utils.storage import LocalStorageManager

    assert isinstance(manager, LocalStorageManager)
    assert manager.storage_root == Path("/tmp/test_storage")
    assert manager.base_url == "http://test:8080/storage"


def test_get_storage_manager_with_s3_config():
    """Test storage factory with S3 configuration."""
    config = S3StorageConfig(
        storage_type="s3",
        bucket="test-bucket",
        access_key_id="test-key",
        secret_access_key="test-secret",
        region="us-west-2",
    )
    with patch("src.utils.storage.S3Manager") as mock_s3_manager_class:
        mock_instance = mock_s3_manager_class.return_value
        manager = get_storage_manager(config)
        mock_s3_manager_class.assert_called_once_with(config)
        assert manager == mock_instance


class MockStorageManager:
    """Mock implementation of StorageManager Protocol for testing."""

    def __init__(self):
        self.upload_calls = []
        self.delete_calls = []
        self.url_calls = []
        self.bucket_calls = []

    def upload_gpx_segment(
        self, local_file_path: Path, file_id: str, prefix: str = "gpx-segments"
    ) -> str:
        """Mock upload implementation."""
        self.upload_calls.append((local_file_path, file_id, prefix))
        return f"{prefix}/{file_id}.gpx"

    def delete_gpx_segment_by_url(self, url: str) -> bool:
        """Mock delete implementation."""
        self.delete_calls.append(url)
        return True

    def get_gpx_segment_url(
        self, storage_key: str, expiration: int = 3600
    ) -> str | None:
        """Mock URL generation implementation."""
        self.url_calls.append((storage_key, expiration))
        return f"https://example.com/{storage_key}"

    def bucket_exists(self) -> bool:
        """Mock bucket existence check implementation."""
        self.bucket_calls.append(())
        return True

    def get_storage_root_prefix(self) -> str:
        """Mock storage root prefix implementation."""
        return "mock://test-bucket"


def test_storage_manager_protocol_interface():
    """Test that StorageManager Protocol defines the correct interface."""
    assert hasattr(StorageManager, "upload_gpx_segment")
    assert hasattr(StorageManager, "delete_gpx_segment_by_url")
    assert hasattr(StorageManager, "get_gpx_segment_url")
    assert hasattr(StorageManager, "bucket_exists")
    assert hasattr(StorageManager, "get_storage_root_prefix")

    upload_method = StorageManager.__dict__["upload_gpx_segment"]
    assert upload_method.__annotations__["return"] is str

    delete_method = StorageManager.__dict__["delete_gpx_segment_by_url"]
    assert delete_method.__annotations__["return"] is bool

    url_method = StorageManager.__dict__["get_gpx_segment_url"]
    assert url_method.__annotations__["return"] == str | None

    bucket_method = StorageManager.__dict__["bucket_exists"]
    assert bucket_method.__annotations__["return"] is bool

    prefix_method = StorageManager.__dict__["get_storage_root_prefix"]
    assert prefix_method.__annotations__["return"] is str


def test_storage_manager_protocol_implementation():
    """Test that a class implementing StorageManager Protocol works correctly."""
    manager = MockStorageManager()

    file_path = Path("/test/file.gpx")
    result = manager.upload_gpx_segment(file_path, "test-id", "test-prefix")
    assert result == "test-prefix/test-id.gpx"
    assert manager.upload_calls == [(file_path, "test-id", "test-prefix")]

    result = manager.delete_gpx_segment_by_url("mock://test-bucket/test/file.gpx")
    assert result is True
    assert manager.delete_calls == ["mock://test-bucket/test/file.gpx"]

    result = manager.get_gpx_segment_url("test/file.gpx", 7200)
    assert result == "https://example.com/test/file.gpx"
    assert manager.url_calls == [("test/file.gpx", 7200)]

    result = manager.bucket_exists()
    assert result is True
    assert manager.bucket_calls == [()]

    # Test get_storage_root_prefix
    result = manager.get_storage_root_prefix()
    assert result == "mock://test-bucket"


def test_storage_manager_protocol_type_checking():
    """Test that type checking works with StorageManager Protocol."""
    manager = MockStorageManager()

    def process_storage_manager(storage: StorageManager) -> str:
        return storage.upload_gpx_segment(Path("/test"), "id")

    result = process_storage_manager(manager)
    assert result == "gpx-segments/id.gpx"


def test_storage_manager_protocol_default_parameters():
    """Test that StorageManager Protocol methods work with default parameters."""
    manager = MockStorageManager()

    result = manager.upload_gpx_segment(Path("/test"), "id")
    assert result == "gpx-segments/id.gpx"
    assert manager.upload_calls[-1] == (Path("/test"), "id", "gpx-segments")

    result = manager.get_gpx_segment_url("test/file.gpx")
    assert result == "https://example.com/test/file.gpx"
    assert manager.url_calls[-1] == ("test/file.gpx", 3600)
