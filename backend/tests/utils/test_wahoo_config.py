"""Unit tests for Wahoo configuration."""

import os
from unittest.mock import patch

import pytest

from backend.src.utils.config import WahooConfig, load_environment_config


class TestWahooConfig:
    """Test WahooConfig class."""

    def test_wahoo_config_creation(self):
        """Test creating a WahooConfig instance."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"

    def test_wahoo_config_immutable(self):
        """Test that WahooConfig is immutable (NamedTuple)."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        # NamedTuple should be immutable
        with pytest.raises(AttributeError):
            config.client_id = "new_client_id"


class TestWahooConfigLoading:
    """Test Wahoo configuration loading from environment."""

    def test_load_wahoo_config_success(self, tmp_path):
        """Test successful loading of Wahoo configuration."""
        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create all required config files
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        wahoo_file = env_folder / "wahoo"
        wahoo_file.write_text("""WAHOO_CLIENT_ID=test_wahoo_client_id
WAHOO_CLIENT_SECRET=test_wahoo_client_secret
WAHOO_CALLBACK_URL=https://test.example.com/wahoo-callback
WAHOO_SCOPES=user_read,routes_write""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        # Load configuration
        (
            db_config,
            storage_config,
            strava_config,
            wahoo_config,
            map_config,
            server_config,
        ) = load_environment_config(project_root=tmp_path)

        # Verify Wahoo configuration
        assert isinstance(wahoo_config, WahooConfig)
        assert wahoo_config.client_id == "test_wahoo_client_id"
        assert wahoo_config.client_secret == "test_wahoo_client_secret"
        assert wahoo_config.callback_url == "https://test.example.com/wahoo-callback"

    def test_load_wahoo_config_missing_file(self, tmp_path):
        """Test error when Wahoo configuration file is missing."""
        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create other required files but not wahoo
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        with pytest.raises(
            FileNotFoundError, match="Wahoo configuration file not found"
        ):
            load_environment_config(project_root=tmp_path)

    def test_load_wahoo_config_missing_parameters(self, tmp_path):
        """Test error when Wahoo configuration parameters are missing."""
        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create all required files
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        # Create wahoo file with missing parameters
        wahoo_file = env_folder / "wahoo"
        wahoo_file.write_text("""WAHOO_CLIENT_ID=test_wahoo_client_id
WAHOO_CLIENT_SECRET=
WAHOO_TOKENS_FILE_PATH=""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        with pytest.raises(
            ValueError, match="Missing required Wahoo configuration parameters"
        ):
            load_environment_config(project_root=tmp_path)

    def test_load_wahoo_config_missing_client_id(self, tmp_path):
        """Test error when WAHOO_CLIENT_ID is missing."""
        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create all required files
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        # Create wahoo file without client_id
        wahoo_file = env_folder / "wahoo"
        wahoo_file.write_text("""WAHOO_CLIENT_ID=
WAHOO_CLIENT_SECRET=test_wahoo_client_secret
WAHOO_TOKENS_FILE_PATH=/secure/path/to/wahoo_tokens.json""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        with pytest.raises(ValueError, match="WAHOO_CLIENT_ID"):
            load_environment_config(project_root=tmp_path)

    def test_load_wahoo_config_missing_client_secret(self, tmp_path):
        """Test error when WAHOO_CLIENT_SECRET is missing."""
        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create all required files
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        # Create wahoo file without client_secret
        wahoo_file = env_folder / "wahoo"
        wahoo_file.write_text("""WAHOO_CLIENT_ID=test_wahoo_client_id
WAHOO_CLIENT_SECRET=
WAHOO_TOKENS_FILE_PATH=/secure/path/to/wahoo_tokens.json""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        with pytest.raises(ValueError, match="WAHOO_CLIENT_SECRET"):
            load_environment_config(project_root=tmp_path)

    def test_load_wahoo_config_missing_scopes(self, tmp_path):
        """Test error when WAHOO_SCOPES is missing."""
        import os

        # Clear any existing WAHOO_SCOPES environment variable to avoid interference
        if "WAHOO_SCOPES" in os.environ:
            del os.environ["WAHOO_SCOPES"]

        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create all required files
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        # Create wahoo file without scopes
        wahoo_file = env_folder / "wahoo"
        wahoo_file.write_text("""WAHOO_CLIENT_ID=test_wahoo_client_id
WAHOO_CLIENT_SECRET=test_wahoo_client_secret
WAHOO_CALLBACK_URL=https://test.example.com/wahoo-callback""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        with pytest.raises(ValueError, match="WAHOO_SCOPES"):
            load_environment_config(project_root=tmp_path)

    def test_load_wahoo_config_with_example_file(self, tmp_path):
        """Test error message when wahoo.example exists but wahoo doesn't."""
        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create all required files
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        # Create wahoo.example file
        wahoo_example_file = env_folder / "wahoo.example"
        wahoo_example_file.write_text("""WAHOO_CLIENT_ID=your_client_id
WAHOO_CLIENT_SECRET=your_client_secret
WAHOO_TOKENS_FILE_PATH=/path/to/tokens.json""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        with pytest.raises(
            FileNotFoundError,
            match="Please create a Wahoo configuration file based on",
        ):
            load_environment_config(project_root=tmp_path)

    def test_load_wahoo_config_empty_values(self, tmp_path):
        """Test error when Wahoo configuration has empty values."""
        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create all required files
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        # Create wahoo file with empty values
        wahoo_file = env_folder / "wahoo"
        wahoo_file.write_text("""WAHOO_CLIENT_ID=
WAHOO_CLIENT_SECRET=test_wahoo_client_secret
WAHOO_TOKENS_FILE_PATH=/secure/path/to/wahoo_tokens.json""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        with pytest.raises(ValueError, match="WAHOO_CLIENT_ID"):
            load_environment_config(project_root=tmp_path)


class TestWahooConfigEnvironmentVariables:
    """Test Wahoo configuration with environment variables."""

    def test_wahoo_config_file_override_env(self, tmp_path):
        """Test that file values override environment variables."""
        env_folder = tmp_path / ".env"
        env_folder.mkdir()

        # Create all required files
        storage_file = env_folder / "storage"
        storage_file.write_text("""STORAGE_TYPE=local
LOCAL_STORAGE_ROOT=./storage
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage""")

        database_file = env_folder / "database"
        database_file.write_text("""DB_HOST=localhost
DB_PORT=5432
DB_NAME=cycling
DB_USER=postgres
DB_PASSWORD=password""")

        strava_file = env_folder / "strava"
        strava_file.write_text("""STRAVA_CLIENT_ID=test_client_id
STRAVA_CLIENT_SECRET=test_client_secret
STRAVA_TOKENS_FILE_PATH=/secure/path/to/tokens.json""")

        # Create wahoo file
        wahoo_file = env_folder / "wahoo"
        wahoo_file.write_text("""WAHOO_CLIENT_ID=file_client_id
WAHOO_CLIENT_SECRET=file_client_secret
WAHOO_CALLBACK_URL=https://test.example.com/wahoo-callback
WAHOO_SCOPES=user_read,routes_write""")

        thunderforest_file = env_folder / "thunderforest"
        thunderforest_file.write_text("""THUNDERFOREST_API_KEY=test_api_key""")

        # Set environment variables (should be overridden by file values)
        with patch.dict(
            os.environ,
            {
                "WAHOO_CLIENT_ID": "env_client_id",
                "WAHOO_CLIENT_SECRET": "env_client_secret",
                "WAHOO_CALLBACK_URL": "https://env.example.com/wahoo-callback",
                "WAHOO_SCOPES": "user_read",
            },
        ):
            (
                db_config,
                storage_config,
                strava_config,
                wahoo_config,
                map_config,
                server_config,
            ) = load_environment_config(project_root=tmp_path)

            # File values should override environment variables
            assert wahoo_config.client_id == "file_client_id"
            assert wahoo_config.client_secret == "file_client_secret"
