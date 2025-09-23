"""Tests for the config module."""

import os

import pytest

from backend.src.utils.config import (
    DatabaseConfig,
    LocalStorageConfig,
    MapConfig,
    S3StorageConfig,
    StravaConfig,
    load_environment_config,
)


def test_load_storage_and_database_files_with_full_config(tmp_path):
    """Test loading separate storage and database files with full config."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=test_password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    db_config, storage_config, strava_config, map_config = load_environment_config(
        project_root=tmp_path
    )

    # Check configuration structure
    assert isinstance(db_config, DatabaseConfig)
    assert isinstance(storage_config, LocalStorageConfig)
    assert isinstance(strava_config, StravaConfig)
    assert isinstance(map_config, MapConfig)

    # Check database configuration
    assert db_config.host == "localhost"
    assert db_config.port == "5432"
    assert db_config.name == "cycling"
    assert db_config.user == "postgres"
    assert db_config.password == "test_password"

    # Check storage configuration
    assert storage_config.storage_type == "local"
    assert storage_config.storage_root == "./storage"
    assert storage_config.base_url == "http://localhost:8000/storage"

    # Check Strava configuration
    assert strava_config.client_id == "test_client_id"
    assert strava_config.client_secret == "test_client_secret"
    assert strava_config.tokens_file_path == "/secure/path/to/tokens.json"


def test_load_s3_storage_configuration(tmp_path):
    """Test loading S3 storage configuration."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file with S3 config
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=s3
AWS_S3_BUCKET=my-bucket
AWS_ACCESS_KEY_ID=access-key
AWS_SECRET_ACCESS_KEY=secret-key
AWS_REGION=us-west-2""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    db_config, storage_config, strava_config, map_config = load_environment_config(
        project_root=tmp_path
    )

    assert storage_config.storage_type == "s3"
    assert isinstance(storage_config, S3StorageConfig)
    assert storage_config.bucket == "my-bucket"
    assert storage_config.access_key_id == "access-key"
    assert storage_config.secret_access_key == "secret-key"
    assert storage_config.region == "us-west-2"


def test_missing_database_parameters(tmp_path):
    """Test error when database parameters are missing."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file with missing parameters
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required database configuration parameters" in error_message
    assert "DB_NAME" in error_message
    assert "DB_USER" in error_message
    assert "DB_PASSWORD" in error_message


def test_missing_s3_parameters(tmp_path):
    """Test error when S3 parameters are missing."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file with missing S3 parameters
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=s3
AWS_S3_BUCKET=my-bucket""")

    # Create database file with all required parameters
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    # Clear any existing environment variables that might interfere

    for key in list(os.environ.keys()):
        if key.startswith(("AWS_", "STORAGE_", "DB_")):
            del os.environ[key]

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required S3 configuration parameters" in error_message
    assert "AWS_ACCESS_KEY_ID" in error_message
    assert "AWS_SECRET_ACCESS_KEY" in error_message


def test_missing_single_database_parameter(tmp_path):
    """Test error when a single database parameter is missing."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file with missing password
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required database configuration parameters" in error_message
    assert "DB_PASSWORD" in error_message


def test_empty_database_parameters(tmp_path):
    """Test error when database parameters are empty strings."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file with empty host
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required database configuration parameters" in error_message
    assert "DB_HOST" in error_message


def test_error_when_storage_file_not_found_with_example(tmp_path):
    """Test error when storage file not found but example exists."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create example files
    storage_example = env_folder / "storage.example"
    storage_example.write_text("# Storage example")

    database_example = env_folder / "database.example"
    database_example.write_text("# Database example")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Storage configuration file not found" in error_message
    assert "storage.example" in error_message
    assert "Copy the example file and rename it to 'storage'" in error_message


def test_error_when_database_file_not_found_with_example(tmp_path):
    """Test error when database file not found but example exists."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database example
    database_example = env_folder / "database.example"
    database_example.write_text("# Database example")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Database configuration file not found" in error_message
    assert "database.example" in error_message
    assert "Copy the example file and rename it to 'database'" in error_message


def test_error_when_database_file_not_found_no_example(tmp_path):
    """Test error when database file not found and no example exists."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Don't create database.example file

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Database configuration file not found" in error_message
    assert "and no example file available" in error_message


def test_error_when_storage_file_not_found_no_example(tmp_path):
    """Test error when storage file not found and no example exists."""
    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Storage configuration file not found" in error_message
    assert "and no example file available" in error_message


def test_error_when_env_folder_is_file(tmp_path):
    """Test error when .env exists but is a file instead of folder."""
    env_file = tmp_path / ".env"
    env_file.write_text("SOME_CONTENT")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Storage configuration file not found" in error_message
    assert "and no example file available" in error_message


def test_error_when_env_folder_empty(tmp_path):
    """Test error when .env folder exists but is empty."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Storage configuration file not found" in error_message
    assert "and no example file available" in error_message


def test_logging_info_when_files_loaded(tmp_path, caplog):
    """Test that appropriate logging messages are generated when files are loaded."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    with caplog.at_level("INFO"):
        load_environment_config(project_root=tmp_path)

    assert f"Loaded storage environment variables from {storage_file}" in caplog.text
    assert f"Loaded database environment variables from {database_file}" in caplog.text
    assert f"Loaded Strava environment variables from {strava_file}" in caplog.text


def test_project_root_parameter(tmp_path):
    """Test that custom project_root parameter works correctly."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    env_folder = subdir / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    db_config, storage_config, strava_config, map_config = load_environment_config(
        project_root=subdir
    )

    assert db_config.host == "localhost"
    assert storage_config.storage_type == "local"


def test_default_project_root_behavior():
    """Test that default project_root works when not specified."""
    # This test verifies the function doesn't crash with default behavior
    # Since we have actual .env files in the project, this should succeed
    # rather than raise an error
    db_config, storage_config, strava_config, map_config = load_environment_config()

    # Verify we get valid configurations
    assert isinstance(db_config, DatabaseConfig)
    assert isinstance(storage_config, (LocalStorageConfig, S3StorageConfig))
    assert isinstance(strava_config, StravaConfig)
    assert isinstance(map_config, MapConfig)


def test_missing_strava_parameters(tmp_path):
    """Test error when Strava parameters are missing."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file with missing parameters
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required Strava configuration parameters" in error_message
    assert "STRAVA_CLIENT_SECRET" in error_message
    assert "STRAVA_TOKENS_FILE_PATH" in error_message


def test_missing_strava_file(tmp_path):
    """Test error when Strava file is missing."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Don't create strava file

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Strava configuration file not found" in error_message
    assert "and no example file available" in error_message


def test_custom_strava_tokens_file_path(tmp_path):
    """Test custom Strava tokens file path configuration."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file with custom tokens path
    custom_tokens_path = "/secure/path/to/tokens.json"
    strava_file = env_folder / "strava"
    strava_file.write_text(f"""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json
STRAVA_TOKENS_FILE_PATH={custom_tokens_path}""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    db_config, storage_config, strava_config, map_config = load_environment_config(
        project_root=tmp_path
    )

    # Check Strava configuration
    assert strava_config.client_id == "test_client_id"
    assert strava_config.client_secret == "test_client_secret"
    assert strava_config.tokens_file_path == custom_tokens_path


def test_missing_strava_tokens_file_path(tmp_path):
    """Test error when STRAVA_TOKENS_FILE_PATH is missing."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file without tokens file path
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret""")

    # Create thunderforest file
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required Strava configuration parameters" in error_message
    assert "STRAVA_TOKENS_FILE_PATH" in error_message
    assert "must be set to a secure location" in error_message


def test_strava_file_not_found_with_example(tmp_path):
    """Test error when Strava file is missing but example file exists."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create example file but NOT the actual strava file
    strava_example_file = env_folder / "strava.example"
    strava_example_file.write_text("""STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here
STRAVA_TOKENS_FILE_PATH=/secure/path/to/strava_tokens.json""")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Strava configuration file not found at" in error_message
    assert str(env_folder / "strava") in error_message
    assert "Please create a Strava configuration file based on" in error_message
    assert str(strava_example_file) in error_message
    assert "Copy the example file and rename it to 'strava'" in error_message


def test_strava_file_not_found_no_example(tmp_path):
    """Test error when neither Strava file nor example file exists."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Don't create any Strava files (neither strava nor strava.example)

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Strava configuration file not found at" in error_message
    assert str(env_folder / "strava") in error_message
    assert "and no example file available" in error_message


def test_strava_file_not_found_with_mock_path_exists(tmp_path, monkeypatch):
    """Test error handling using mock for Path.exists method."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create strava.example file
    strava_example_file = env_folder / "strava.example"
    strava_example_file.write_text("""STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here
STRAVA_TOKENS_FILE_PATH=/secure/path/to/strava_tokens.json""")

    # Mock Path.exists to simulate that strava file doesn't exist
    # but strava.example does exist
    def mock_exists(self):
        if str(self).endswith("/strava"):
            return False  # Main strava file doesn't exist
        elif str(self).endswith("/strava.example"):
            return True  # Example file exists
        else:
            # For all other files, use the real exists method
            return self._real_exists()

    # Store the original exists method
    from pathlib import Path

    Path._real_exists = Path.exists

    # Apply the mock
    monkeypatch.setattr(Path, "exists", mock_exists)

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Strava configuration file not found at" in error_message
    assert "Please create a Strava configuration file based on" in error_message
    assert "Copy the example file and rename it to 'strava'" in error_message


def test_thunderforest_file_not_found_with_example(tmp_path):
    """Test error when thunderforest file is missing but example file exists."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest.example file but NOT the thunderforest file
    thunderforest_example_file = env_folder / "thunderforest.example"
    thunderforest_example_file.write_text("""THUNDERFOREST_API_KEY=your_api_key_here""")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Map configuration file not found at" in error_message
    assert "Please create a map configuration file based on" in error_message
    assert "Copy the example file and rename it to 'thunderforest'" in error_message


def test_thunderforest_file_not_found_without_example(tmp_path):
    """Test error when thunderforest file is missing and no example file exists."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Do NOT create thunderforest file or thunderforest.example file

    with pytest.raises(FileNotFoundError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Map configuration file not found at" in error_message
    assert "and no example file available" in error_message


def test_missing_thunderforest_api_key(tmp_path):
    """Test error when thunderforest file exists but THUNDERFOREST_API_KEY is missing."""  # noqa: E501
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file without THUNDERFOREST_API_KEY
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""# THUNDERFOREST_API_KEY is missing""")

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert (
        "Missing required map configuration parameter: THUNDERFOREST_API_KEY"
        in error_message
    )
    assert (
        "Please set this environment variable in your .env/thunderforest file"
        in error_message
    )


def test_empty_thunderforest_api_key(tmp_path):
    """Test error when thunderforest file exists but THUNDERFOREST_API_KEY is empty."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    # Create storage file
    storage_file = env_folder / "storage"
    storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

    # Create database file
    database_file = env_folder / "database"
    database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

    # Create Strava file
    strava_file = env_folder / "strava"
    strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

    # Create thunderforest file with empty THUNDERFOREST_API_KEY
    thunderforest_file = env_folder / "thunderforest"
    thunderforest_file.write_text("""THUNDERFOREST_API_KEY=""")

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert (
        "Missing required map configuration parameter: THUNDERFOREST_API_KEY"
        in error_message
    )
    assert (
        "Please set this environment variable in your .env/thunderforest file"
        in error_message
    )
