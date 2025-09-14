"""Tests for the config module."""

import os
from unittest.mock import patch

import pytest

from backend.src.utils.config import (
    DatabaseConfig,
    LocalStorageConfig,
    S3StorageConfig,
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

    db_config, storage_config = load_environment_config(project_root=tmp_path)

    # Check configuration structure
    assert isinstance(db_config, DatabaseConfig)
    assert isinstance(storage_config, LocalStorageConfig)

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

    db_config, storage_config = load_environment_config(project_root=tmp_path)

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

    # Clear any existing environment variables that might interfere
    import os

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

    with caplog.at_level("INFO"):
        load_environment_config(project_root=tmp_path)

    assert f"Loaded storage environment variables from {storage_file}" in caplog.text
    assert f"Loaded database environment variables from {database_file}" in caplog.text


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

    db_config, storage_config = load_environment_config(project_root=subdir)

    assert db_config.host == "localhost"
    assert storage_config.storage_type == "local"


def test_default_project_root_behavior():
    """Test that default project_root works when not specified."""
    # This test verifies the function doesn't crash with default behavior
    # Since we have actual .env files in the project, this should succeed
    # rather than raise an error
    db_config, storage_config = load_environment_config()

    # Verify we get valid configurations
    assert isinstance(db_config, DatabaseConfig)
    assert isinstance(storage_config, (LocalStorageConfig, S3StorageConfig))
