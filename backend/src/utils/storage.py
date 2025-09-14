"""
Storage Module

This module provides a unified storage interface that can work with both AWS S3
and local filesystem storage, allowing seamless switching between production
and local development environments.
"""

import logging
import os
from pathlib import Path
from typing import Protocol
from urllib.parse import urljoin

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class StorageManager(Protocol):
    """Protocol defining the storage manager interface."""

    def upload_gpx_segment(
        self, local_file_path: Path, file_id: str, prefix: str = "gpx-segments"
    ) -> str:
        """Upload a GPX segment file to storage."""
        ...

    def delete_gpx_segment(self, storage_key: str) -> bool:
        """Delete a GPX segment file from storage."""
        ...

    def get_gpx_segment_url(
        self, storage_key: str, expiration: int = 3600
    ) -> str | None:
        """Generate a URL for accessing a GPX segment file."""
        ...

    def bucket_exists(self) -> bool:
        """Check if the storage bucket/container exists and is accessible."""
        ...


class S3Manager:
    """Manages S3 operations for GPX file storage."""

    def __init__(
        self,
        bucket_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_region: str = "us-east-1",
    ):
        """Initialize S3 manager with credentials and configuration.

        Parameters
        ----------
        bucket_name : Optional[str]
            S3 bucket name. If None, will use AWS_S3_BUCKET environment variable.
        aws_access_key_id : Optional[str]
            AWS access key ID. If None, will use AWS_ACCESS_KEY_ID environment variable.
        aws_secret_access_key : Optional[str]
            AWS secret access key. If None, will use AWS_SECRET_ACCESS_KEY
            environment variable.
        aws_region : str
            AWS region name. Defaults to "us-east-1".
        """
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET")
        self.aws_region = aws_region

        if not self.bucket_name:
            raise ValueError(
                "S3 bucket name must be provided or set in AWS_S3_BUCKET environment"
                "variable"
            )

        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=aws_secret_access_key
                or os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=aws_region,
            )
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise

    def upload_gpx_segment(
        self,
        local_file_path: Path,
        file_id: str,
        prefix: str = "gpx-segments",
    ) -> str:
        """Upload a GPX segment file to S3.

        Parameters
        ----------
        local_file_path : Path
            Path to the local GPX file to upload.
        file_id : str
            Unique identifier for the file.
        prefix : str
            S3 prefix to organize files. Defaults to "gpx-segments".

        Returns
        -------
        str
            S3 key (path) where the file was uploaded.

        Raises
        ------
        ClientError
            If the upload fails.
        FileNotFoundError
            If the local file doesn't exist.
        """
        if not local_file_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_file_path}")

        s3_key = f"{prefix}/{file_id}.gpx"

        try:
            logger.info(
                f"Uploading {local_file_path} to s3://{self.bucket_name}/{s3_key}"
            )

            self.s3_client.upload_file(
                str(local_file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    "ContentType": "application/gpx+xml",
                    "Metadata": {
                        "file-id": file_id,
                        "file-type": "gpx-segment",
                    },
                },
            )

            logger.info(
                f"Successfully uploaded GPX segment to s3://{self.bucket_name}/{s3_key}"
            )
            return s3_key

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Failed to upload to S3: {error_code} - {error_message}")
            raise

    def delete_gpx_segment(self, s3_key: str) -> bool:
        """Delete a GPX segment file from S3.

        Parameters
        ----------
        s3_key : str
            S3 key (path) of the file to delete.

        Returns
        -------
        bool
            True if deletion was successful, False otherwise.
        """
        try:
            logger.info(f"Deleting s3://{self.bucket_name}/{s3_key}")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Successfully deleted s3://{self.bucket_name}/{s3_key}")
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Failed to delete from S3: {error_code} - {error_message}")
            return False

    def get_gpx_segment_url(self, s3_key: str, expiration: int = 3600) -> str | None:
        """Generate a presigned URL for a GPX segment file.

        Parameters
        ----------
        s3_key : str
            S3 key (path) of the file.
        expiration : int
            URL expiration time in seconds. Defaults to 1 hour.

        Returns
        -------
        Optional[str]
            Presigned URL if successful, None otherwise.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )
            logger.info(f"Generated presigned URL for s3://{self.bucket_name}/{s3_key}")
            return url

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"Failed to generate presigned URL: {error_code} - {error_message}"
            )
            return None

    def bucket_exists(self) -> bool:
        """Check if the configured S3 bucket exists and is accessible.

        Returns
        -------
        bool
            True if bucket exists and is accessible, False otherwise.
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False


class LocalStorageManager:
    """Local filesystem storage manager that mimics S3 API."""

    def __init__(self, storage_root: str | None = None):
        """Initialize local storage manager.

        Parameters
        ----------
        storage_root : Optional[str]
            Root directory for local storage. If None, will use LOCAL_STORAGE_ROOT
            environment variable or default to "../scratch/local_storage".
        """
        self.storage_root = Path(
            storage_root or os.getenv("LOCAL_STORAGE_ROOT", "../scratch/local_storage")
        )
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.base_url = os.getenv(
            "LOCAL_STORAGE_BASE_URL", "http://localhost:8000/storage"
        )

        logger.info(f"Local storage manager initialized with root: {self.storage_root}")

    def upload_gpx_segment(
        self,
        local_file_path: Path,
        file_id: str,
        prefix: str = "gpx-segments",
    ) -> str:
        """Upload a GPX segment file to local storage.

        Parameters
        ----------
        local_file_path : Path
            Path to the local GPX file to upload.
        file_id : str
            Unique identifier for the file.
        prefix : str
            Storage prefix to organize files. Defaults to "gpx-segments".

        Returns
        -------
        str
            Storage key (path) where the file was stored.

        Raises
        ------
        FileNotFoundError
            If the local file doesn't exist.
        """
        if not local_file_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_file_path}")

        storage_key = f"{prefix}/{file_id}.gpx"
        target_path = self.storage_root / storage_key
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Uploading {local_file_path} to local storage: {target_path}")

            # Copy the file to local storage
            import shutil

            shutil.copy2(local_file_path, target_path)

            # Create metadata file
            metadata_path = target_path.with_suffix(".gpx.metadata")
            metadata_content = f"""file-id: {file_id}
file-type: gpx-segment
content-type: application/gpx+xml
original-path: {local_file_path}
"""
            metadata_path.write_text(metadata_content)

            logger.info(
                f"Successfully uploaded GPX segment to local storage: {target_path}"
            )
            return storage_key

        except Exception as e:
            logger.error(f"Failed to upload to local storage: {str(e)}")
            raise

    def delete_gpx_segment(self, storage_key: str) -> bool:
        """Delete a GPX segment file from local storage.

        Parameters
        ----------
        storage_key : str
            Storage key (path) of the file to delete.

        Returns
        -------
        bool
            True if deletion was successful, False otherwise.
        """
        try:
            target_path = self.storage_root / storage_key
            metadata_path = target_path.with_suffix(".gpx.metadata")

            logger.info(f"Deleting from local storage: {target_path}")

            # Delete the main file
            if target_path.exists():
                target_path.unlink()

            # Delete the metadata file
            if metadata_path.exists():
                metadata_path.unlink()

            logger.info(f"Successfully deleted from local storage: {target_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete from local storage: {str(e)}")
            return False

    def get_gpx_segment_url(
        self, storage_key: str, expiration: int = 3600
    ) -> str | None:
        """Generate a URL for accessing a GPX segment file.

        Parameters
        ----------
        storage_key : str
            Storage key (path) of the file.
        expiration : int
            URL expiration time in seconds (ignored for local storage).

        Returns
        -------
        str
            URL for accessing the file.
        """
        try:
            target_path = self.storage_root / storage_key
            if not target_path.exists():
                logger.warning(f"File not found in local storage: {target_path}")
                return None

            # Generate a URL that points to the local storage endpoint
            url = urljoin(self.base_url + "/", storage_key)
            logger.info(f"Generated local storage URL: {url}")
            return url

        except Exception as e:
            logger.error(f"Failed to generate local storage URL: {str(e)}")
            return None

    def bucket_exists(self) -> bool:
        """Check if the local storage directory exists and is accessible.

        Returns
        -------
        bool
            True if storage directory exists and is accessible, False otherwise.
        """
        try:
            return self.storage_root.exists() and self.storage_root.is_dir()
        except Exception:
            return False

    def get_file_path(self, storage_key: str) -> Path:
        """Get the local file path for a storage key.

        Parameters
        ----------
        storage_key : str
            Storage key (path) of the file.

        Returns
        -------
        Path
            Local file path.
        """
        return self.storage_root / storage_key

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in local storage with optional prefix.

        Parameters
        ----------
        prefix : str
            Prefix to filter files.

        Returns
        -------
        list[str]
            List of storage keys matching the prefix.
        """
        try:
            prefix_path = self.storage_root / prefix if prefix else self.storage_root
            if not prefix_path.exists():
                return []

            files = []
            for file_path in prefix_path.rglob("*.gpx"):
                relative_path = file_path.relative_to(self.storage_root)
                files.append(str(relative_path))

            return sorted(files)
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []


def get_storage_manager() -> StorageManager:
    """Get the appropriate storage manager based on environment configuration.

    Returns
    -------
    StorageManager
        Either S3Manager or LocalStorageManager based on configuration.

    Raises
    ------
    ValueError
        If storage configuration is invalid.
    """
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()

    if storage_type == "s3":
        return S3Manager()
    elif storage_type == "local":
        return LocalStorageManager()
    else:
        raise ValueError(
            f"Invalid STORAGE_TYPE: {storage_type}. Must be 's3' or 'local'"
        )


def cleanup_local_file(file_path: Path) -> bool:
    """Safely remove a local file.

    Parameters
    ----------
    file_path : Path
        Path to the file to remove.

    Returns
    -------
    bool
        True if file was removed successfully, False otherwise.
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Successfully removed local file: {file_path}")
            return True
        else:
            logger.warning(f"File does not exist, nothing to remove: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to remove local file {file_path}: {str(e)}")
        return False
