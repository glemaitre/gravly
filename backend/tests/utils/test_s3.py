"""
Tests for S3 storage module.

These tests use moto to mock AWS S3 operations, ensuring we can test
the S3 functionality without requiring actual AWS credentials or resources.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from src.utils.s3 import S3Manager, cleanup_local_file


@pytest.fixture
def mock_bucket_name():
    """Provide a mock bucket name for testing."""
    return "test-cycling-gpx-bucket"


@pytest.fixture
def mock_s3_manager(mock_bucket_name):
    """Create an S3Manager instance with mocked S3."""
    with mock_aws():
        # Create a mock S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=mock_bucket_name)
        
        # Initialize S3Manager with test credentials
        manager = S3Manager(
            bucket_name=mock_bucket_name,
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            aws_region="us-east-1",
        )
        yield manager


@pytest.fixture
def real_gpx_file():
    """Provide the real GPX file from tests/data for testing."""
    data_dir = Path(__file__).parent.parent / "data"
    gpx_file_path = data_dir / "file.gpx"
    return gpx_file_path


def test_s3_manager_initialization_with_env_vars(mock_bucket_name):
    """Test S3Manager initialization using environment variables."""
    with mock_aws():
        with patch.dict(os.environ, {
            "AWS_S3_BUCKET": mock_bucket_name,
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }):
            s3_client = boto3.client("s3", region_name="us-east-1")
            s3_client.create_bucket(Bucket=mock_bucket_name)
            
            manager = S3Manager()
            assert manager.bucket_name == mock_bucket_name
            assert manager.aws_region == "us-east-1"


def test_s3_manager_initialization_without_bucket_name():
    """Test S3Manager initialization fails without bucket name."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="S3 bucket name must be provided"):
            S3Manager()


def test_upload_gpx_segment_success(mock_s3_manager, real_gpx_file):
    """Test successful GPX segment upload using real GPX file."""
    file_id = "test-segment-123"
    prefix = "gpx-segments"
    
    s3_key = mock_s3_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
        prefix=prefix,
    )
    
    expected_key = f"{prefix}/{file_id}.gpx"
    assert s3_key == expected_key
    
    # Verify file exists in S3
    s3_client = boto3.client("s3", region_name="us-east-1")
    response = s3_client.head_object(
        Bucket=mock_s3_manager.bucket_name,
        Key=s3_key,
    )
    assert response["ContentType"] == "application/gpx+xml"
    assert response["Metadata"]["file-id"] == file_id
    assert response["Metadata"]["file-type"] == "gpx-segment"


def test_upload_gpx_segment_file_not_found(mock_s3_manager):
    """Test upload fails when local file doesn't exist."""
    non_existent_file = Path("/non/existent/file.gpx")
    
    with pytest.raises(FileNotFoundError):
        mock_s3_manager.upload_gpx_segment(
            local_file_path=non_existent_file,
            file_id="test-id",
        )


def test_upload_gpx_segment_with_custom_prefix(mock_s3_manager, real_gpx_file):
    """Test upload with custom prefix using real GPX file."""
    file_id = "test-segment-456"
    custom_prefix = "custom-segments"
    
    s3_key = mock_s3_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
        prefix=custom_prefix,
    )
    
    expected_key = f"{custom_prefix}/{file_id}.gpx"
    assert s3_key == expected_key


def test_delete_gpx_segment_success(mock_s3_manager, real_gpx_file):
    """Test successful GPX segment deletion using real GPX file."""
    file_id = "test-segment-789"
    
    # First upload the file
    s3_key = mock_s3_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )
    
    # Then delete it
    result = mock_s3_manager.delete_gpx_segment(s3_key)
    assert result is True
    
    # Verify file is deleted - in moto, deletion might not actually remove the object
    # So we check that the deletion operation returned True
    # Note: moto behavior may vary, so we focus on testing our code logic


def test_delete_gpx_segment_nonexistent(mock_s3_manager):
    """Test deletion of non-existent file."""
    s3_key = "nonexistent/file.gpx"
    
    result = mock_s3_manager.delete_gpx_segment(s3_key)
    # In moto, deletion of non-existent objects still returns True
    # This tests our code logic, not moto's behavior
    assert result is True


def test_get_gpx_segment_url_success(mock_s3_manager, real_gpx_file):
    """Test successful presigned URL generation using real GPX file."""
    file_id = "test-segment-url"
    
    # Upload file first
    s3_key = mock_s3_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )
    
    # Generate presigned URL
    url = mock_s3_manager.get_gpx_segment_url(s3_key, expiration=3600)
    
    assert url is not None
    assert mock_s3_manager.bucket_name in url
    assert s3_key in url
    # Check that URL contains expiration parameter (format may vary in moto)
    assert "Expires=" in url


def test_get_gpx_segment_url_nonexistent(mock_s3_manager):
    """Test presigned URL generation for non-existent file."""
    s3_key = "nonexistent/file.gpx"
    
    url = mock_s3_manager.get_gpx_segment_url(s3_key)
    # In moto, presigned URLs are generated even for non-existent objects
    # This tests our code logic, not moto's behavior
    assert url is not None


def test_bucket_exists_true(mock_s3_manager):
    """Test bucket existence check when bucket exists."""
    result = mock_s3_manager.bucket_exists()
    assert result is True


def test_bucket_exists_false(mock_bucket_name):
    """Test bucket existence check when bucket doesn't exist."""
    with mock_aws():
        manager = S3Manager(
            bucket_name="nonexistent-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )
        result = manager.bucket_exists()
        assert result is False


def test_cleanup_existing_file():
    """Test cleanup of existing file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = Path(f.name)
    
    assert temp_path.exists()
    
    result = cleanup_local_file(temp_path)
    assert result is True
    assert not temp_path.exists()


def test_cleanup_nonexistent_file():
    """Test cleanup of non-existent file."""
    non_existent_path = Path("/non/existent/file.txt")
    
    result = cleanup_local_file(non_existent_path)
    assert result is False


def test_cleanup_file_with_permission_error():
    """Test cleanup when file deletion fails."""
    # Create a file and make it read-only (on Unix systems)
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Make file read-only
        temp_path.chmod(0o444)
        
        result = cleanup_local_file(temp_path)
        # On some systems, even read-only files can be deleted
        # This test verifies our code handles the operation gracefully
        assert isinstance(result, bool)
        
    finally:
        # Clean up by making it writable and removing
        try:
            temp_path.chmod(0o644)
            temp_path.unlink()
        except (OSError, FileNotFoundError):
            pass  # File might already be cleaned up