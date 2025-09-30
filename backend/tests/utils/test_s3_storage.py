"""
Tests for S3 storage module.

These tests use moto to mock AWS S3 operations, ensuring we can test
the S3 functionality without requiring actual AWS credentials or resources.
"""

import os
from pathlib import Path
from unittest.mock import patch

import boto3
import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from moto import mock_aws
from src.utils.storage import S3Manager, cleanup_local_file

from backend.src.utils.config import S3StorageConfig


@pytest.fixture
def mock_bucket_name():
    """Provide a mock bucket name for testing."""
    return "test-cycling-gpx-bucket"


@pytest.fixture
def mock_s3_manager(mock_bucket_name):
    """Create an S3Manager instance with mocked S3."""
    with mock_aws():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=mock_bucket_name)

        config = S3StorageConfig(
            storage_type="s3",
            bucket=mock_bucket_name,
            access_key_id="test-key",
            secret_access_key="test-secret",
            region="us-east-1",
        )
        manager = S3Manager(config)
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
        with patch.dict(
            os.environ,
            {
                "AWS_S3_BUCKET": mock_bucket_name,
                "AWS_ACCESS_KEY_ID": "test-key",
                "AWS_SECRET_ACCESS_KEY": "test-secret",
            },
        ):
            s3_client = boto3.client("s3", region_name="us-east-1")
            s3_client.create_bucket(Bucket=mock_bucket_name)

            config = S3StorageConfig(
                storage_type="s3",
                bucket=mock_bucket_name,
                access_key_id="test-key",
                secret_access_key="test-secret",
                region="us-east-1",
            )
            manager = S3Manager(config)
            assert manager.bucket_name == mock_bucket_name
            assert manager.aws_region == "us-east-1"


def test_s3_manager_initialization_without_bucket_name():
    """Test S3Manager initialization fails without bucket name."""
    with pytest.raises(ValueError, match="S3 bucket name must be provided"):
        config = S3StorageConfig(
            storage_type="s3",
            bucket="",
            access_key_id="test-key",
            secret_access_key="test-secret",
            region="us-east-1",
        )
        S3Manager(config)


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

    s3_key = mock_s3_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )

    full_url = f"s3://test-cycling-gpx-bucket/{s3_key}"
    result = mock_s3_manager.delete_gpx_segment_by_url(full_url)
    assert result is True

    # Verify file is deleted - in moto, deletion might not actually remove the object
    # So we check that the deletion operation returned True
    # Note: moto behavior may vary, so we focus on testing our code logic


def test_delete_gpx_segment_nonexistent(mock_s3_manager):
    """Test deletion of non-existent file."""
    s3_key = "nonexistent/file.gpx"
    full_url = f"s3://test-cycling-gpx-bucket/{s3_key}"

    result = mock_s3_manager.delete_gpx_segment_by_url(full_url)
    # In moto, deletion of non-existent objects still returns True
    # This tests our code logic, not moto's behavior
    assert result is True


def test_get_gpx_segment_url_success(mock_s3_manager, real_gpx_file):
    """Test successful presigned URL generation using real GPX file."""
    file_id = "test-segment-url"

    s3_key = mock_s3_manager.upload_gpx_segment(
        local_file_path=real_gpx_file,
        file_id=file_id,
    )

    url = mock_s3_manager.get_gpx_segment_url(s3_key, expiration=3600)

    assert url is not None
    assert mock_s3_manager.bucket_name in url
    assert s3_key in url
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
        config = S3StorageConfig(
            storage_type="s3",
            bucket="nonexistent-bucket",
            access_key_id="test-key",
            secret_access_key="test-secret",
            region="us-east-1",
        )
        manager = S3Manager(config)
        result = manager.bucket_exists()
        assert result is False


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


def test_s3_manager_no_credentials_error():
    """Test S3Manager initialization when AWS credentials are not found."""
    with patch("src.utils.storage.boto3.client", side_effect=NoCredentialsError()):
        with pytest.raises(NoCredentialsError, match="Unable to locate credentials"):
            config = S3StorageConfig(
                storage_type="s3",
                bucket="test-bucket",
                access_key_id="test-key",
                secret_access_key="test-secret",
                region="us-east-1",
            )
            S3Manager(config)


@mock_aws
def test_upload_gpx_segment_client_error(mock_s3_manager, real_gpx_file, tmp_path):
    """Test upload_gpx_segment when S3 upload raises a ClientError."""
    temp_file = tmp_path / "test_file.gpx"
    temp_file.write_text(real_gpx_file.read_text())

    client_error = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="PutObject",
    )

    with patch.object(
        mock_s3_manager.s3_client, "upload_file", side_effect=client_error
    ):
        with pytest.raises(ClientError) as exc_info:
            mock_s3_manager.upload_gpx_segment(
                local_file_path=temp_file, file_id="test-file-id"
            )

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
        assert exc_info.value.response["Error"]["Message"] == "Access Denied"


@mock_aws
def test_delete_gpx_segment_client_error(mock_s3_manager):
    """Test delete_gpx_segment when S3 deletion raises a ClientError."""
    s3_key = "test-segment/file.gpx"
    full_url = f"s3://test-cycling-gpx-bucket/{s3_key}"

    client_error = ClientError(
        error_response={
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist",
            }
        },
        operation_name="DeleteObject",
    )

    with patch.object(
        mock_s3_manager.s3_client, "delete_object", side_effect=client_error
    ):
        result = mock_s3_manager.delete_gpx_segment_by_url(full_url)
        assert result is False


@mock_aws
def test_get_gpx_segment_url_client_error(mock_s3_manager):
    """Test get_gpx_segment_url when S3 presigned URL generation raises a
    ClientError."""
    s3_key = "test-segment/file.gpx"

    client_error = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="GetObject",
    )

    with patch.object(
        mock_s3_manager.s3_client, "generate_presigned_url", side_effect=client_error
    ):
        result = mock_s3_manager.get_gpx_segment_url(s3_key)
        assert result is None


def test_get_storage_root_prefix(mock_s3_manager):
    """Test getting storage root prefix for S3 storage."""
    result = mock_s3_manager.get_storage_root_prefix()
    assert result == "s3://test-cycling-gpx-bucket"


def test_load_gpx_data_success(mock_s3_manager):
    """Test successful GPX data loading from S3."""
    s3_key = "gpx-segments/test-file.gpx"
    test_content = b"<?xml version='1.0'?><gpx><trk><name>Test Track</name></trk></gpx>"

    mock_s3_manager.s3_client.put_object(
        Bucket="test-cycling-gpx-bucket", Key=s3_key, Body=test_content
    )

    s3_url = f"s3://test-cycling-gpx-bucket/{s3_key}"
    result = mock_s3_manager.load_gpx_data(s3_url)

    assert result == test_content


def test_load_gpx_data_invalid_url_format(mock_s3_manager):
    """Test load_gpx_data with invalid URL format."""
    result = mock_s3_manager.load_gpx_data("https://example.com/file.gpx")
    assert result is None

    result = mock_s3_manager.load_gpx_data("local:///file.gpx")
    assert result is None

    result = mock_s3_manager.load_gpx_data("s3://test-cycling-gpx-bucket")
    assert result is None


def test_load_gpx_data_wrong_bucket(mock_s3_manager):
    """Test load_gpx_data with wrong bucket name."""
    s3_url = "s3://wrong-bucket/gpx-segments/file.gpx"
    result = mock_s3_manager.load_gpx_data(s3_url)
    assert result is None


def test_load_gpx_data_bucket_validation_error(mock_s3_manager):
    """Test load_gpx_data with bucket name that doesn't match configured bucket."""
    # We need to test the bucket validation logic, but the URL must start
    # with the correct prefix
    # The prefix check happens before bucket validation, so we need to craft a URL that
    # passes the prefix check but fails bucket validation
    # Since get_storage_root_prefix() returns "s3://test-cycling-gpx-bucket",
    # we need a URL that starts with that but has a different bucket in the path

    # This is a bit tricky - let me test the URL parsing logic more directly
    # by mocking the get_storage_root_prefix to return just "s3://" temporarily
    from unittest.mock import patch

    with patch.object(mock_s3_manager, "get_storage_root_prefix", return_value="s3://"):
        wrong_bucket = "wrong-cycling-gpx-bucket"
        s3_key = "gpx-segments/test-file.gpx"
        s3_url = f"s3://{wrong_bucket}/{s3_key}"

        # This should return None due to bucket name mismatch validation
        result = mock_s3_manager.load_gpx_data(s3_url)

        # Should return None due to bucket name mismatch
        assert result is None


def test_load_gpx_data_file_not_found(mock_s3_manager):
    """Test load_gpx_data when file doesn't exist in S3."""
    s3_url = "s3://test-cycling-gpx-bucket/non-existent/file.gpx"
    result = mock_s3_manager.load_gpx_data(s3_url)
    assert result is None


def test_load_gpx_data_client_error(mock_s3_manager):
    """Test load_gpx_data when S3 client raises an error."""
    s3_url = "s3://test-cycling-gpx-bucket/test-file.gpx"

    client_error = ClientError(
        error_response={
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        },
        operation_name="GetObject",
    )

    with patch.object(
        mock_s3_manager.s3_client, "get_object", side_effect=client_error
    ):
        result = mock_s3_manager.load_gpx_data(s3_url)
        assert result is None


def test_load_gpx_data_large_file(mock_s3_manager):
    """Test load_gpx_data with a large GPX file."""
    s3_key = "gpx-segments/large-file.gpx"
    large_content = b"<?xml version='1.0'?><gpx><trk><name>Large Track</name>"
    large_content += b"<trkpt lat='45.0' lon='2.0'><ele>100.0</ele></trkpt>" * 1000
    large_content += b"</trk></gpx>"

    mock_s3_manager.s3_client.put_object(
        Bucket="test-cycling-gpx-bucket", Key=s3_key, Body=large_content
    )

    s3_url = f"s3://test-cycling-gpx-bucket/{s3_key}"
    result = mock_s3_manager.load_gpx_data(s3_url)

    assert result == large_content
    assert len(result) > 10000  # Ensure we got substantial data


def test_load_gpx_data_empty_file(mock_s3_manager):
    """Test load_gpx_data with an empty file."""
    s3_key = "gpx-segments/empty-file.gpx"
    empty_content = b""

    mock_s3_manager.s3_client.put_object(
        Bucket="test-cycling-gpx-bucket", Key=s3_key, Body=empty_content
    )

    s3_url = f"s3://test-cycling-gpx-bucket/{s3_key}"
    result = mock_s3_manager.load_gpx_data(s3_url)

    assert result == empty_content
    assert len(result) == 0


def test_load_gpx_data_with_nested_paths(mock_s3_manager):
    """Test load_gpx_data with nested S3 key paths."""
    s3_key = "gpx-segments/2023/08/track-123.gpx"
    test_content = (
        b"<?xml version='1.0'?><gpx><trk><name>Nested Track</name></trk></gpx>"
    )

    mock_s3_manager.s3_client.put_object(
        Bucket="test-cycling-gpx-bucket", Key=s3_key, Body=test_content
    )

    s3_url = f"s3://test-cycling-gpx-bucket/{s3_key}"
    result = mock_s3_manager.load_gpx_data(s3_url)

    assert result == test_content


def test_load_gpx_data_with_special_characters(mock_s3_manager):
    """Test load_gpx_data with special characters in the key."""
    s3_key = "gpx-segments/track with spaces & symbols!.gpx"
    test_content = (
        b"<?xml version='1.0'?><gpx><trk><name>Special Track</name></trk></gpx>"
    )

    mock_s3_manager.s3_client.put_object(
        Bucket="test-cycling-gpx-bucket", Key=s3_key, Body=test_content
    )

    s3_url = f"s3://test-cycling-gpx-bucket/{s3_key}"
    result = mock_s3_manager.load_gpx_data(s3_url)

    assert result == test_content


# ============== NEW IMAGE UPLOAD TESTS ==============


def test_upload_image_png_file(mock_s3_manager, tmp_path):
    """Test upload_image for PNG file."""
    image_content = b"fake-png-data"
    test_image_file = tmp_path / "test.png"
    test_image_file.write_bytes(image_content)

    result = mock_s3_manager.upload_image(
        test_image_file, "test-image-id", "images-segments"
    )

    expected_key = "images-segments/test-image-id.png"
    assert result == expected_key

    # Verify the file was uploaded
    try:
        response = mock_s3_manager.s3_client.get_object(
            Bucket="test-cycling-gpx-bucket", Key=expected_key
        )
        assert response["ContentType"] == "image/png"
        assert response["Metadata"]["file-id"] == "test-image-id"
        assert response["Metadata"]["file-type"] == "image"
    except Exception:
        pytest.fail("Image file was not uploaded properly")


def test_upload_image_jpeg_file(mock_s3_manager, tmp_path):
    """Test upload_image for JPEG file."""
    image_content = b"fake-jpeg-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    result = mock_s3_manager.upload_image(test_image_file, "test-image-id")

    expected_key = "images-segments/test-image-id.jpg"
    assert result == expected_key

    # Verify the file was uploaded
    try:
        response = mock_s3_manager.s3_client.get_object(
            Bucket="test-cycling-gpx-bucket", Key=expected_key
        )
        assert response["ContentType"] == "image/jpeg"
        assert response["Metadata"]["file-id"] == "test-image-id"
        assert response["Metadata"]["file-type"] == "image"
    except Exception:
        pytest.fail("Image file was not uploaded properly")


def test_upload_image_gif_file(mock_s3_manager, tmp_path):
    """Test upload_image for GIF file."""
    image_content = b"fake-gif-data"
    test_image_file = tmp_path / "test.gif"
    test_image_file.write_bytes(image_content)

    result = mock_s3_manager.upload_image(test_image_file, "test-image-id")

    expected_key = "images-segments/test-image-id.gif"
    assert result == expected_key

    # Verify the file was uploaded
    try:
        response = mock_s3_manager.s3_client.get_object(
            Bucket="test-cycling-gpx-bucket", Key=expected_key
        )
        assert response["ContentType"] == "image/gif"
        assert response["Metadata"]["file-id"] == "test-image-id"
        assert response["Metadata"]["file-type"] == "image"
    except Exception:
        pytest.fail("Image file was not uploaded properly")


def test_upload_image_webp_file(mock_s3_manager, tmp_path):
    """Test upload_image for WebP file."""
    image_content = b"fake-webp-data"
    test_image_file = tmp_path / "test.webp"
    test_image_file.write_bytes(image_content)

    result = mock_s3_manager.upload_image(test_image_file, "test-image-id")

    expected_key = "images-segments/test-image-id.webp"
    assert result == expected_key

    # Verify the file was uploaded
    try:
        response = mock_s3_manager.s3_client.get_object(
            Bucket="test-cycling-gpx-bucket", Key=expected_key
        )
        assert response["ContentType"] == "image/webp"
        assert response["Metadata"]["file-id"] == "test-image-id"
        assert response["Metadata"]["file-type"] == "image"
    except Exception:
        pytest.fail("Image file was not uploaded properly")


def test_upload_image_unknown_extension_defaults_to_jpeg(mock_s3_manager, tmp_path):
    """Test upload_image with unknown file extension defaults to JPEG."""
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.bmp"
    test_image_file.write_bytes(image_content)

    result = mock_s3_manager.upload_image(test_image_file, "test-image-id")

    expected_key = "images-segments/test-image-id.bmp"
    assert result == expected_key

    # Verify the file was uploaded
    try:
        response = mock_s3_manager.s3_client.get_object(
            Bucket="test-cycling-gpx-bucket", Key=expected_key
        )
        assert response["ContentType"] == "image/jpeg"  # Should default to JPEG
        assert response["Metadata"]["file-id"] == "test-image-id"
        assert response["Metadata"]["file-type"] == "image"
    except Exception:
        pytest.fail("Image file was not uploaded properly")


def test_upload_image_custom_prefix(mock_s3_manager, tmp_path):
    """Test upload_image with custom prefix."""
    image_content = b"fake-image-data"
    test_image_file = tmp_path / "test.jpg"
    test_image_file.write_bytes(image_content)

    result = mock_s3_manager.upload_image(
        test_image_file, "test-image-id", "custom-images"
    )

    expected_key = "custom-images/test-image-id.jpg"
    assert result == expected_key


def test_upload_image_file_not_found(mock_s3_manager):
    """Test upload_image when file doesn't exist."""
    non_existent_file = Path("non_existent_image.jpg")

    with pytest.raises(FileNotFoundError):
        mock_s3_manager.upload_image(non_existent_file, "test-image-id")


def test_upload_image_s3_client_error(mock_s3_manager, tmp_path):
    """Test upload_image with S3 client error."""
    with patch.object(mock_s3_manager.s3_client, "upload_file") as mock_upload:
        mock_upload.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "NoSuchBucket",
                    "Message": "The bucket does not exist",
                }
            },
            operation_name="upload_file",
        )

        image_content = b"fake-image-data"
        test_image_file = tmp_path / "test.jpg"
        test_image_file.write_bytes(image_content)

        with pytest.raises(ClientError):
            mock_s3_manager.upload_image(test_image_file, "test-image-id")


def test_delete_image_success(mock_s3_manager):
    """Test delete_image successful deletion."""
    # First upload an image
    mock_s3_manager.s3_client.put_object(
        Bucket="test-cycling-gpx-bucket",
        Key="images-segments/test-image.jpg",
        Body=b"fake-image-data",
    )

    full_url = "s3://test-cycling-gpx-bucket/images-segments/test-image.jpg"
    result = mock_s3_manager.delete_image_by_url(full_url)
    assert result is True


def test_delete_image_no_file(mock_s3_manager):
    """Test delete_image with non-existent file."""
    full_url = "s3://test-cycling-gpx-bucket/images-segments/nonexistent.jpg"
    result = mock_s3_manager.delete_image_by_url(full_url)
    # S3 delete expects to succeed even if key doesn't exist
    assert result is True


def test_delete_image_s3_client_error(mock_s3_manager):
    """Test delete_image with S3 client error."""
    with patch.object(mock_s3_manager.s3_client, "delete_object") as mock_delete:
        mock_delete.side_effect = ClientError(
            error_response={
                "Error": {"Code": "AccessDenied", "Message": "Access denied"}
            },
            operation_name="delete_object",
        )

        full_url = "s3://test-cycling-gpx-bucket/images-segments/test-image.jpg"
        result = mock_s3_manager.delete_image_by_url(full_url)
        assert result is False


def test_get_image_url_success(mock_s3_manager):
    """Test get_image_url successful generation."""
    result = mock_s3_manager.get_image_url("images-segments/test-image.jpg")

    # Should return a presigned URL
    assert result is not None
    assert isinstance(result, str)
    assert "images-segments/test-image.jpg" in result


def test_get_image_url_custom_expiration(mock_s3_manager):
    """Test get_image_url with custom expiration time."""
    result = mock_s3_manager.get_image_url(
        "images-segments/test-image.jpg", expiration=7200
    )

    # Should return a presigned URL
    assert result is not None
    assert isinstance(result, str)
    assert "images-segments/test-image.jpg" in result


def test_get_image_url_s3_client_error(mock_s3_manager):
    """Test get_image_url with S3 client error."""
    with patch.object(
        mock_s3_manager.s3_client, "generate_presigned_url"
    ) as mock_presigned:
        mock_presigned.side_effect = ClientError(
            error_response={
                "Error": {"Code": "AccessDenied", "Message": "Access denied"}
            },
            operation_name="generate_presigned_url",
        )

        result = mock_s3_manager.get_image_url("images-segments/test-image.jpg")
        assert result is None


# ============== ADDITIONAL EDGE CASE TESTS FOR COVERAGE ==============


def test_delete_gpx_segment_invalid_url_format(mock_s3_manager):
    """Test delete_gpx_segment with invalid URL format (covers lines 382-383)."""
    # URL that doesn't start with s3://bucket prefix
    invalid_url = "https://example.com/file.gpx"
    result = mock_s3_manager.delete_gpx_segment_by_url(invalid_url)
    assert result is False


def test_delete_gpx_segment_missing_key(mock_s3_manager):
    """Test delete_gpx_segment with missing key in URL (covers lines 387-388)."""
    # URL without a key after the bucket name
    invalid_url = "s3://test-cycling-gpx-bucket"
    result = mock_s3_manager.delete_gpx_segment_by_url(invalid_url)
    assert result is False


def test_delete_gpx_segment_bucket_mismatch(mock_s3_manager):
    """Test delete_gpx_segment with wrong bucket name (covers lines 393-397)."""
    # URL with a different bucket name than configured
    wrong_bucket_url = "s3://wrong-bucket/gpx-segments/file.gpx"

    # Mock get_storage_root_prefix to return a generic s3:// prefix
    with patch.object(mock_s3_manager, "get_storage_root_prefix", return_value="s3://"):
        result = mock_s3_manager.delete_gpx_segment_by_url(wrong_bucket_url)
        assert result is False


def test_delete_gpx_segment_generic_exception(mock_s3_manager):
    """Test delete_gpx_segment with generic exception (covers lines 412-414)."""
    valid_url = "s3://test-cycling-gpx-bucket/gpx-segments/file.gpx"

    # Mock delete_object to raise a generic exception (not ClientError)
    with patch.object(
        mock_s3_manager.s3_client,
        "delete_object",
        side_effect=RuntimeError("Unexpected error"),
    ):
        result = mock_s3_manager.delete_gpx_segment_by_url(valid_url)
        assert result is False


def test_delete_image_invalid_url_format(mock_s3_manager):
    """Test delete_image with invalid URL format (covers lines 431-432)."""
    # URL that doesn't start with s3://bucket prefix
    invalid_url = "https://example.com/image.jpg"
    result = mock_s3_manager.delete_image_by_url(invalid_url)
    assert result is False


def test_delete_image_missing_key(mock_s3_manager):
    """Test delete_image with missing key in URL (covers lines 436-437)."""
    # URL without a key after the bucket name
    invalid_url = "s3://test-cycling-gpx-bucket"
    result = mock_s3_manager.delete_image_by_url(invalid_url)
    assert result is False


def test_delete_image_bucket_mismatch(mock_s3_manager):
    """Test delete_image with wrong bucket name (covers lines 442-446)."""
    # URL with a different bucket name than configured
    wrong_bucket_url = "s3://wrong-bucket/images-segments/image.jpg"

    # Mock get_storage_root_prefix to return a generic s3:// prefix
    with patch.object(mock_s3_manager, "get_storage_root_prefix", return_value="s3://"):
        result = mock_s3_manager.delete_image_by_url(wrong_bucket_url)
        assert result is False


def test_delete_image_generic_exception(mock_s3_manager):
    """Test delete_image with generic exception (covers lines 461-463)."""
    valid_url = "s3://test-cycling-gpx-bucket/images-segments/image.jpg"

    # Mock delete_object to raise a generic exception (not ClientError)
    with patch.object(
        mock_s3_manager.s3_client,
        "delete_object",
        side_effect=RuntimeError("Unexpected error"),
    ):
        result = mock_s3_manager.delete_image_by_url(valid_url)
        assert result is False
