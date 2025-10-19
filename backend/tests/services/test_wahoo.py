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
                scope=["routes_write", "user_read"],
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
                scope=["routes_write", "user_read"],
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
