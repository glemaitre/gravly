"""Configuration management utilities for loading environment variables."""

import logging
import os
from pathlib import Path
from typing import NamedTuple

from dotenv import load_dotenv


class DatabaseConfig(NamedTuple):
    """Database configuration parameters."""

    host: str
    port: str
    name: str
    user: str
    password: str


class S3StorageConfig(NamedTuple):
    """S3 storage configuration parameters."""

    storage_type: str  # Always "s3"
    bucket: str
    access_key_id: str
    secret_access_key: str
    region: str


class LocalStorageConfig(NamedTuple):
    """Local storage configuration parameters."""

    storage_type: str  # Always "local"
    storage_root: str
    base_url: str


# Union type for storage configurations
StorageConfig = S3StorageConfig | LocalStorageConfig


def load_environment_config(
    project_root: Path | None = None,
) -> tuple[DatabaseConfig, StorageConfig]:
    """Load environment variables from separate storage and database .env files.

    This function loads environment variables from .env/storage and .env/database files
    in the .env folder and provides helpful error messages if no configuration is found.

    Parameters
    ----------
    project_root : Path, optional
        Path to the project root directory. If None, will be automatically
        determined from the current file location.

    Raises
    ------
    FileNotFoundError
        If required environment files are not found.
    """
    if project_root is None:
        # Default to the project root (4 levels up from this file:
        # config.py -> utils -> src -> backend -> project_root)
        project_root = Path(__file__).parent.parent.parent.parent

    env_folder = project_root / ".env"

    # Load storage configuration
    storage_file = env_folder / "storage"
    if storage_file.exists():
        load_dotenv(storage_file, override=True)
        logging.info(f"Loaded storage environment variables from {storage_file}")
    else:
        # Check if example file exists
        storage_example = env_folder / "storage.example"
        if storage_example.exists():
            raise FileNotFoundError(
                f"Storage configuration file not found at {storage_file}. "
                f"Please create a storage configuration file based on "
                f"{storage_example}. Copy the example file and rename it to 'storage'."
            )
        else:
            raise FileNotFoundError(
                f"Storage configuration file not found at {storage_file} "
                f"and no example file available."
            )

    # Load database configuration
    database_file = env_folder / "database"
    if database_file.exists():
        load_dotenv(database_file, override=True)
        logging.info(f"Loaded database environment variables from {database_file}")
    else:
        # Check if example file exists
        database_example = env_folder / "database.example"
        if database_example.exists():
            raise FileNotFoundError(
                f"Database configuration file not found at {database_file}. "
                f"Please create a database configuration file based on "
                f"{database_example}. Copy the example file and rename it to "
                f"'database'."
            )
        else:
            raise FileNotFoundError(
                f"Database configuration file not found at {database_file} "
                f"and no example file available."
            )

    # Extract database configuration from environment variables
    # All database parameters are required - no defaults
    required_db_params = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_db_params = [param for param in required_db_params if not os.getenv(param)]

    if missing_db_params:
        raise ValueError(
            f"Missing required database configuration parameters: "
            f"{', '.join(missing_db_params)}. "
            f"Please set these environment variables in your .env file."
        )

    # Extract storage configuration from environment variables
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()

    if storage_type == "s3":
        # For S3, validate required parameters
        required_s3_params = [
            "AWS_S3_BUCKET",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]
        missing_s3_params = [
            param for param in required_s3_params if not os.getenv(param)
        ]

        if missing_s3_params:
            raise ValueError(
                f"Missing required S3 configuration parameters: "
                f"{', '.join(missing_s3_params)}. "
                f"Please set these environment variables in your .env file."
            )

    database_config = DatabaseConfig(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        name=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    # Create storage configuration based on type
    if storage_type == "s3":
        storage_config = S3StorageConfig(
            storage_type="s3",
            bucket=os.getenv("AWS_S3_BUCKET"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region=os.getenv("AWS_REGION", "us-east-1"),
        )
    else:  # local storage
        storage_config = LocalStorageConfig(
            storage_type="local",
            storage_root=os.getenv("LOCAL_STORAGE_ROOT"),
            base_url=os.getenv("LOCAL_STORAGE_BASE_URL"),
        )

    return database_config, storage_config
