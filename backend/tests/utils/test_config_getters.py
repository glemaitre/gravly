"""Tests for the config getter functions to cover missing lines."""

from unittest.mock import patch

from backend.src.utils.config import (
    DatabaseConfig,
    LocalStorageConfig,
    MapConfig,
    ServerConfig,
    StravaConfig,
    WahooConfig,
    get_database_config,
    get_map_config,
    get_server_config,
    get_storage_config,
    get_strava_config,
    get_wahoo_config,
)


def test_get_database_config():
    """Test get_database_config() function."""
    # Mock the _get_configs function to return test configurations
    mock_configs = (
        DatabaseConfig(
            host="localhost",
            port="5432",
            name="cycling",
            user="postgres",
            password="password",
        ),
        LocalStorageConfig(
            storage_type="local",
            storage_root="./storage",
            base_url="http://localhost:8000/storage",
        ),
        StravaConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/secure/path/to/tokens.json",
        ),
        WahooConfig(
            client_id="test_wahoo_client_id",
            client_secret="test_wahoo_client_secret",
            tokens_file_path="/secure/path/to/wahoo_tokens.json",
            callback_url="http://localhost:8000/callback",
        ),
        MapConfig(thunderforest_api_key="test_api_key"),
        ServerConfig(
            backend_host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
        ),
    )

    with patch("backend.src.utils.config._get_configs", return_value=mock_configs):
        db_config = get_database_config()

        assert isinstance(db_config, DatabaseConfig)
        assert db_config.host == "localhost"
        assert db_config.port == "5432"
        assert db_config.name == "cycling"
        assert db_config.user == "postgres"
        assert db_config.password == "password"


def test_get_storage_config():
    """Test get_storage_config() function."""
    # Mock the _get_configs function to return test configurations
    mock_configs = (
        DatabaseConfig(
            host="localhost",
            port="5432",
            name="cycling",
            user="postgres",
            password="password",
        ),
        LocalStorageConfig(
            storage_type="local",
            storage_root="./storage",
            base_url="http://localhost:8000/storage",
        ),
        StravaConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/secure/path/to/tokens.json",
        ),
        WahooConfig(
            client_id="test_wahoo_client_id",
            client_secret="test_wahoo_client_secret",
            tokens_file_path="/secure/path/to/wahoo_tokens.json",
            callback_url="http://localhost:8000/callback",
        ),
        MapConfig(thunderforest_api_key="test_api_key"),
        ServerConfig(
            backend_host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
        ),
    )

    with patch("backend.src.utils.config._get_configs", return_value=mock_configs):
        storage_config = get_storage_config()

        assert isinstance(storage_config, LocalStorageConfig)
        assert storage_config.storage_type == "local"
        assert storage_config.storage_root == "./storage"
        assert storage_config.base_url == "http://localhost:8000/storage"


def test_get_strava_config():
    """Test get_strava_config() function."""
    # Mock the _get_configs function to return test configurations
    mock_configs = (
        DatabaseConfig(
            host="localhost",
            port="5432",
            name="cycling",
            user="postgres",
            password="password",
        ),
        LocalStorageConfig(
            storage_type="local",
            storage_root="./storage",
            base_url="http://localhost:8000/storage",
        ),
        StravaConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/secure/path/to/tokens.json",
        ),
        WahooConfig(
            client_id="test_wahoo_client_id",
            client_secret="test_wahoo_client_secret",
            tokens_file_path="/secure/path/to/wahoo_tokens.json",
            callback_url="http://localhost:8000/callback",
        ),
        MapConfig(thunderforest_api_key="test_api_key"),
        ServerConfig(
            backend_host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
        ),
    )

    with patch("backend.src.utils.config._get_configs", return_value=mock_configs):
        strava_config = get_strava_config()

        assert isinstance(strava_config, StravaConfig)
        assert strava_config.client_id == "test_client_id"
        assert strava_config.client_secret == "test_client_secret"
        assert strava_config.tokens_file_path == "/secure/path/to/tokens.json"


def test_get_wahoo_config():
    """Test get_wahoo_config() function."""
    # Mock the _get_configs function to return test configurations
    mock_configs = (
        DatabaseConfig(
            host="localhost",
            port="5432",
            name="cycling",
            user="postgres",
            password="password",
        ),
        LocalStorageConfig(
            storage_type="local",
            storage_root="./storage",
            base_url="http://localhost:8000/storage",
        ),
        StravaConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/secure/path/to/tokens.json",
        ),
        WahooConfig(
            client_id="test_wahoo_client_id",
            client_secret="test_wahoo_client_secret",
            tokens_file_path="/secure/path/to/wahoo_tokens.json",
            callback_url="http://localhost:8000/callback",
        ),
        MapConfig(thunderforest_api_key="test_api_key"),
        ServerConfig(
            backend_host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
        ),
    )

    with patch("backend.src.utils.config._get_configs", return_value=mock_configs):
        wahoo_config = get_wahoo_config()

        assert isinstance(wahoo_config, WahooConfig)
        assert wahoo_config.client_id == "test_wahoo_client_id"
        assert wahoo_config.client_secret == "test_wahoo_client_secret"
        assert wahoo_config.tokens_file_path == "/secure/path/to/wahoo_tokens.json"
        assert wahoo_config.callback_url == "http://localhost:8000/callback"


def test_get_map_config():
    """Test get_map_config() function."""
    # Mock the _get_configs function to return test configurations
    mock_configs = (
        DatabaseConfig(
            host="localhost",
            port="5432",
            name="cycling",
            user="postgres",
            password="password",
        ),
        LocalStorageConfig(
            storage_type="local",
            storage_root="./storage",
            base_url="http://localhost:8000/storage",
        ),
        StravaConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/secure/path/to/tokens.json",
        ),
        WahooConfig(
            client_id="test_wahoo_client_id",
            client_secret="test_wahoo_client_secret",
            tokens_file_path="/secure/path/to/wahoo_tokens.json",
            callback_url="http://localhost:8000/callback",
        ),
        MapConfig(thunderforest_api_key="test_api_key"),
        ServerConfig(
            backend_host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
        ),
    )

    with patch("backend.src.utils.config._get_configs", return_value=mock_configs):
        map_config = get_map_config()

        assert isinstance(map_config, MapConfig)
        assert map_config.thunderforest_api_key == "test_api_key"


def test_get_server_config():
    """Test get_server_config() function."""
    # Mock the _get_configs function to return test configurations
    mock_configs = (
        DatabaseConfig(
            host="localhost",
            port="5432",
            name="cycling",
            user="postgres",
            password="password",
        ),
        LocalStorageConfig(
            storage_type="local",
            storage_root="./storage",
            base_url="http://localhost:8000/storage",
        ),
        StravaConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/secure/path/to/tokens.json",
        ),
        WahooConfig(
            client_id="test_wahoo_client_id",
            client_secret="test_wahoo_client_secret",
            tokens_file_path="/secure/path/to/wahoo_tokens.json",
            callback_url="http://localhost:8000/callback",
        ),
        MapConfig(thunderforest_api_key="test_api_key"),
        ServerConfig(
            backend_host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
        ),
    )

    with patch("backend.src.utils.config._get_configs", return_value=mock_configs):
        server_config = get_server_config()

        assert isinstance(server_config, ServerConfig)
        assert server_config.backend_host == "0.0.0.0"
        assert server_config.backend_port == 8000
        assert server_config.frontend_port == 3000
        assert server_config.frontend_url == "http://localhost:3000"
        assert server_config.backend_url == "http://localhost:8000"


def test_get_configs_caching():
    """Test that _get_configs() caches the configuration and returns the same instance."""  # noqa: E501
    # Mock the _get_configs function to return test configurations
    mock_configs = (
        DatabaseConfig(
            host="localhost",
            port="5432",
            name="cycling",
            user="postgres",
            password="password",
        ),
        LocalStorageConfig(
            storage_type="local",
            storage_root="./storage",
            base_url="http://localhost:8000/storage",
        ),
        StravaConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/secure/path/to/tokens.json",
        ),
        WahooConfig(
            client_id="test_wahoo_client_id",
            client_secret="test_wahoo_client_secret",
            tokens_file_path="/secure/path/to/wahoo_tokens.json",
            callback_url="http://localhost:8000/callback",
        ),
        MapConfig(thunderforest_api_key="test_api_key"),
        ServerConfig(
            backend_host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
        ),
    )

    with patch("backend.src.utils.config._get_configs", return_value=mock_configs):
        # Test that multiple calls return the same configuration instances
        db_config1 = get_database_config()
        db_config2 = get_database_config()

        storage_config1 = get_storage_config()
        storage_config2 = get_storage_config()

        strava_config1 = get_strava_config()
        strava_config2 = get_strava_config()

        wahoo_config1 = get_wahoo_config()
        wahoo_config2 = get_wahoo_config()

        map_config1 = get_map_config()
        map_config2 = get_map_config()

        server_config1 = get_server_config()
        server_config2 = get_server_config()

        # Verify that the same instances are returned (caching works)
        assert db_config1 is db_config2
        assert storage_config1 is storage_config2
        assert strava_config1 is strava_config2
        assert wahoo_config1 is wahoo_config2
        assert map_config1 is map_config2
        assert server_config1 is server_config2


def test_get_configs_when_none():
    """Test _get_configs() function when _configs is None (lines 378-380)."""
    # Clear the global cache
    import backend.src.utils.config as config_module
    from backend.src.utils.config import _get_configs

    config_module._configs = None

    # Mock load_environment_config to return test configurations
    mock_configs = (
        DatabaseConfig(
            host="localhost",
            port="5432",
            name="cycling",
            user="postgres",
            password="password",
        ),
        LocalStorageConfig(
            storage_type="local",
            storage_root="./storage",
            base_url="http://localhost:8000/storage",
        ),
        StravaConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/secure/path/to/tokens.json",
        ),
        WahooConfig(
            client_id="test_wahoo_client_id",
            client_secret="test_wahoo_client_secret",
            tokens_file_path="/secure/path/to/wahoo_tokens.json",
            callback_url="http://localhost:8000/callback",
        ),
        MapConfig(thunderforest_api_key="test_api_key"),
        ServerConfig(
            backend_host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
        ),
    )

    with patch(
        "backend.src.utils.config.load_environment_config", return_value=mock_configs
    ):
        # This should trigger the _configs is None condition and load the config
        result = _get_configs()

        # Verify that the configuration was loaded and cached
        assert result == mock_configs
        assert config_module._configs == mock_configs

        # Verify that subsequent calls return the cached configuration
        result2 = _get_configs()
        assert result is result2  # Same instance (cached)
