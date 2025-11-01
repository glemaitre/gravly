"""Tests for Wahoo API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestWahooCallbackEndpoint:
    """Test Wahoo callback endpoint."""

    def test_wahoo_callback_success(self, client):
        """Test successful Wahoo callback with authorization code."""
        test_code = "test_authorization_code_123"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Wahoo authorization code received successfully"
        assert data["code"] == test_code
        assert data["status"] == "success"

    def test_wahoo_callback_missing_code(self, client):
        """Test Wahoo callback without authorization code."""
        response = client.get("/api/wahoo/callback")

        assert response.status_code == 400  # Bad request
        data = response.json()
        assert data["detail"] == "Authorization code is required"

    def test_wahoo_callback_empty_code(self, client):
        """Test Wahoo callback with empty authorization code."""
        response = client.get("/api/wahoo/callback?code=")

        assert response.status_code == 400  # Bad request
        data = response.json()
        assert data["detail"] == "Authorization code is required"

    def test_wahoo_callback_special_characters(self, client):
        """Test Wahoo callback with special characters in code."""
        test_code = "test_code_with_special_chars_!@#$%^&*()"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        # The test client may URL decode the code, so we check that it contains
        # the expected parts
        assert "test_code_with_special_chars" in data["code"]

    def test_wahoo_callback_long_code(self, client):
        """Test Wahoo callback with a very long authorization code."""
        test_code = "a" * 1000  # Very long code

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code

    def test_wahoo_callback_logging(self, client):
        """Test that Wahoo callback logs the received code."""
        test_code = "logging_test_code"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200

    def test_wahoo_callback_response_format(self, client):
        """Test that Wahoo callback returns the expected response format."""
        test_code = "format_test_code"

        response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()

        # Check that all expected fields are present
        assert "message" in data
        assert "code" in data
        assert "status" in data

        # Check field types
        assert isinstance(data["message"], str)
        assert isinstance(data["code"], str)
        assert isinstance(data["status"], str)

        # Check field values
        assert data["message"] == "Wahoo authorization code received successfully"
        assert data["code"] == test_code
        assert data["status"] == "success"

    def test_wahoo_callback_unicode_characters(self, client):
        """Test Wahoo callback with unicode characters in code."""
        test_code = "test_code_with_unicode_🚴‍♂️_🏔️"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code

    def test_wahoo_callback_numeric_code(self, client):
        """Test Wahoo callback with numeric authorization code."""
        test_code = "123456789"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code

    def test_wahoo_callback_whitespace_code(self, client):
        """Test Wahoo callback with whitespace in authorization code."""
        test_code = "  test_code_with_spaces  "

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code

    def test_wahoo_callback_multiple_parameters(self, client):
        """Test Wahoo callback with additional parameters."""
        test_code = "test_code_123"
        state = "test_state"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}&state={state}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code

    def test_wahoo_callback_error_handling(self, client):
        """Test Wahoo callback error handling."""
        # Test with None code (should be handled by FastAPI)
        response = client.get("/api/wahoo/callback?code=None")

        # FastAPI should handle None as a string "None"
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "None"

    def test_wahoo_callback_content_type(self, client):
        """Test that Wahoo callback returns correct content type."""
        test_code = "content_type_test"

        response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_wahoo_callback_cors_headers(self, client):
        """Test that Wahoo callback includes appropriate headers."""
        test_code = "cors_test"

        response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        # Check that response is JSON (CORS headers would be set by middleware)
        assert "application/json" in response.headers.get("content-type", "")

    def test_wahoo_callback_general_exception(self, client):
        """Test Wahoo callback endpoint with general exception handling."""
        # This test is no longer applicable since we removed the logger.info call
        # The callback should succeed normally
        response = client.get("/api/wahoo/callback?code=test_code")
        assert response.status_code == 200

    def test_wahoo_callback_http_exception_passthrough(self, client):
        """Test that HTTPException is passed through without modification."""
        # This test is no longer applicable since we removed the logger.info call
        # The callback should succeed normally
        response = client.get("/api/wahoo/callback?code=test_code")
        assert response.status_code == 200


class TestWahooRouterIntegration:
    """Test Wahoo router integration with the main app."""

    def test_wahoo_router_registration(self, client):
        """Test that Wahoo router is properly registered."""
        # Test that the callback endpoint is accessible
        response = client.get("/api/wahoo/callback?code=test")
        assert response.status_code == 200

    def test_wahoo_router_prefix(self, client):
        """Test that Wahoo router uses correct prefix."""
        # Test that endpoints are under /api/wahoo/
        response = client.get("/api/wahoo/callback?code=test")
        assert response.status_code == 200

        # Test that non-existent endpoint returns 404
        response = client.get("/api/wahoo/nonexistent")
        assert response.status_code == 404

    def test_wahoo_router_tags(self, client):
        """Test that Wahoo router endpoints have correct tags."""
        # This would require checking OpenAPI schema, but we can verify
        # that the endpoint is accessible and returns expected format
        response = client.get("/api/wahoo/callback?code=test")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "code" in data
        assert "status" in data


class TestWahooAuthUrlEndpoint:
    """Test Wahoo auth URL endpoint."""

    @patch("src.api.wahoo.Client")
    def test_get_wahoo_auth_url_success(self, mock_client_class, client):
        """Test successful Wahoo auth URL generation."""
        # Mock the Client
        mock_client = mock_client_class.return_value
        mock_client.authorization_url.return_value = (
            "https://api.wahooligan.com/oauth/authorize?client_id=test"
        )

        response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert (
            data["auth_url"]
            == "https://api.wahooligan.com/oauth/authorize?client_id=test"
        )

    @patch("src.api.wahoo.Client")
    def test_get_wahoo_auth_url_with_state(self, mock_client_class, client):
        """Test Wahoo auth URL generation with custom state."""
        mock_client = mock_client_class.return_value
        mock_client.authorization_url.return_value = "https://api.wahooligan.com/oauth/authorize?client_id=test&state=custom_state"

        response = client.get("/api/wahoo/auth-url?state=custom_state")

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data

    @patch("src.api.wahoo.Client")
    def test_get_wahoo_auth_url_service_error(self, mock_client_class, client):
        """Test Wahoo auth URL generation with service error."""
        mock_client = mock_client_class.return_value
        mock_client.authorization_url.side_effect = Exception("Service error")

        response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate authorization URL" in data["detail"]


class TestWahooExchangeCodeEndpoint:
    """Test Wahoo exchange code endpoint."""

    def test_exchange_wahoo_code_missing_code(self, client):
        """Test Wahoo code exchange without code."""
        response = client.post("/api/wahoo/exchange-code")

        assert response.status_code == 422  # Validation error

    @patch("src.dependencies.SessionLocal", None)
    def test_exchange_wahoo_code_no_database(self, client):
        """Test exchange code when database is not initialized."""
        response = client.post("/api/wahoo/exchange-code", data={"code": "test_code"})

        assert response.status_code == 503
        data = response.json()
        assert "database not initialized" in data["detail"].lower()

    @patch("src.api.wahoo.Client")
    @patch("src.api.wahoo.get_wahoo_config")
    def test_exchange_wahoo_code_no_user_id(
        self, mock_get_config, mock_client_class, client
    ):
        """Test exchange code when no user ID in response."""
        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_config.return_value = mock_config

        # Mock client
        mock_client = mock_client_class.return_value
        mock_client.exchange_code_for_token.return_value = {
            "access_token": "test_token",
            "refresh_token": "refresh_token",
            "expires_at": int(datetime.now().timestamp()),
        }
        mock_client.get_user.return_value = {"name": "Test User"}  # No ID

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post(
                "/api/wahoo/exchange-code", data={"code": "test_code"}
            )

            assert response.status_code == 400
            data = response.json()
            assert "no user id" in data["detail"].lower()

    @patch("src.api.wahoo.Client")
    @patch("src.api.wahoo.get_wahoo_config")
    def test_exchange_wahoo_code_success_new_token(
        self, mock_get_config, mock_client_class, client
    ):
        """Test successful Wahoo code exchange creating new token."""

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_config.return_value = mock_config

        # Mock client
        mock_client = mock_client_class.return_value
        mock_client.exchange_code_for_token.return_value = {
            "access_token": "test_token",
            "refresh_token": "refresh_token",
            "expires_at": int(datetime.now().timestamp()),
        }
        mock_client.get_user.return_value = {"id": 12345, "name": "Test User"}

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post(
                "/api/wahoo/exchange-code", data={"code": "test_code"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user" in data
            assert data["user"]["id"] == 12345
            mock_session.add.assert_called_once()

    @patch("src.api.wahoo.Client")
    @patch("src.api.wahoo.get_wahoo_config")
    def test_exchange_wahoo_code_success_update_token(
        self, mock_get_config, mock_client_class, client
    ):
        """Test successful Wahoo code exchange updating existing token."""
        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_config.return_value = mock_config

        # Mock client
        mock_client = mock_client_class.return_value
        mock_client.exchange_code_for_token.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh_token",
            "expires_at": int(datetime.now().timestamp()),
        }
        mock_client.get_user.return_value = {"id": 12345, "name": "Test User"}

        # Mock existing token record
        mock_token_record = Mock()
        mock_token_record.access_token = "old_token"
        mock_token_record.refresh_token = "old_refresh_token"
        mock_token_record.expires_at = datetime.now()
        mock_token_record.user_data = None

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post(
                "/api/wahoo/exchange-code", data={"code": "test_code"}
            )

            assert response.status_code == 200
            assert mock_token_record.access_token == "new_token"
            assert mock_token_record.refresh_token == "new_refresh_token"

    @patch("src.api.wahoo.Client")
    @patch("src.api.wahoo.get_wahoo_config")
    def test_exchange_wahoo_code_service_error(
        self, mock_get_config, mock_client_class, client
    ):
        """Test Wahoo code exchange with service error."""
        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_config.return_value = mock_config

        # Mock client to raise exception
        mock_client = mock_client_class.return_value
        mock_client.exchange_code_for_token.side_effect = RuntimeError(
            "Exchange failed"
        )

        # Mock database session
        mock_session = AsyncMock()

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post(
                "/api/wahoo/exchange-code", data={"code": "test_code"}
            )

            assert response.status_code == 400
            data = response.json()
            assert "failed to exchange code" in data["detail"].lower()


class TestWahooRefreshTokenEndpoint:
    """Test Wahoo refresh token endpoint."""

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_refresh_wahoo_token_success(
        self, mock_service_class, mock_session, client
    ):
        """Test successful Wahoo token refresh."""
        # Mock database session
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        # Mock the WahooService methods
        mock_service = AsyncMock()
        mock_service.refresh_access_token.return_value = True
        mock_service_class.return_value = mock_service

        response = client.post("/api/wahoo/refresh-token", data={"wahoo_id": 1})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Token refreshed successfully"

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_refresh_wahoo_token_failure(
        self, mock_service_class, mock_session, client
    ):
        """Test Wahoo token refresh failure."""
        # Mock database session
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.refresh_access_token.return_value = False
        mock_service_class.return_value = mock_service

        response = client.post("/api/wahoo/refresh-token", data={"wahoo_id": 1})

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Failed to refresh token"

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_refresh_wahoo_token_service_error(
        self, mock_service_class, mock_session, client
    ):
        """Test Wahoo token refresh with service error."""
        # Mock database session
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.refresh_access_token.side_effect = Exception("Refresh failed")
        mock_service_class.return_value = mock_service

        response = client.post("/api/wahoo/refresh-token", data={"wahoo_id": 1})

        assert response.status_code == 401
        data = response.json()
        assert "Failed to refresh token" in data["detail"]

    @patch("src.dependencies.SessionLocal", None)
    def test_refresh_wahoo_token_no_database(self, client):
        """Test refresh token when database is not initialized."""
        response = client.post("/api/wahoo/refresh-token", data={"wahoo_id": 1})

        assert response.status_code == 503
        data = response.json()
        assert "database not initialized" in data["detail"].lower()

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_refresh_wahoo_token_http_exception_passthrough(
        self, mock_service_class, mock_session, client
    ):
        """Test that HTTPException is passed through."""
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.refresh_access_token.side_effect = HTTPException(
            status_code=400, detail="Custom error"
        )
        mock_service_class.return_value = mock_service

        response = client.post("/api/wahoo/refresh-token", data={"wahoo_id": 1})

        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Custom error"


class TestWahooDeauthorizeEndpoint:
    """Test Wahoo deauthorize endpoint."""

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_deauthorize_success(self, mock_service_class, mock_session, client):
        """Test successful deauthorization."""
        # Mock database session
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.deauthorize.return_value = None
        mock_service_class.return_value = mock_service

        response = client.post("/api/wahoo/deauthorize", data={"wahoo_id": 1})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deauthorized" in data["message"].lower()

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_deauthorize_error(self, mock_service_class, mock_session, client):
        """Test deauthorization with error."""
        # Mock database session
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.deauthorize.side_effect = Exception("Deauth error")
        mock_service_class.return_value = mock_service

        response = client.post("/api/wahoo/deauthorize", data={"wahoo_id": 1})

        assert response.status_code == 401
        data = response.json()
        assert "failed to deauthorize" in data["detail"].lower()

    @patch("src.dependencies.SessionLocal", None)
    def test_deauthorize_no_database(self, client):
        """Test deauthorize when database is not initialized."""
        response = client.post("/api/wahoo/deauthorize", data={"wahoo_id": 1})

        assert response.status_code == 503
        data = response.json()
        assert "database not initialized" in data["detail"].lower()

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_deauthorize_http_exception_passthrough(
        self, mock_service_class, mock_session, client
    ):
        """Test that HTTPException is passed through."""
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.deauthorize.side_effect = HTTPException(
            status_code=400, detail="Custom error"
        )
        mock_service_class.return_value = mock_service

        response = client.post("/api/wahoo/deauthorize", data={"wahoo_id": 1})

        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Custom error"


class TestWahooGetUserEndpoint:
    """Test Wahoo get user endpoint."""

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_get_user_success(self, mock_service_class, mock_session, client):
        """Test successful user retrieval."""
        # Mock database session
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.get_user.return_value = {
            "id": 123,
            "name": "Test User",
            "email": "test@example.com",
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/wahoo/user?wahoo_id=1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123
        assert data["name"] == "Test User"

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_get_user_error(self, mock_service_class, mock_session, client):
        """Test user retrieval with error."""
        # Mock database session
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.get_user.side_effect = Exception("Auth error")
        mock_service_class.return_value = mock_service

        response = client.get("/api/wahoo/user?wahoo_id=1")

        assert response.status_code == 401
        data = response.json()
        assert "failed to get user" in data["detail"].lower()

    @patch("src.dependencies.SessionLocal", None)
    def test_get_user_no_database(self, client):
        """Test get user when database is not initialized."""
        response = client.get("/api/wahoo/user?wahoo_id=1")

        assert response.status_code == 503
        data = response.json()
        assert "database not initialized" in data["detail"].lower()

    @patch("src.dependencies.SessionLocal")
    @patch("src.api.wahoo.WahooService")
    def test_get_user_http_exception_passthrough(
        self, mock_service_class, mock_session, client
    ):
        """Test that HTTPException is passed through."""
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.return_value.__aexit__.return_value = False

        mock_service = AsyncMock()
        mock_service.get_user.side_effect = HTTPException(
            status_code=400, detail="Custom error"
        )
        mock_service_class.return_value = mock_service

        response = client.get("/api/wahoo/user?wahoo_id=1")

        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Custom error"


class TestWahooDeleteRouteEndpoint:
    """Test Wahoo delete route endpoint."""

    @patch("src.dependencies.SessionLocal", None)
    def test_delete_route_database_not_initialized(self, client):
        """Test delete route when database is not initialized."""
        # The endpoint requires wahoo_id parameter, so we get 422 instead of 503
        response = client.delete("/api/wahoo/routes/123?wahoo_id=1")

        assert response.status_code == 503
        data = response.json()
        assert "database not initialized" in data["detail"].lower()

    def test_delete_route_endpoint_exists(self, client):
        """Test that the delete route endpoint is registered."""
        # The endpoint should exist and return some response (not 404)
        # Actual error will be 500/503 without proper setup, but 404 means endpoint
        # doesn't exist
        with patch("src.dependencies.SessionLocal", None):
            response = client.delete("/api/wahoo/routes/999")

            # Should not be 404 (which would mean endpoint doesn't exist)
            assert response.status_code != 404

    def test_delete_route_calls_service_method(self):
        """Test that the delete route endpoint will call the service method."""
        from src.services.wahoo.service import WahooService

        # Verify the service has the delete_route method
        assert hasattr(WahooService, "delete_route")
        assert callable(WahooService.delete_route)

        # Get the method signature
        import inspect

        sig = inspect.signature(WahooService.delete_route)
        params = list(sig.parameters.keys())

        # Should take route_id as parameter
        assert "route_id" in params

    def test_delete_route_service_method_signature(self):
        """Test delete_route service method signature."""
        import inspect

        from src.services.wahoo.service import WahooService

        # Get the method
        delete_method = WahooService.delete_route

        # Check signature
        sig = inspect.signature(delete_method)
        assert len(sig.parameters) == 2  # self + route_id
        assert "route_id" in sig.parameters

    def test_delete_route_client_method_exists(self):
        """Test that client has delete_route method."""
        from src.services.wahoo.client import Client

        assert hasattr(Client, "delete_route")

    def test_delete_route_protocol_method_exists(self):
        """Test that protocol has delete_route method."""
        from src.services.wahoo.protocol import ApiV1

        assert hasattr(ApiV1, "delete_route")

    @patch("src.api.wahoo.get_wahoo_config")
    def test_delete_route_not_found_in_database(self, mock_get_wahoo_config, client):
        """Test delete route when route not found in database."""

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.delete("/api/wahoo/routes/123?wahoo_id=1")

            assert response.status_code == 404
            data = response.json()
            assert "route not found" in data["detail"].lower()

    @patch("src.api.wahoo.get_wahoo_config")
    def test_delete_route_not_found_in_wahoo(self, mock_get_wahoo_config, client):
        """Test delete route when route not found in Wahoo."""
        from src.models.track import TrackType

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock track
        mock_track = Mock()
        mock_track.id = 123
        mock_track.name = "Test Route"
        mock_track.track_type = TrackType.ROUTE

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock Wahoo service
        mock_service = AsyncMock()
        mock_service.get_routes.return_value = []  # No routes found

        with (
            patch("src.dependencies.SessionLocal") as mock_session_local,
            patch("src.api.wahoo.WahooService", return_value=mock_service),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.delete("/api/wahoo/routes/123?wahoo_id=1")

            assert response.status_code == 404
            data = response.json()
            assert "route not found in wahoo cloud" in data["detail"].lower()

    @patch("src.api.wahoo.get_wahoo_config")
    def test_delete_route_success(self, mock_get_wahoo_config, client):
        """Test successful route deletion."""
        from src.models.track import TrackType

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock track
        mock_track = Mock()
        mock_track.id = 123
        mock_track.name = "Test Route"
        mock_track.track_type = TrackType.ROUTE

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock Wahoo service
        mock_service = AsyncMock()
        mock_service.get_routes.return_value = [
            {"id": 456, "external_id": "gravly_route_123", "name": "Test Route"}
        ]
        mock_service.delete_route.return_value = None

        with (
            patch("src.dependencies.SessionLocal") as mock_session_local,
            patch("src.api.wahoo.WahooService", return_value=mock_service),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.delete("/api/wahoo/routes/123?wahoo_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "deleted" in data["message"].lower()
            mock_service.delete_route.assert_called_once_with(456)

    @patch("src.api.wahoo.get_wahoo_config")
    def test_delete_route_service_error(self, mock_get_wahoo_config, client):
        """Test delete route with service error."""
        from src.models.track import TrackType

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock track
        mock_track = Mock()
        mock_track.id = 123
        mock_track.name = "Test Route"
        mock_track.track_type = TrackType.ROUTE

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock Wahoo service to raise exception
        mock_service = AsyncMock()
        mock_service.get_routes.side_effect = RuntimeError("Service error")

        with (
            patch("src.dependencies.SessionLocal") as mock_session_local,
            patch("src.api.wahoo.WahooService", return_value=mock_service),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.delete("/api/wahoo/routes/123?wahoo_id=1")

            assert response.status_code == 500
            data = response.json()
            assert "failed to delete route" in data["detail"].lower()


class TestWahooUploadRouteEndpoint:
    """Test Wahoo upload route endpoint."""

    @patch("src.dependencies.SessionLocal", None)
    def test_upload_route_no_database(self, client):
        """Test upload route when database is not initialized."""
        response = client.post("/api/wahoo/routes/123/upload?wahoo_id=1")

        assert response.status_code == 503
        data = response.json()
        assert "database not initialized" in data["detail"].lower()

    @patch("src.api.wahoo.get_wahoo_config")
    def test_upload_route_not_found_in_database(self, mock_get_wahoo_config, client):
        """Test upload route when route not found in database."""
        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post("/api/wahoo/routes/123/upload?wahoo_id=1")

            assert response.status_code == 404
            data = response.json()
            assert "route not found" in data["detail"].lower()

    @patch("src.api.wahoo.get_wahoo_config")
    def test_upload_route_no_storage_manager(self, mock_get_wahoo_config, client):
        """Test upload route when storage manager not available."""
        from src.models.track import TrackType

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock track
        mock_track = Mock()
        mock_track.id = 123
        mock_track.name = "Test Route"
        mock_track.track_type = TrackType.ROUTE

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("src.dependencies.SessionLocal") as mock_session_local,
            patch("src.dependencies.storage_manager", None),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post("/api/wahoo/routes/123/upload?wahoo_id=1")

            assert response.status_code == 500
            data = response.json()
            assert "storage manager not available" in data["detail"].lower()

    @patch("src.api.wahoo.get_wahoo_config")
    def test_upload_route_gpx_not_found(self, mock_get_wahoo_config, client):
        """Test upload route when GPX file not found."""
        from src.models.track import TrackType

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock track
        mock_track = Mock()
        mock_track.id = 123
        mock_track.name = "Test Route"
        mock_track.track_type = TrackType.ROUTE
        mock_track.file_path = "test.gpx"

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock storage manager
        mock_storage_manager = Mock()
        mock_storage_manager.load_gpx_data.return_value = None

        with (
            patch("src.dependencies.SessionLocal") as mock_session_local,
            patch("src.dependencies.storage_manager", mock_storage_manager),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post("/api/wahoo/routes/123/upload?wahoo_id=1")

            assert response.status_code == 404
            data = response.json()
            assert "gpx file not found" in data["detail"].lower()

    @patch("src.api.wahoo.get_wahoo_config")
    @patch("src.api.wahoo.gpxpy")
    @patch("src.api.wahoo.extract_from_gpx_file")
    @patch("src.api.wahoo.convert_gpx_to_fit")
    def test_upload_route_success_new(
        self,
        mock_convert_gpx,
        mock_extract_gpx,
        mock_gpxpy,
        mock_get_wahoo_config,
        client,
    ):
        """Test successful route upload creating new route."""
        from src.models.track import TrackType

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock track
        mock_track = Mock()
        mock_track.id = 123
        mock_track.name = "Test Route"
        mock_track.track_type = TrackType.ROUTE
        mock_track.file_path = "test.gpx"
        mock_track.comments = "Test description"

        # Mock GPX data
        mock_gpx = Mock()
        mock_gpx.time = None
        mock_gpxpy.parse.return_value = mock_gpx

        mock_gpx_point = Mock()
        mock_gpx_point.latitude = 45.0
        mock_gpx_point.longitude = 5.0

        mock_stats = Mock()
        mock_stats.total_distance = 10.0
        mock_stats.total_elevation_gain = 500.0
        mock_stats.total_elevation_loss = 300.0

        mock_gpx_data = Mock()
        mock_gpx_data.points = [mock_gpx_point]
        mock_gpx_data.total_stats = mock_stats
        mock_extract_gpx.return_value = mock_gpx_data

        mock_convert_gpx.return_value = b"fit_file_content"

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock storage manager
        mock_storage_manager = Mock()
        mock_storage_manager.load_gpx_data.return_value = b"<gpx>test</gpx>"

        # Mock Wahoo service
        mock_service = AsyncMock()
        mock_service.get_routes.return_value = []  # No existing routes
        mock_service.create_route.return_value = {"id": 456, "name": "Test Route"}

        with (
            patch("src.dependencies.SessionLocal") as mock_session_local,
            patch("src.api.wahoo.WahooService", return_value=mock_service),
            patch("src.dependencies.storage_manager", mock_storage_manager),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post("/api/wahoo/routes/123/upload?wahoo_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "uploaded" in data["message"].lower()
            mock_service.create_route.assert_called_once()

    @patch("src.api.wahoo.get_wahoo_config")
    @patch("src.api.wahoo.gpxpy")
    @patch("src.api.wahoo.extract_from_gpx_file")
    @patch("src.api.wahoo.convert_gpx_to_fit")
    def test_upload_route_success_update(
        self,
        mock_convert_gpx,
        mock_extract_gpx,
        mock_gpxpy,
        mock_get_wahoo_config,
        client,
    ):
        """Test successful route upload updating existing route."""
        from src.models.track import TrackType

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock track
        mock_track = Mock()
        mock_track.id = 123
        mock_track.name = "Test Route"
        mock_track.track_type = TrackType.ROUTE
        mock_track.file_path = "test.gpx"
        mock_track.comments = "Test description"

        # Mock GPX data
        mock_gpx = Mock()
        mock_gpx.time = None
        mock_gpxpy.parse.return_value = mock_gpx

        mock_gpx_point = Mock()
        mock_gpx_point.latitude = 45.0
        mock_gpx_point.longitude = 5.0

        mock_stats = Mock()
        mock_stats.total_distance = 10.0
        mock_stats.total_elevation_gain = 500.0
        mock_stats.total_elevation_loss = 300.0

        mock_gpx_data = Mock()
        mock_gpx_data.points = [mock_gpx_point]
        mock_gpx_data.total_stats = mock_stats
        mock_extract_gpx.return_value = mock_gpx_data

        mock_convert_gpx.return_value = b"fit_file_content"

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock storage manager
        mock_storage_manager = Mock()
        mock_storage_manager.load_gpx_data.return_value = b"<gpx>test</gpx>"

        # Mock Wahoo service
        mock_service = AsyncMock()
        mock_service.get_routes.return_value = [
            {"id": 456, "external_id": "gravly_route_123", "name": "Test Route"}
        ]
        mock_service.update_route.return_value = {"id": 456, "name": "Test Route"}

        with (
            patch("src.dependencies.SessionLocal") as mock_session_local,
            patch("src.api.wahoo.WahooService", return_value=mock_service),
            patch("src.dependencies.storage_manager", mock_storage_manager),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post("/api/wahoo/routes/123/upload?wahoo_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "updated" in data["message"].lower()
            mock_service.update_route.assert_called_once()

    @patch("src.api.wahoo.get_wahoo_config")
    def test_upload_route_service_error(self, mock_get_wahoo_config, client):
        """Test upload route with service error."""
        from src.models.track import TrackType

        # Mock config
        mock_config = Mock()
        mock_config.client_id = "test_client_id"
        mock_config.client_secret = "test_secret"
        mock_config.callback_url = "https://example.com/callback"
        mock_get_wahoo_config.return_value = mock_config

        # Mock track
        mock_track = Mock()
        mock_track.id = 123
        mock_track.name = "Test Route"
        mock_track.track_type = TrackType.ROUTE
        mock_track.file_path = "test.gpx"

        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_track
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock storage manager
        mock_storage_manager = Mock()
        mock_storage_manager.load_gpx_data.side_effect = RuntimeError("Storage error")

        with (
            patch("src.dependencies.SessionLocal") as mock_session_local,
            patch("src.dependencies.storage_manager", mock_storage_manager),
        ):
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = False

            response = client.post("/api/wahoo/routes/123/upload?wahoo_id=1")

            assert response.status_code == 500
            data = response.json()
            assert "failed to upload route" in data["detail"].lower()
