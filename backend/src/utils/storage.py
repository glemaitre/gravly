"""
Storage Module

This module provides a unified storage interface that can work with both AWS S3
and local filesystem storage, allowing seamless switching between production
and local development environments.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol
from urllib.parse import urljoin

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


class LocalStorageManager:
    """Local filesystem storage manager that mimics S3 API."""

    def __init__(self, storage_root: str | None = None):
        """Initialize local storage manager.

        Parameters
        ----------
        storage_root : Optional[str]
            Root directory for local storage. If None, will use LOCAL_STORAGE_ROOT
            environment variable or default to "./scratch/local_storage".
        """
        self.storage_root = Path(
            storage_root or os.getenv("LOCAL_STORAGE_ROOT", "./scratch/local_storage")
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
        from .s3 import S3Manager

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
