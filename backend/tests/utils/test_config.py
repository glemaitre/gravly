"""Tests for the config module."""

import os
from unittest.mock import patch

import pytest
from src.utils.config import load_environment_config


def test_load_existing_env_file(tmp_path):
    """Test loading an existing environment file."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value")

    os.environ["ENVIRONMENT"] = "local"
    load_environment_config(project_root=tmp_path)

    assert os.getenv("TEST_VAR") == "test_value"
    assert os.getenv("ANOTHER_VAR") == "another_value"

    os.environ.pop("TEST_VAR", None)
    os.environ.pop("ANOTHER_VAR", None)
    os.environ.pop("ENVIRONMENT", None)


def test_load_default_local_environment(tmp_path):
    """Test loading default local environment when ENVIRONMENT is not set."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text("DEFAULT_VAR=default_value")

    original_env = os.environ.pop("ENVIRONMENT", None)
    load_environment_config(project_root=tmp_path)

    assert os.getenv("DEFAULT_VAR") == "default_value"

    os.environ.pop("DEFAULT_VAR", None)
    if original_env is not None:
        os.environ["ENVIRONMENT"] = original_env


def test_load_custom_environment(tmp_path):
    """Test loading a custom environment file."""
    env_folder = tmp_path / ".env"
    env_folder.mkdir()

    staging_env_file = env_folder / "staging"
    staging_env_file.write_text("STAGING_VAR=staging_value")

    production_env_file = env_folder / "production"
    production_env_file.write_text("PROD_VAR=prod_value")

    os.environ["ENVIRONMENT"] = "staging"
    load_environment_config(project_root=tmp_path)

    assert os.getenv("STAGING_VAR") == "staging_value"
    assert os.getenv("PROD_VAR") is None

    os.environ.pop("STAGING_VAR", None)
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
    local_env_file.write_text("TEST_VAR=test_value")

    os.environ["ENVIRONMENT"] = "local"
    with caplog.at_level("INFO"):
        load_environment_config(project_root=tmp_path)

    assert f"Loaded environment variables from {local_env_file}" in caplog.text

    os.environ.pop("TEST_VAR", None)
    os.environ.pop("ENVIRONMENT", None)


def test_project_root_parameter(tmp_path):
    """Test that custom project_root parameter works correctly."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    env_folder = subdir / ".env"
    env_folder.mkdir()

    local_env_file = env_folder / "local"
    local_env_file.write_text("CUSTOM_VAR=custom_value")

    os.environ["ENVIRONMENT"] = "local"
    load_environment_config(project_root=subdir)

    assert os.getenv("CUSTOM_VAR") == "custom_value"

    os.environ.pop("CUSTOM_VAR", None)
    os.environ.pop("ENVIRONMENT", None)


def test_default_project_root_behavior():
    """Test that default project_root works when not specified."""
    # This test verifies the function doesn't crash with default behavior
    # We can't easily test the actual loading without mocking the file system
    # but we can test that it raises appropriate errors
    with patch.dict(os.environ, {"ENVIRONMENT": "nonexistent"}):
        with pytest.raises(FileNotFoundError):
            load_environment_config()
