"""Unit tests for the Wahoo service."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.src.services.wahoo.exceptions import WahooAccessUnauthorized
from backend.src.services.wahoo.service import WahooService
from backend.src.utils.config import WahooConfig


@pytest.fixture
def mock_wahoo_config(tmp_path):
    """Create a mock Wahoo configuration for testing."""
    tokens_file = tmp_path / "test_wahoo_tokens.json"
    return WahooConfig(
        client_id="test_wahoo_client_id",
        client_secret="test_wahoo_client_secret",
        tokens_file_path=str(tokens_file),
        callback_url="https://test.example.com/wahoo-callback",
        scopes=["user_read", "routes_write"],
    )


@pytest.fixture
def wahoo_service(mock_wahoo_config):
    """Create a WahooService instance for testing."""
    with patch("backend.src.services.wahoo.service.Client"):
        return WahooService(mock_wahoo_config)


class TestWahooServiceInitialization:
    """Test WahooService initialization."""

    def test_init_with_valid_config(self, mock_wahoo_config):
        """Test WahooService initialization with valid configuration."""
        with patch("backend.src.services.wahoo.service.Client") as mock_client:
            service = WahooService(mock_wahoo_config)

            assert service.client_id == "test_wahoo_client_id"
            assert service.client_secret == "test_wahoo_client_secret"
            assert service.tokens_file == Path(mock_wahoo_config.tokens_file_path)
            mock_client.assert_called_once()

    def test_init_creates_client(self, mock_wahoo_config):
        """Test that WahooService creates a Client instance."""
        with patch("backend.src.services.wahoo.service.Client") as mock_client:
            WahooService(mock_wahoo_config)
            mock_client.assert_called_once()


class TestWahooServiceTokenManagement:
    """Test token loading and saving functionality."""

    def test_load_tokens_file_not_exists(self, wahoo_service):
        """Test loading tokens when file doesn't exist."""
        result = wahoo_service._load_tokens()
        assert result is None

    def test_load_tokens_file_exists(self, wahoo_service, tmp_path):
        """Test loading tokens from existing file."""
        tokens_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
        }

        wahoo_service.tokens_file.write_text(json.dumps(tokens_data))

        result = wahoo_service._load_tokens()
        assert result == tokens_data

    def test_load_tokens_invalid_json(self, wahoo_service):
        """Test loading tokens with invalid JSON."""
        wahoo_service.tokens_file.write_text("invalid json")

        result = wahoo_service._load_tokens()
        assert result is None

    def test_save_tokens_success(self, wahoo_service):
        """Test saving tokens successfully."""
        tokens_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
        }

        wahoo_service._save_tokens(tokens_data)

        assert wahoo_service.tokens_file.exists()
        loaded_tokens = json.loads(wahoo_service.tokens_file.read_text())
        assert loaded_tokens == tokens_data

    def test_save_tokens_with_datetime(self, wahoo_service):
        """Test saving tokens with datetime objects."""
        tokens_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": datetime.now(),
        }

        wahoo_service._save_tokens(tokens_data)

        assert wahoo_service.tokens_file.exists()
        loaded_tokens = json.loads(wahoo_service.tokens_file.read_text())
        assert "access_token" in loaded_tokens
        assert "refresh_token" in loaded_tokens
        assert "expires_at" in loaded_tokens

    def test_save_tokens_creates_directory(self, wahoo_service, tmp_path):
        """Test that save_tokens creates parent directory if needed."""
        # Create a nested path that doesn't exist
        nested_path = tmp_path / "nested" / "tokens.json"
        wahoo_service.tokens_file = nested_path

        tokens_data = {"access_token": "test_token"}
        wahoo_service._save_tokens(tokens_data)

        assert nested_path.exists()
        assert nested_path.parent.exists()


class TestWahooServiceAuthorization:
    """Test OAuth authorization functionality."""

    def test_get_authorization_url_default_state(self, wahoo_service):
        """Test generating authorization URL with default state."""
        with patch.object(wahoo_service.client, "authorization_url") as mock_auth_url:
            mock_auth_url.return_value = (
                "https://api.wahooligan.com/oauth/authorize?test=url"
            )

            result = wahoo_service.get_authorization_url()

            mock_auth_url.assert_called_once_with(
                client_id="test_wahoo_client_id",
                redirect_uri="https://test.example.com/wahoo-callback",
                scope=["user_read", "routes_write"],
                state="wahoo_auth",
            )
            assert result == "https://api.wahooligan.com/oauth/authorize?test=url"

    def test_get_authorization_url_custom_state(self, wahoo_service):
        """Test generating authorization URL with custom state."""
        with patch.object(wahoo_service.client, "authorization_url") as mock_auth_url:
            mock_auth_url.return_value = (
                "https://api.wahooligan.com/oauth/authorize?test=url"
            )

            wahoo_service.get_authorization_url("custom_state")

            mock_auth_url.assert_called_once_with(
                client_id="test_wahoo_client_id",
                redirect_uri="https://test.example.com/wahoo-callback",
                scope=["user_read", "routes_write"],
                state="custom_state",
            )


class TestWahooServiceTokenExchange:
    """Test token exchange functionality."""

    def test_exchange_code_for_token_success(self, wahoo_service):
        """Test successful token exchange."""
        mock_access_info = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(
            wahoo_service.client, "exchange_code_for_token"
        ) as mock_exchange:
            mock_exchange.return_value = mock_access_info

            result = wahoo_service.exchange_code_for_token("test_code")

            mock_exchange.assert_called_once_with(
                client_id="test_wahoo_client_id",
                client_secret="test_wahoo_client_secret",
                code="test_code",
                redirect_uri="https://test.example.com/wahoo-callback",
            )
            assert result == mock_access_info
            assert wahoo_service.tokens_file.exists()

    def test_exchange_code_for_token_failure(self, wahoo_service):
        """Test token exchange failure."""
        with patch.object(
            wahoo_service.client, "exchange_code_for_token"
        ) as mock_exchange:
            mock_exchange.side_effect = Exception("Token exchange failed")

            with pytest.raises(Exception, match="Token exchange failed"):
                wahoo_service.exchange_code_for_token("invalid_code")


class TestWahooServiceTokenRefresh:
    """Test token refresh functionality."""

    def test_refresh_access_token_success(self, wahoo_service):
        """Test successful token refresh."""
        # Setup existing tokens
        existing_tokens = {
            "access_token": "old_access_token",
            "refresh_token": "old_refresh_token",
            "expires_at": 9999999999,
        }
        wahoo_service._save_tokens(existing_tokens)

        mock_refresh_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(wahoo_service.client, "refresh_access_token") as mock_refresh:
            mock_refresh.return_value = mock_refresh_response

            result = wahoo_service.refresh_access_token()

            mock_refresh.assert_called_once_with(
                client_id="test_wahoo_client_id",
                client_secret="test_wahoo_client_secret",
                refresh_token="old_refresh_token",
            )
            assert result is True

    def test_refresh_access_token_no_tokens(self, wahoo_service):
        """Test token refresh when no tokens exist."""
        result = wahoo_service.refresh_access_token()
        assert result is False

    def test_refresh_access_token_no_refresh_token(self, wahoo_service):
        """Test token refresh when no refresh token exists."""
        tokens_without_refresh = {
            "access_token": "test_access_token",
            "expires_at": 9999999999,
        }
        wahoo_service._save_tokens(tokens_without_refresh)

        result = wahoo_service.refresh_access_token()
        assert result is False

    def test_refresh_access_token_failure(self, wahoo_service):
        """Test token refresh failure."""
        existing_tokens = {
            "access_token": "old_access_token",
            "refresh_token": "old_refresh_token",
            "expires_at": 9999999999,
        }
        wahoo_service._save_tokens(existing_tokens)

        with patch.object(wahoo_service.client, "refresh_access_token") as mock_refresh:
            mock_refresh.side_effect = Exception("Refresh failed")

            result = wahoo_service.refresh_access_token()
            assert result is False


class TestWahooServiceAuthentication:
    """Test authentication state management."""

    def test_ensure_authenticated_no_tokens(self, wahoo_service):
        """Test _ensure_authenticated when no tokens exist."""
        with pytest.raises(WahooAccessUnauthorized, match="No tokens available"):
            wahoo_service._ensure_authenticated()

    def test_ensure_authenticated_no_access_token(self, wahoo_service):
        """Test _ensure_authenticated when no access token exists."""
        tokens_without_access = {
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
        }
        wahoo_service._save_tokens(tokens_without_access)

        with pytest.raises(WahooAccessUnauthorized, match="No access token available"):
            wahoo_service._ensure_authenticated()

    def test_ensure_authenticated_valid_token(self, wahoo_service):
        """Test _ensure_authenticated with valid token."""
        valid_tokens = {
            "access_token": "valid_access_token",
            "refresh_token": "valid_refresh_token",
            "expires_at": 9999999999,  # Far in the future
        }
        wahoo_service._save_tokens(valid_tokens)

        wahoo_service._ensure_authenticated()

        # Should set the access token on the client
        assert wahoo_service.client.access_token == "valid_access_token"

    def test_ensure_authenticated_expired_token_refresh_success(self, wahoo_service):
        """Test _ensure_authenticated with expired token that refreshes successfully."""
        expired_tokens = {
            "access_token": "expired_access_token",
            "refresh_token": "valid_refresh_token",
            "expires_at": 1000000000,  # Past timestamp
        }
        wahoo_service._save_tokens(expired_tokens)

        new_tokens = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(wahoo_service, "refresh_access_token") as mock_refresh:
            mock_refresh.return_value = True
            with patch.object(wahoo_service, "_load_tokens") as mock_load:
                # First call returns expired tokens, second call returns new tokens
                mock_load.side_effect = [expired_tokens, new_tokens]

                wahoo_service._ensure_authenticated()

                mock_refresh.assert_called_once()
                assert wahoo_service.client.access_token == "new_access_token"

    def test_ensure_authenticated_expired_token_refresh_failure(self, wahoo_service):
        """Test _ensure_authenticated with expired token that fails to refresh."""
        expired_tokens = {
            "access_token": "expired_access_token",
            "refresh_token": "invalid_refresh_token",
            "expires_at": 1000000000,  # Past timestamp
        }
        wahoo_service._save_tokens(expired_tokens)

        with patch.object(wahoo_service, "refresh_access_token") as mock_refresh:
            mock_refresh.return_value = False

            with pytest.raises(
                WahooAccessUnauthorized, match="Token expired and refresh failed"
            ):
                wahoo_service._ensure_authenticated()


class TestWahooServiceDeauthorization:
    """Test application deauthorization."""

    def test_deauthorize_success(self, wahoo_service):
        """Test successful deauthorization."""
        # Setup valid tokens
        valid_tokens = {
            "access_token": "valid_access_token",
            "refresh_token": "valid_refresh_token",
            "expires_at": 9999999999,
        }
        wahoo_service._save_tokens(valid_tokens)

        with patch.object(wahoo_service.client, "deauthorize") as mock_deauth:
            wahoo_service.deauthorize()
            mock_deauth.assert_called_once()

    def test_deauthorize_not_authenticated(self, wahoo_service):
        """Test deauthorization when not authenticated."""
        with pytest.raises(WahooAccessUnauthorized):
            wahoo_service.deauthorize()

    def test_deauthorize_api_error(self, wahoo_service):
        """Test deauthorization with API error."""
        valid_tokens = {
            "access_token": "valid_access_token",
            "refresh_token": "valid_refresh_token",
            "expires_at": 9999999999,
        }
        wahoo_service._save_tokens(valid_tokens)

        with patch.object(wahoo_service.client, "deauthorize") as mock_deauth:
            mock_deauth.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                wahoo_service.deauthorize()

    def test_deauthorize_general_error(self, wahoo_service):
        """Test deauthorization with general error."""
        valid_tokens = {
            "access_token": "valid_access_token",
            "refresh_token": "valid_refresh_token",
            "expires_at": 9999999999,
        }
        wahoo_service._save_tokens(valid_tokens)

        with patch.object(wahoo_service.client, "deauthorize") as mock_deauth:
            mock_deauth.side_effect = Exception("Network error")

            with pytest.raises(Exception, match="Network error"):
                wahoo_service.deauthorize()


class TestWahooServiceIntegration:
    """Test integration scenarios."""

    def test_full_oauth_flow(self, wahoo_service):
        """Test complete OAuth flow from authorization to token exchange."""
        # Step 1: Generate authorization URL
        with patch.object(wahoo_service.client, "authorization_url") as mock_auth_url:
            mock_auth_url.return_value = (
                "https://api.wahooligan.com/oauth/authorize?test=url"
            )

            auth_url = wahoo_service.get_authorization_url(
                "https://example.com/callback"
            )
            assert auth_url == "https://api.wahooligan.com/oauth/authorize?test=url"

        # Step 2: Exchange code for token
        mock_access_info = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(
            wahoo_service.client, "exchange_code_for_token"
        ) as mock_exchange:
            mock_exchange.return_value = mock_access_info

            result = wahoo_service.exchange_code_for_token("test_code")
            assert result == mock_access_info
            assert wahoo_service.tokens_file.exists()

        # Step 3: Verify tokens are saved
        loaded_tokens = wahoo_service._load_tokens()
        assert loaded_tokens == mock_access_info

    def test_token_refresh_flow(self, wahoo_service):
        """Test token refresh flow."""
        # Setup initial tokens
        initial_tokens = {
            "access_token": "initial_access_token",
            "refresh_token": "initial_refresh_token",
            "expires_at": 1000000000,  # Expired
        }
        wahoo_service._save_tokens(initial_tokens)

        # Mock successful refresh
        new_tokens = {
            "access_token": "refreshed_access_token",
            "refresh_token": "refreshed_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(wahoo_service.client, "refresh_access_token") as mock_refresh:
            mock_refresh.return_value = new_tokens

            result = wahoo_service.refresh_access_token()
            assert result is True

            # Verify new tokens are saved
            loaded_tokens = wahoo_service._load_tokens()
            assert loaded_tokens == new_tokens


class TestWahooServiceExtended:
    """Extended tests for WahooService to cover missing lines."""

    def test_save_tokens_convert_datetime_recursive_dict(self):
        """Test _save_tokens with nested datetime objects in dict."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Create tokens with nested datetime objects
            from datetime import datetime

            tokens = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "expires_at": 9999999999,
                "user_info": {
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
                "metadata": {
                    "nested": {
                        "timestamp": datetime.now(),
                    },
                },
            }

            with patch("builtins.open", _mock_open()):
                with patch("json.dump") as mock_json_dump:
                    service._save_tokens(tokens)

                    # Should call json.dump with serialized tokens
                    mock_json_dump.assert_called_once()
                    call_args = mock_json_dump.call_args[0][0]

                    # Check that datetime objects are converted to ISO format
                    assert isinstance(call_args["user_info"]["created_at"], str)
                    assert isinstance(call_args["user_info"]["updated_at"], str)
                    assert isinstance(call_args["metadata"]["nested"]["timestamp"], str)

    def test_save_tokens_convert_datetime_recursive_list(self):
        """Test _save_tokens with datetime objects in list."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Create tokens with datetime objects in list
            from datetime import datetime

            tokens = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "expires_at": 9999999999,
                "timestamps": [datetime.now(), datetime.now()],
                "nested_list": [
                    {"created": datetime.now()},
                    {"updated": datetime.now()},
                ],
            }

            with patch("builtins.open", _mock_open()):
                with patch("json.dump") as mock_json_dump:
                    service._save_tokens(tokens)

                    # Should call json.dump with serialized tokens
                    mock_json_dump.assert_called_once()
                    call_args = mock_json_dump.call_args[0][0]

                    # Check that datetime objects in list are converted
                    assert all(isinstance(ts, str) for ts in call_args["timestamps"])
                    # Check that datetime objects in nested list items are converted
                    for item in call_args["nested_list"]:
                        if "created" in item:
                            assert isinstance(item["created"], str)
                        if "updated" in item:
                            assert isinstance(item["updated"], str)

    def test_save_tokens_convert_datetime_other_types(self):
        """Test _save_tokens with other types that should pass through."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Create tokens with various types
            tokens = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "expires_at": 9999999999,
                "user_id": 12345,
                "is_active": True,
                "metadata": None,
            }

            with patch("builtins.open", _mock_open()):
                with patch("json.dump") as mock_json_dump:
                    service._save_tokens(tokens)

                    # Should call json.dump with tokens unchanged
                    mock_json_dump.assert_called_once()
                    call_args = mock_json_dump.call_args[0][0]

                    # Check that non-datetime types pass through unchanged
                    assert call_args["access_token"] == "test_token"
                    assert call_args["refresh_token"] == "test_refresh"
                    assert call_args["expires_at"] == 9999999999
                    assert call_args["user_id"] == 12345
                    assert call_args["is_active"] is True
                    assert call_args["metadata"] is None

    def test_deauthorize_401_unauthorized_error(self):
        """Test deauthorize method with 401 Unauthorized error."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Setup valid tokens
            valid_tokens = {
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token",
                "expires_at": 9999999999,
            }
            service._save_tokens(valid_tokens)

            with patch.object(service.client, "deauthorize") as mock_deauth:
                mock_deauth.side_effect = ValueError("401 Unauthorized")

                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    with pytest.raises(WahooAccessUnauthorized):
                        service.deauthorize()

                    mock_logger.error.assert_called_with(
                        "Wahoo API access unauthorized: 401 Unauthorized"
                    )

    def test_deauthorize_unauthorized_error_lowercase(self):
        """Test deauthorize method with unauthorized error (lowercase)."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Setup valid tokens
            valid_tokens = {
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token",
                "expires_at": 9999999999,
            }
            service._save_tokens(valid_tokens)

            with patch.object(service.client, "deauthorize") as mock_deauth:
                mock_deauth.side_effect = ValueError("access unauthorized")

                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    with pytest.raises(WahooAccessUnauthorized):
                        service.deauthorize()

                    mock_logger.error.assert_called_with(
                        "Wahoo API access unauthorized: access unauthorized"
                    )

    def test_deauthorize_general_error(self):
        """Test deauthorize method with general error."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Setup valid tokens
            valid_tokens = {
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token",
                "expires_at": 9999999999,
            }
            service._save_tokens(valid_tokens)

            with patch.object(service.client, "deauthorize") as mock_deauth:
                mock_deauth.side_effect = ValueError("Network error")

                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    with pytest.raises(ValueError, match="Network error"):
                        service.deauthorize()

                    mock_logger.error.assert_called_with(
                        "Failed to deauthorize: Network error"
                    )

    def test_deauthorize_exception_during_deauthorize(self):
        """Test deauthorize method with exception during deauthorize."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Setup valid tokens
            valid_tokens = {
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token",
                "expires_at": 9999999999,
            }
            service._save_tokens(valid_tokens)

            with patch.object(service.client, "deauthorize") as mock_deauth:
                mock_deauth.side_effect = Exception("Unexpected error")

                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    with pytest.raises(Exception, match="Unexpected error"):
                        service.deauthorize()

                    mock_logger.error.assert_called_with(
                        "Failed to deauthorize: Unexpected error"
                    )


def _mock_open():
    """Mock open function for testing file operations."""
    from unittest.mock import mock_open as mock_open_func

    return mock_open_func()


class TestWahooServiceMissing:
    """Test missing service coverage."""

    @pytest.fixture
    def service(self):
        """Create a WahooService instance."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            return WahooService(config)

    def test_get_user_unauthorized_error(self, service):
        """Test get_user with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_user") as mock_get_user,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_user.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                service.get_user()

    def test_get_user_other_value_error(self, service):
        """Test get_user with other ValueError."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_user") as mock_get_user,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_user.side_effect = ValueError("Network error")

            with pytest.raises(ValueError, match="Network error"):
                service.get_user()

    def test_get_user_exception(self, service):
        """Test get_user with general exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_user") as mock_get_user,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_user.side_effect = Exception("Unexpected error")

            with pytest.raises(Exception, match="Unexpected error"):
                service.get_user()

    def test_get_route_unauthorized_error(self, service):
        """Test get_route with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_route") as mock_get_route,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_route.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                service.get_route(123)

    def test_get_route_other_value_error(self, service):
        """Test get_route with other ValueError."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_route") as mock_get_route,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_route.side_effect = ValueError("Not found")

            with pytest.raises(ValueError, match="Not found"):
                service.get_route(999)

    def test_get_route_exception(self, service):
        """Test get_route with general exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_route") as mock_get_route,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_route.side_effect = Exception("Unexpected error")

            with pytest.raises(Exception, match="Unexpected error"):
                service.get_route(456)

    def test_get_routes_unauthorized_error(self, service):
        """Test get_routes with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_routes") as mock_get_routes,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_routes.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                service.get_routes()

    def test_get_routes_other_value_error(self, service):
        """Test get_routes with other ValueError."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_routes") as mock_get_routes,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_routes.side_effect = ValueError("Network error")

            with pytest.raises(ValueError, match="Network error"):
                service.get_routes()

    def test_get_routes_exception(self, service):
        """Test get_routes with general exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_routes") as mock_get_routes,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_routes.side_effect = Exception("Unexpected error")

            with pytest.raises(Exception, match="Unexpected error"):
                service.get_routes()

    def test_create_route_value_error_other(self, service):
        """Test create_route with ValueError that is not unauthorized."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("Invalid route data")

            with pytest.raises(ValueError, match="Invalid route data"):
                service.create_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_create_route_exception(self, service):
        """Test create_route with non-ValueError exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                service.create_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_update_route_value_error_other(self, service):
        """Test update_route with ValueError that is not unauthorized."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_update.side_effect = ValueError("Route not found")

            with pytest.raises(ValueError, match="Route not found"):
                service.update_route(
                    route_id=999,
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Updated Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_update_route_exception(self, service):
        """Test update_route with non-ValueError exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_update.side_effect = Exception("Network error")

            with pytest.raises(Exception, match="Network error"):
                service.update_route(
                    route_id=456,
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Updated Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_upload_route_success(self, service):
        """Test upload_route successful creation."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.return_value = {"id": 789, "name": "Uploaded Route"}

            result = service.upload_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Uploaded Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
                external_id="test_789",
            )

            assert result == {"id": 789, "name": "Uploaded Route"}

    def test_upload_route_unauthorized_error(self, service):
        """Test upload_route with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_upload_route_already_exists(self, service):
        """Test upload_route when route already exists."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("Route already exists")

            with pytest.raises(ValueError, match="Update not implemented yet"):
                service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                    external_id="test_123",
                )

    def test_upload_route_other_value_error(self, service):
        """Test upload_route with other ValueError."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("Invalid route data")

            with pytest.raises(ValueError, match="Invalid route data"):
                service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_upload_route_exception(self, service):
        """Test upload_route with general exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = Exception("Network timeout")

            with pytest.raises(Exception, match="Network timeout"):
                service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_get_user_success(self, service):
        """Test get_user successful execution."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {"id": 123, "name": "Test User"}

            result = service.get_user()

            assert result == {"id": 123, "name": "Test User"}

    def test_get_route_success(self, service):
        """Test get_route successful execution."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_route") as mock_get_route,
        ):
            mock_get_route.return_value = {"id": 456, "name": "Test Route"}

            result = service.get_route(456)

            assert result == {"id": 456, "name": "Test Route"}

    def test_get_routes_success(self, service):
        """Test get_routes successful execution."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_routes") as mock_get_routes,
        ):
            mock_get_routes.return_value = [
                {"id": 1, "name": "Route 1"},
                {"id": 2, "name": "Route 2"},
            ]

            result = service.get_routes()

            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 2

    def test_create_route_success_execution(self, service):
        """Test create_route successful execution (not just errors)."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
        ):
            mock_create.return_value = {"id": 111, "name": "Success Route"}

            result = service.create_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Success Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 111, "name": "Success Route"}

    def test_update_route_success_execution(self, service):
        """Test update_route successful execution (not just errors)."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
        ):
            mock_update.return_value = {"id": 222, "name": "Updated Route"}

            result = service.update_route(
                route_id=222,
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Updated Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 222, "name": "Updated Route"}


class TestWahooServiceCreateRouteErrorHandling:
    """Test create_route error handling in service."""

    @pytest.fixture
    def service(self):
        """Create a WahooService instance."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            return WahooService(config)

    def test_create_route_with_401_unauthorized_in_lowercase(self, service):
        """Test create_route with unauthorized error (lowercase)."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("unauthorized access")

            with pytest.raises(WahooAccessUnauthorized):
                service.create_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_create_route_with_401_in_message(self, service):
        """Test create_route with 401 in error message."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("Error 401 occurred")

            with pytest.raises(WahooAccessUnauthorized):
                service.create_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )


class TestWahooServiceUpdateRouteErrorHandling:
    """Test update_route error handling in service."""

    @pytest.fixture
    def service(self):
        """Create a WahooService instance."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            return WahooService(config)

    def test_update_route_with_401_unauthorized_in_lowercase(self, service):
        """Test update_route with unauthorized error (lowercase)."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_update.side_effect = ValueError("unauthorized access")

            with pytest.raises(WahooAccessUnauthorized):
                service.update_route(
                    route_id=456,
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Updated Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_update_route_with_401_in_message(self, service):
        """Test update_route with 401 in error message."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_update.side_effect = ValueError("Error 401 occurred")

            with pytest.raises(WahooAccessUnauthorized):
                service.update_route(
                    route_id=456,
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Updated Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )


class TestWahooServiceSaveError:
    """Tests for Wahoo service _save_tokens error handling."""

    def test_save_tokens_file_write_error(self):
        """Test _save_tokens when file write fails."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Mock open to raise an exception
            with patch("builtins.open", side_effect=OSError("Permission denied")):
                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    tokens = {"access_token": "test_token"}
                    service._save_tokens(tokens)

                    # Should log the error
                    mock_logger.error.assert_called_once_with(
                        "Failed to save tokens: Permission denied"
                    )

    def test_save_tokens_json_dump_error(self):
        """Test _save_tokens when json.dump fails."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
            scopes=["user_read", "routes_write"],
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Mock json.dump to raise an exception
            with patch("builtins.open", _mock_open()):
                with patch(
                    "backend.src.services.wahoo.service.json.dump",
                    side_effect=TypeError("Not JSON serializable"),
                ):
                    with patch(
                        "backend.src.services.wahoo.service.logger"
                    ) as mock_logger:
                        tokens = {"access_token": "test_token"}
                        service._save_tokens(tokens)

                        # Should log the error
                        mock_logger.error.assert_called_once_with(
                            "Failed to save tokens: Not JSON serializable"
                        )
