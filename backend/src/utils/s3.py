"""
S3 Storage Module

This module provides functionality to manage GPX files in AWS S3, including
uploading files with appropriate prefixes and cleaning up temporary files.
"""

import logging
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


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
            AWS secret access key. If None, will use AWS_SECRET_ACCESS_KEY environment variable.
        aws_region : str
            AWS region name. Defaults to "us-east-1".
        """
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET")
        self.aws_region = aws_region

        if not self.bucket_name:
            raise ValueError(
                "S3 bucket name must be provided or set in AWS_S3_BUCKET environment variable"
            )

        try:
            # Initialize S3 client
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

        # Construct S3 key with prefix
        s3_key = f"{prefix}/{file_id}.gpx"

        try:
            logger.info(
                f"Uploading {local_file_path} to s3://{self.bucket_name}/{s3_key}"
            )

            # Upload file to S3
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
