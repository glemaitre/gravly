"""Configuration management utilities for loading environment variables."""

import logging
import os
from pathlib import Path
from typing import NamedTuple

from dotenv import load_dotenv

# Configure detailed logging for configuration loading
logger = logging.getLogger(__name__)
# Don't override the global logging level - use INFO level
logger.setLevel(logging.INFO)


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


class StravaConfig(NamedTuple):
    """Strava API configuration parameters."""

    client_id: str
    client_secret: str
    tokens_file_path: str


class WahooConfig(NamedTuple):
    """Wahoo API configuration parameters."""

    client_id: str
    client_secret: str
    tokens_file_path: str
    callback_url: str
    scopes: list[str]


class MapConfig(NamedTuple):
    """Map service configuration parameters."""

    thunderforest_api_key: str


class ServerConfig(NamedTuple):
    """Server configuration parameters."""

    backend_host: str
    backend_port: int
    frontend_port: int
    frontend_url: str
    backend_url: str


# Union type for storage configurations
StorageConfig = S3StorageConfig | LocalStorageConfig


def load_environment_config(
    project_root: Path | None = None,
) -> tuple[
    DatabaseConfig, StorageConfig, StravaConfig, WahooConfig, MapConfig, ServerConfig
]:
    """Load environment variables from separate configuration files.

    This function loads environment variables from .env/storage, .env/database,
    .env/strava, .env/wahoo, and .env/server files in the .env folder and provides
    helpful error messages if no configuration is found.

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

    logger.debug(f"Loading configuration from project root: {project_root}")
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

    # Load Strava configuration
    strava_file = env_folder / "strava"
    if strava_file.exists():
        load_dotenv(strava_file, override=True)
        logger.info(f"Loaded Strava environment variables from {strava_file}")
    else:
        # Check if example file exists
        strava_example = env_folder / "strava.example"
        if strava_example.exists():
            raise FileNotFoundError(
                f"Strava configuration file not found at {strava_file}. "
                f"Please create a Strava configuration file based on "
                f"{strava_example}. Copy the example file and rename it to 'strava'."
            )
        else:
            raise FileNotFoundError(
                f"Strava configuration file not found at {strava_file} "
                f"and no example file available."
            )

    # Load map configuration
    map_file = env_folder / "thunderforest"
    if map_file.exists():
        load_dotenv(map_file, override=True)
        logger.info(f"Loaded map environment variables from {map_file}")
    else:
        # Check if example file exists
        map_example = env_folder / "thunderforest.example"
        if map_example.exists():
            raise FileNotFoundError(
                f"Map configuration file not found at {map_file}. "
                f"Please create a map configuration file based on "
                f"{map_example}. Copy the example file and rename it to "
                f"'thunderforest'."
            )
        else:
            raise FileNotFoundError(
                f"Map configuration file not found at {map_file} "
                f"and no example file available."
            )

    # Load server configuration (optional - has sensible defaults)
    server_file = env_folder / "server"
    if server_file.exists():
        load_dotenv(server_file, override=True)
        logger.info(f"Loaded server environment variables from {server_file}")
    else:
        logger.info(
            f"Server configuration file not found at {server_file}. "
            f"Using default values (backend: 0.0.0.0:8000, frontend: localhost:3000)."
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

    # Extract Strava configuration from environment variables
    required_strava_params = [
        "STRAVA_CLIENT_ID",
        "STRAVA_CLIENT_SECRET",
        "STRAVA_TOKENS_FILE_PATH",
    ]
    missing_strava_params = [
        param for param in required_strava_params if not os.getenv(param)
    ]

    if missing_strava_params:
        raise ValueError(
            f"Missing required Strava configuration parameters: "
            f"{', '.join(missing_strava_params)}. "
            f"Please set these environment variables in your .env/strava file. "
            f"STRAVA_TOKENS_FILE_PATH must be set to a secure location for "
            f"storing tokens."
        )

    tokens_file_path = os.getenv("STRAVA_TOKENS_FILE_PATH")

    strava_config = StravaConfig(
        client_id=os.getenv("STRAVA_CLIENT_ID"),
        client_secret=os.getenv("STRAVA_CLIENT_SECRET"),
        tokens_file_path=tokens_file_path,
    )

    # Load Wahoo configuration
    wahoo_file = env_folder / "wahoo"
    if wahoo_file.exists():
        load_dotenv(wahoo_file, override=True)
        logger.info(f"Loaded Wahoo environment variables from {wahoo_file}")
    else:
        # Check if example file exists
        wahoo_example = env_folder / "wahoo.example"
        if wahoo_example.exists():
            raise FileNotFoundError(
                f"Wahoo configuration file not found at {wahoo_file}. "
                f"Please create a Wahoo configuration file based on "
                f"{wahoo_example}. Copy the example file and rename it to 'wahoo'."
            )
        else:
            raise FileNotFoundError(
                f"Wahoo configuration file not found at {wahoo_file} "
                f"and no example file available."
            )

    # Extract Wahoo configuration from environment variables
    required_wahoo_params = [
        "WAHOO_CLIENT_ID",
        "WAHOO_CLIENT_SECRET",
        "WAHOO_TOKENS_FILE_PATH",
        "WAHOO_CALLBACK_URL",
        "WAHOO_SCOPES",
    ]
    missing_wahoo_params = [
        param for param in required_wahoo_params if not os.getenv(param)
    ]

    if missing_wahoo_params:
        raise ValueError(
            f"Missing required Wahoo configuration parameters: "
            f"{', '.join(missing_wahoo_params)}. "
            f"Please set these environment variables in your .env/wahoo file. "
            f"WAHOO_TOKENS_FILE_PATH must be set to a secure location for "
            f"storing tokens."
        )

    wahoo_tokens_file_path = os.getenv("WAHOO_TOKENS_FILE_PATH")

    wahoo_config = WahooConfig(
        client_id=os.getenv("WAHOO_CLIENT_ID"),
        client_secret=os.getenv("WAHOO_CLIENT_SECRET"),
        tokens_file_path=wahoo_tokens_file_path,
        callback_url=os.getenv("WAHOO_CALLBACK_URL"),
        scopes=os.getenv("WAHOO_SCOPES", "user_read routes_write").split(" "),
    )

    # Extract map configuration from environment variables
    thunderforest_api_key = os.getenv("THUNDERFOREST_API_KEY")
    if not thunderforest_api_key:
        raise ValueError(
            "Missing required map configuration parameter: THUNDERFOREST_API_KEY. "
            "Please set this environment variable in your .env/thunderforest file."
        )

    map_config = MapConfig(thunderforest_api_key=thunderforest_api_key)

    # Extract server configuration from environment variables with defaults
    backend_host = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port = int(os.getenv("FRONTEND_PORT", "3000"))
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    server_config = ServerConfig(
        backend_host=backend_host,
        backend_port=backend_port,
        frontend_port=frontend_port,
        frontend_url=frontend_url,
        backend_url=backend_url,
    )

    return (
        database_config,
        storage_config,
        strava_config,
        wahoo_config,
        map_config,
        server_config,
    )


# Global configuration instances
_configs = None


def _get_configs():
    """Get or load configuration instances."""
    global _configs
    if _configs is None:
        _configs = load_environment_config()
    return _configs


def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return _get_configs()[0]


def get_storage_config() -> StorageConfig:
    """Get storage configuration."""
    return _get_configs()[1]


def get_strava_config() -> StravaConfig:
    """Get Strava configuration."""
    return _get_configs()[2]


def get_wahoo_config() -> WahooConfig:
    """Get Wahoo configuration."""
    return _get_configs()[3]


def get_map_config() -> MapConfig:
    """Get map configuration."""
    return _get_configs()[4]


def get_server_config() -> ServerConfig:
    """Get server configuration."""
    return _get_configs()[5]
