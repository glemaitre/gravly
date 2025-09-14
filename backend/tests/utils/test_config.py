"""Tests for the config module."""

import os
from unittest.mock import patch

import pytest

from backend.src.utils.config import (
    DatabaseConfig,
    LocalStorageConfig,
    S3StorageConfig,
    StorageConfig,
    load_environment_config,
)


def test_load_existing_env_file_with_full_config(tmp_path):
    """Test loading an existing environment file with database and storage configuration."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text(
        "TEST_VAR=test_value\n"
        "ANOTHER_VAR=another_value\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=cycling\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=test_password\n"
        "STORAGE_TYPE=local\n"
        "LOCAL_STORAGE_ROOT=./storage\n"
        "LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage"
    )

    os.environ["ENVIRONMENT"] = "local"
    db_config, storage_config = load_environment_config(project_root=tmp_path)

    assert os.getenv("TEST_VAR") == "test_value"
    assert os.getenv("ANOTHER_VAR") == "another_value"

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

    os.environ.pop("TEST_VAR", None)
    os.environ.pop("ANOTHER_VAR", None)
    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("DB_PASSWORD", None)
    os.environ.pop("STORAGE_TYPE", None)
    os.environ.pop("LOCAL_STORAGE_ROOT", None)
    os.environ.pop("LOCAL_STORAGE_BASE_URL", None)
    os.environ.pop("ENVIRONMENT", None)


def test_load_default_local_environment(tmp_path):
    """Test loading default local environment when ENVIRONMENT is not set."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text(
        "DEFAULT_VAR=default_value\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=cycling\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=default_password\n"
        "STORAGE_TYPE=local"
    )

    original_env = os.environ.pop("ENVIRONMENT", None)
    db_config, storage_config = load_environment_config(project_root=tmp_path)

    assert os.getenv("DEFAULT_VAR") == "default_value"
    assert db_config.host == "localhost"
    assert db_config.password == "default_password"
    assert storage_config.storage_type == "local"

    os.environ.pop("DEFAULT_VAR", None)
    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("DB_PASSWORD", None)
    os.environ.pop("STORAGE_TYPE", None)
    if original_env is not None:
        os.environ["ENVIRONMENT"] = original_env


def test_load_s3_environment(tmp_path):
    """Test loading S3 storage configuration."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    s3_env_file = env_folder / "s3"
    s3_env_file.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=cycling\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=password\n"
        "STORAGE_TYPE=s3\n"
        "AWS_S3_BUCKET=my-bucket\n"
        "AWS_ACCESS_KEY_ID=access-key\n"
        "AWS_SECRET_ACCESS_KEY=secret-key\n"
        "AWS_REGION=us-west-2"
    )

    os.environ["ENVIRONMENT"] = "s3"
    db_config, storage_config = load_environment_config(project_root=tmp_path)

    assert storage_config.storage_type == "s3"
    assert isinstance(storage_config, S3StorageConfig)
    assert storage_config.bucket == "my-bucket"
    assert storage_config.access_key_id == "access-key"
    assert storage_config.secret_access_key == "secret-key"
    assert storage_config.region == "us-west-2"

    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("DB_PASSWORD", None)
    os.environ.pop("STORAGE_TYPE", None)
    os.environ.pop("AWS_S3_BUCKET", None)
    os.environ.pop("AWS_ACCESS_KEY_ID", None)
    os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
    os.environ.pop("AWS_REGION", None)
    os.environ.pop("ENVIRONMENT", None)


def test_load_custom_environment(tmp_path):
    """Test loading a custom environment file."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    staging_env_file = env_folder / "staging"
    staging_env_file.write_text(
        "STAGING_VAR=staging_value\n"
        "DB_HOST=staging-db\n"
        "DB_PORT=5432\n"
        "DB_NAME=cycling_staging\n"
        "DB_USER=staging_user\n"
        "DB_PASSWORD=staging_password\n"
        "STORAGE_TYPE=local"
    )

    production_env_file = env_folder / "production"
    production_env_file.write_text("PROD_VAR=prod_value")

    os.environ["ENVIRONMENT"] = "staging"
    db_config, storage_config = load_environment_config(project_root=tmp_path)

    assert os.getenv("STAGING_VAR") == "staging_value"
    assert os.getenv("PROD_VAR") is None
    assert db_config.host == "staging-db"
    assert db_config.name == "cycling_staging"
    assert storage_config.storage_type == "local"

    os.environ.pop("STAGING_VAR", None)
    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("DB_PASSWORD", None)
    os.environ.pop("STORAGE_TYPE", None)
    os.environ.pop("ENVIRONMENT", None)


def test_missing_database_parameters(tmp_path):
    """Test error when database parameters are missing."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text(
        "DB_HOST=localhost\nDB_PORT=5432\nSTORAGE_TYPE=local\n"
        # Missing DB_NAME, DB_USER, DB_PASSWORD
    )

    os.environ["ENVIRONMENT"] = "local"

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required database configuration parameters" in error_message
    assert "DB_NAME" in error_message
    assert "DB_USER" in error_message
    assert "DB_PASSWORD" in error_message

    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)
    os.environ.pop("STORAGE_TYPE", None)
    os.environ.pop("ENVIRONMENT", None)


def test_missing_s3_parameters(tmp_path):
    """Test error when S3 parameters are missing."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    s3_env_file = env_folder / "s3"
    s3_env_file.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=cycling\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=password\n"
        "STORAGE_TYPE=s3\n"
        "AWS_S3_BUCKET=my-bucket\n"
        # Missing AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    )

    # Clear existing environment variables and set test ones
    with patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "s3",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "cycling",
            "DB_USER": "postgres",
            "DB_PASSWORD": "password",
            "STORAGE_TYPE": "s3",
            "AWS_S3_BUCKET": "my-bucket",
            # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are not set
        },
        clear=True,
    ):
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

    local_env_file = env_folder / "local"
    local_env_file.write_text(
        "DB_HOST=localhost\nDB_PORT=5432\nDB_NAME=cycling\nDB_USER=postgres\n"
        # Missing DB_PASSWORD
    )

    os.environ["ENVIRONMENT"] = "local"

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required database configuration parameters" in error_message
    assert "DB_PASSWORD" in error_message

    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("ENVIRONMENT", None)


def test_empty_database_parameters(tmp_path):
    """Test error when database parameters are empty strings."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text(
        "DB_HOST=\n"  # Empty string
        "DB_PORT=5432\n"
        "DB_NAME=cycling\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=password"
    )

    os.environ["ENVIRONMENT"] = "local"

    with pytest.raises(ValueError) as exc_info:
        load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "Missing required database configuration parameters" in error_message
    assert "DB_HOST" in error_message

    os.environ.pop("DB_PORT", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("DB_PASSWORD", None)
    os.environ.pop("ENVIRONMENT", None)


def test_error_when_env_file_not_found_with_examples(tmp_path):
    """Test error when environment file not found but examples exist."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    (env_folder / ".env.example").write_text("# Example file")
    (env_folder / ".env.local.example").write_text("# Local example")
    (env_folder / ".env.production.example").write_text("# Production example")

    with patch.dict(os.environ, {"ENVIRONMENT": "nonexistent"}):
        with pytest.raises(FileNotFoundError) as exc_info:
            load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "No environment file found for environment 'nonexistent'" in error_message
    assert "Example files available:" in error_message
    assert ".env.example" in error_message
    assert ".env.local.example" in error_message
    assert ".env.production.example" in error_message
    assert "Copy one of the example files" in error_message


def test_error_when_env_file_not_found_no_examples(tmp_path):
    """Test error when environment file not found and no examples exist."""
    with patch.dict(os.environ, {"ENVIRONMENT": "nonexistent"}):
        with pytest.raises(FileNotFoundError) as exc_info:
            load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "No environment file found for environment 'nonexistent'" in error_message
    assert "and no .env folder with examples found" in error_message


def test_error_when_env_folder_is_file(tmp_path):
    """Test error when .env exists but is a file instead of folder."""
    env_file = tmp_path / ".env"
    env_file.write_text("SOME_CONTENT")

    with patch.dict(os.environ, {"ENVIRONMENT": "local"}):
        with pytest.raises(FileNotFoundError) as exc_info:
            load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "and no .env folder with examples found" in error_message


def test_error_when_env_folder_empty(tmp_path):
    """Test error when .env folder exists but is empty."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    with patch.dict(os.environ, {"ENVIRONMENT": "local"}):
        with pytest.raises(FileNotFoundError) as exc_info:
            load_environment_config(project_root=tmp_path)

    error_message = str(exc_info.value)
    assert "and no .env folder with examples found" in error_message


def test_logging_info_when_file_loaded(tmp_path, caplog):
    """Test that appropriate logging message is generated when file is loaded."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text(
        "TEST_VAR=test_value\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=cycling\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=password"
    )

    os.environ["ENVIRONMENT"] = "local"
    with caplog.at_level("INFO"):
        load_environment_config(project_root=tmp_path)

    assert f"Loaded environment variables from {local_env_file}" in caplog.text

    os.environ.pop("TEST_VAR", None)
    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("DB_PASSWORD", None)
    os.environ.pop("ENVIRONMENT", None)


def test_project_root_parameter(tmp_path):
    """Test that custom project_root parameter works correctly."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    env_folder = subdir / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text(
        "CUSTOM_VAR=custom_value\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=cycling\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=password\n"
        "STORAGE_TYPE=local"
    )

    os.environ["ENVIRONMENT"] = "local"
    db_config, storage_config = load_environment_config(project_root=subdir)

    assert os.getenv("CUSTOM_VAR") == "custom_value"
    assert db_config.host == "localhost"

    os.environ.pop("CUSTOM_VAR", None)
    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("DB_PASSWORD", None)
    os.environ.pop("STORAGE_TYPE", None)
    os.environ.pop("ENVIRONMENT", None)


def test_default_project_root_behavior():
    """Test that default project_root works when not specified."""
    # This test verifies the function doesn't crash with default behavior
    # We can't easily test the actual loading without mocking the file system
    # but we can test that it raises appropriate errors
    with patch.dict(os.environ, {"ENVIRONMENT": "nonexistent"}):
        with pytest.raises(FileNotFoundError):
            load_environment_config()
