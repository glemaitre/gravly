"""Unit tests for Wahoo client and protocol."""

import os
from unittest.mock import Mock, patch

import pytest
from requests import Session

from backend.src.services.wahoo.client import Client
from backend.src.services.wahoo.protocol import AccessInfo, ApiV1


class TestWahooClient:
    """Test Wahoo Client class."""

    def test_client_initialization_default(self):
        """Test Client initialization with default parameters."""
        client = Client()

        assert client.protocol is not None
        assert isinstance(client.protocol, ApiV1)
        assert client.access_token is None
        assert client.token_expires is None
        assert client.refresh_token is None

    def test_client_initialization_with_token(self):
        """Test Client initialization with access token."""
        client = Client(access_token="test_token")

        assert client.access_token == "test_token"

    def test_client_initialization_with_all_params(self):
        """Test Client initialization with all parameters."""
        mock_limiter = Mock()
        mock_session = Mock(spec=Session)

        client = Client(
            access_token="test_token",
            rate_limit_requests=True,
            rate_limiter=mock_limiter,
            requests_session=mock_session,
            token_expires=9999999999,
            refresh_token="test_refresh_token",
        )

        assert client.access_token == "test_token"
        assert client.token_expires == 9999999999
        assert client.refresh_token == "test_refresh_token"

    def test_client_initialization_rate_limiting_disabled(self):
        """Test Client initialization with rate limiting disabled."""
        client = Client(rate_limit_requests=False)

        assert client.protocol is not None
        assert client.protocol.rate_limiter is not None

    def test_client_initialization_rate_limiter_conflict(self):
        """Test Client initialization with conflicting rate limiter settings."""
        mock_limiter = Mock()

        with pytest.raises(
            ValueError,
            match="Cannot specify rate_limiter object",
        ):
            Client(rate_limit_requests=False, rate_limiter=mock_limiter)

    def test_client_access_token_property(self):
        """Test Client access_token property."""
        client = Client()

        # Test getter
        assert client.access_token is None

        # Test setter
        client.access_token = "new_token"
        assert client.access_token == "new_token"
        assert client.protocol.access_token == "new_token"

    def test_client_token_expires_property(self):
        """Test Client token_expires property."""
        client = Client()

        # Test getter
        assert client.token_expires is None

        # Test setter
        client.token_expires = 9999999999
        assert client.token_expires == 9999999999
        assert client.protocol.token_expires == 9999999999

    def test_client_refresh_token_property(self):
        """Test Client refresh_token property."""
        client = Client()

        # Test getter
        assert client.refresh_token is None

        # Test setter
        client.refresh_token = "new_refresh_token"
        assert client.refresh_token == "new_refresh_token"
        assert client.protocol.refresh_token == "new_refresh_token"

    def test_client_authorization_url(self):
        """Test Client authorization_url method."""
        client = Client()

        with patch.object(client.protocol, "authorization_url") as mock_auth_url:
            mock_auth_url.return_value = (
                "https://api.wahooligan.com/oauth/authorize?test=url"
            )

            result = client.authorization_url(
                client_id="test_client_id",
                redirect_uri="https://example.com/callback",
                scope=["routes_write", "user_read"],
                state="test_state",
            )

            mock_auth_url.assert_called_once_with(
                client_id="test_client_id",
                redirect_uri="https://example.com/callback",
                approval_prompt="auto",
                scope=["routes_write", "user_read"],
                state="test_state",
            )
            assert result == "https://api.wahooligan.com/oauth/authorize?test=url"

    def test_client_exchange_code_for_token(self):
        """Test Client exchange_code_for_token method."""
        client = Client()

        mock_access_info = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(client.protocol, "exchange_code_for_token") as mock_exchange:
            mock_exchange.return_value = mock_access_info

            result = client.exchange_code_for_token(
                client_id="test_client_id",
                client_secret="test_client_secret",
                code="test_code",
                redirect_uri="https://test.example.com/callback",
            )

            mock_exchange.assert_called_once_with(
                client_id="test_client_id",
                client_secret="test_client_secret",
                code="test_code",
                redirect_uri="https://test.example.com/callback",
            )
            assert result == mock_access_info

    def test_client_refresh_access_token(self):
        """Test Client refresh_access_token method."""
        client = Client()

        mock_access_info = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(client.protocol, "refresh_access_token") as mock_refresh:
            mock_refresh.return_value = mock_access_info

            result = client.refresh_access_token(
                client_id="test_client_id",
                client_secret="test_client_secret",
                refresh_token="old_refresh_token",
            )

            mock_refresh.assert_called_once_with(
                client_id="test_client_id",
                client_secret="test_client_secret",
                refresh_token="old_refresh_token",
            )
            assert result == mock_access_info

    def test_client_deauthorize(self):
        """Test Client deauthorize method."""
        client = Client()

        with patch.object(client.protocol, "_request") as mock_request:
            client.deauthorize()
            # Verify _request was called with the correct URL and method
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert (
                "oauth/deauthorize" in call_args[0][0]
            )  # URL contains oauth/deauthorize
            assert call_args[1]["method"] == "POST"  # method is POST


class TestWahooProtocol:
    """Test Wahoo ApiV1 protocol class."""

    def test_protocol_initialization_default(self):
        """Test ApiV1 initialization with default parameters."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            assert protocol.access_token is None
            assert protocol.token_expires is None
            assert protocol.refresh_token is None
            assert protocol.client_id is None
            assert protocol.client_secret is None
            assert protocol.server == "api.wahooligan.com"
            assert protocol.api_base == "/v1"

    def test_protocol_initialization_with_params(self):
        """Test ApiV1 initialization with parameters."""
        mock_session = Mock(spec=Session)
        mock_limiter = Mock()

        with patch.dict(
            os.environ,
            {
                "WAHOO_CLIENT_ID": "test_client_id",
                "WAHOO_CLIENT_SECRET": "test_client_secret",
                "SILENCE_TOKEN_WARNINGS": "true",
            },
            clear=True,
        ):
            protocol = ApiV1(
                access_token="test_token",
                requests_session=mock_session,
                rate_limiter=mock_limiter,
                token_expires=9999999999,
                refresh_token="test_refresh_token",
                client_id="test_client_id",
                client_secret="test_client_secret",
            )

            assert protocol.access_token == "test_token"
            assert protocol.token_expires == 9999999999
            assert protocol.refresh_token == "test_refresh_token"
            assert protocol.client_id == "test_client_id"
            assert protocol.client_secret == "test_client_secret"
            assert protocol.rsession == mock_session
            assert protocol.rate_limiter == mock_limiter

    def test_protocol_authorization_url(self):
        """Test ApiV1 authorization_url method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = (
                "https://api.wahooligan.com/oauth/authorize?test=url"
            )

            result = protocol.authorization_url(
                client_id="test_client_id",
                redirect_uri="https://example.com/callback",
                scope=["routes_write", "user_read"],
                state="test_state",
            )

            # Verify the URL is properly constructed
            assert "api.wahooligan.com" in result
            assert "/oauth/authorize" in result

    def test_protocol_authorization_url_default_scope(self):
        """Test ApiV1 authorization_url with default scope."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = (
                "https://api.wahooligan.com/oauth/authorize?test=url"
            )

            result = protocol.authorization_url(
                client_id="test_client_id",
                redirect_uri="https://example.com/callback",
            )

            # Should use default scope
            assert "api.wahooligan.com" in result

    def test_protocol_authorization_url_string_scope(self):
        """Test ApiV1 authorization_url with string scope."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = (
                "https://api.wahooligan.com/oauth/authorize?test=url"
            )

            result = protocol.authorization_url(
                client_id="test_client_id",
                redirect_uri="https://example.com/callback",
                scope="routes_write",
            )

            assert "api.wahooligan.com" in result

    def test_protocol_exchange_code_for_token(self):
        """Test ApiV1 exchange_code_for_token method."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            mock_response = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": 9999999999,
            }

            # Mock the entire _request method to avoid making real HTTP calls
            with patch.object(protocol, "_request") as mock_request:
                mock_request.return_value = mock_response

                access_info = protocol.exchange_code_for_token(
                    client_id="test_client_id",
                    client_secret="test_client_secret",
                    redirect_uri="https://test.example.com/callback",
                    code="test_code",
                )

                mock_request.assert_called_once()
                assert access_info["access_token"] == "test_access_token"
                assert access_info["refresh_token"] == "test_refresh_token"
                assert access_info["expires_at"] == 9999999999

    def test_protocol_refresh_access_token(self):
        """Test ApiV1 refresh_access_token method."""
        protocol = ApiV1()

        mock_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = mock_response

            access_info = protocol.refresh_access_token(
                client_id="test_client_id",
                client_secret="test_client_secret",
                refresh_token="old_refresh_token",
            )

            mock_request.assert_called_once()
            assert access_info["access_token"] == "new_access_token"
            assert access_info["refresh_token"] == "new_refresh_token"
            assert access_info["expires_at"] == 9999999999
            assert protocol.access_token == "new_access_token"
            assert protocol.refresh_token == "new_refresh_token"
            assert protocol.token_expires == 9999999999

    def test_protocol_resolve_url_relative(self):
        """Test ApiV1 resolve_url with relative URL."""
        protocol = ApiV1()

        result = protocol.resolve_url("test/endpoint")

        assert result == "https://api.wahooligan.com/v1/test/endpoint"

    def test_protocol_resolve_url_absolute(self):
        """Test ApiV1 resolve_url with absolute URL."""
        protocol = ApiV1()

        result = protocol.resolve_url("https://example.com/test")

        assert result == "https://example.com/test"

    def test_protocol_get_method(self):
        """Test ApiV1 get method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"test": "data"}

            result = protocol.get("test/endpoint", param1="value1")

            mock_request.assert_called_once_with(
                "test/endpoint",
                params={"param1": "value1"},
                check_for_errors=True,
            )
            assert result == {"test": "data"}

    def test_protocol_post_method(self):
        """Test ApiV1 post method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"test": "data"}

            result = protocol.post("test/endpoint", param1="value1")

            mock_request.assert_called_once_with(
                "test/endpoint",
                params={"param1": "value1"},
                files=None,
                method="POST",
                check_for_errors=True,
            )
            assert result == {"test": "data"}

    def test_protocol_put_method(self):
        """Test ApiV1 put method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"test": "data"}

            result = protocol.put("test/endpoint", param1="value1")

            mock_request.assert_called_once_with(
                "test/endpoint",
                params={"param1": "value1"},
                method="PUT",
                check_for_errors=True,
            )
            assert result == {"test": "data"}

    def test_protocol_delete_method(self):
        """Test ApiV1 delete method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"test": "data"}

            result = protocol.delete("test/endpoint", param1="value1")

            mock_request.assert_called_once_with(
                "test/endpoint",
                params={"param1": "value1"},
                method="DELETE",
                check_for_errors=True,
            )
            assert result == {"test": "data"}

    def test_protocol_handle_protocol_error_success(self):
        """Test ApiV1 _handle_protocol_error with successful response."""
        protocol = ApiV1()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        result = protocol._handle_protocol_error(mock_response)

        assert result == mock_response

    def test_protocol_handle_protocol_error_http_error(self):
        """Test ApiV1 _handle_protocol_error with HTTP error."""
        protocol = ApiV1()

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.json.return_value = {"message": "Invalid request"}

        with pytest.raises(ValueError, match="400 Bad Request"):
            protocol._handle_protocol_error(mock_response)

    def test_protocol_handle_protocol_error_with_message(self):
        """Test ApiV1 _handle_protocol_error with error message."""
        protocol = ApiV1()

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.json.return_value = {
            "message": "Invalid token",
            "errors": ["Token expired"],
        }

        with pytest.raises(
            ValueError,
            match="401 Unauthorized - Invalid token: \\['Token expired'\\]",
        ):
            protocol._handle_protocol_error(mock_response)

    def test_protocol_extract_referenced_vars(self):
        """Test ApiV1 _extract_referenced_vars method."""
        protocol = ApiV1()

        # Test with format variables
        result = protocol._extract_referenced_vars("test/{var1}/endpoint/{var2}")
        assert set(result) == {"var1", "var2"}

        # Test with no variables
        result = protocol._extract_referenced_vars("test/endpoint")
        assert result == []

        # Test with single variable
        result = protocol._extract_referenced_vars("test/{id}")
        assert result == ["id"]


class TestWahooAccessInfo:
    """Test AccessInfo TypedDict."""

    def test_access_info_structure(self):
        """Test AccessInfo structure."""
        access_info: AccessInfo = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
        }

        assert access_info["access_token"] == "test_access_token"
        assert access_info["refresh_token"] == "test_refresh_token"
        assert access_info["expires_at"] == 9999999999

    def test_access_info_required_fields(self):
        """Test that AccessInfo requires all fields."""
        # This should work
        access_info: AccessInfo = {
            "access_token": "test",
            "refresh_token": "test",
            "expires_at": 123,
        }
        assert access_info is not None

        # Missing fields would cause type errors in a real type checker
        # but we can't easily test that here without mypy
