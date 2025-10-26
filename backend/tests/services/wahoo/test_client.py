"""Unit tests for Wahoo client."""

from unittest.mock import patch

import pytest

from backend.src.services.wahoo.client import Client
from backend.src.services.wahoo.protocol import ApiV1


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

    def test_client_access_token_property(self):
        """Test Client access_token property."""
        client = Client()

        # Test getter
        assert client.access_token is None

        # Test setter
        client.access_token = "new_token"
        assert client.access_token == "new_token"
        assert client.protocol.access_token == "new_token"

    def test_get_user_method(self):
        """Test client get_user method."""
        client = Client()

        with patch.object(client.protocol, "get_user") as mock_get_user:
            mock_get_user.return_value = {"id": 123, "name": "Test User"}

            result = client.get_user()

            assert result == {"id": 123, "name": "Test User"}
            mock_get_user.assert_called_once()

    def test_get_route_method(self):
        """Test client get_route method."""
        client = Client()

        with patch.object(client.protocol, "get_route") as mock_get_route:
            mock_get_route.return_value = {"id": 456, "name": "Test Route"}

            result = client.get_route(456)

            assert result == {"id": 456, "name": "Test Route"}
            mock_get_route.assert_called_once_with(route_id=456)

    def test_get_routes_method(self):
        """Test client get_routes method."""
        client = Client()

        with patch.object(client.protocol, "get_routes") as mock_get_routes:
            mock_get_routes.return_value = [{"id": 1}, {"id": 2}]

            result = client.get_routes()

            assert result == [{"id": 1}, {"id": 2}]
            mock_get_routes.assert_called_once()

    def test_client_create_route(self):
        """Test client create_route method."""
        client = Client()

        with patch.object(client.protocol, "create_route") as mock_create:
            mock_create.return_value = {"id": 123}

            result = client.create_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Test Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 123}
            mock_create.assert_called_once()

    def test_client_update_route(self):
        """Test client update_route method."""
        client = Client()

        with patch.object(client.protocol, "update_route") as mock_update:
            mock_update.return_value = {"id": 456}

            result = client.update_route(
                route_id=456,
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Test Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 456}
            mock_update.assert_called_once()

    def test_upload_route_success(self):
        """Test upload_route successfully creates a route."""
        client = Client()

        with patch.object(client, "create_route") as mock_create:
            mock_create.return_value = {"id": 123, "name": "Test Route"}

            result = client.upload_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Test Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 123, "name": "Test Route"}
            mock_create.assert_called_once()

    def test_upload_route_already_exists(self):
        """Test upload_route when route already exists."""
        client = Client()

        with patch.object(client, "create_route") as mock_create:
            mock_create.side_effect = ValueError("Route already exists")

            with pytest.raises(ValueError, match="Update not implemented yet"):
                client.upload_route(
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

    def test_upload_route_other_error(self):
        """Test upload_route with other error."""
        client = Client()

        with patch.object(client, "create_route") as mock_create:
            mock_create.side_effect = ValueError("Network error")

            with pytest.raises(ValueError, match="Network error"):
                client.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_client_initialization_rate_limiter_conflict(self):
        """Test Client initialization with conflicting rate limiter settings."""
        from backend.src.services.wahoo.limiter import DefaultRateLimiter

        with pytest.raises(
            ValueError,
            match=(
                "Cannot specify rate_limiter object when rate_limit_requests is False"
            ),
        ):
            Client(rate_limit_requests=False, rate_limiter=DefaultRateLimiter())

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
        # Set an access token so the deauthorize method doesn't fail the pre-check
        client.access_token = "test_token"

        with patch.object(client.protocol, "_request") as mock_request:
            client.deauthorize()
            # Verify _request was called with the correct URL and method
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert "permissions" in call_args[0][0]  # URL contains permissions endpoint
            assert call_args[1]["method"] == "DELETE"  # method is DELETE
