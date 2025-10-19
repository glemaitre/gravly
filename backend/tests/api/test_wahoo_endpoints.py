"""Unit tests for Wahoo API endpoints."""

from unittest.mock import patch

import pytest
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

        # Verify that the code was logged
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

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
        # Verify that the code was logged (check that logging was called with the actual
        # received code)
        mock_logger.info.assert_called_once()
        logged_message = mock_logger.info.call_args[0][0]
        assert "Received Wahoo authorization code:" in logged_message
        assert data["code"] in logged_message

    def test_wahoo_callback_long_code(self, client):
        """Test Wahoo callback with a very long authorization code."""
        test_code = "a" * 1000  # Very long code

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

    def test_wahoo_callback_logging(self, client):
        """Test that Wahoo callback logs the received code."""
        test_code = "logging_test_code"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        # Verify that info logging was called
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

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
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

    def test_wahoo_callback_numeric_code(self, client):
        """Test Wahoo callback with numeric authorization code."""
        test_code = "123456789"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

    def test_wahoo_callback_whitespace_code(self, client):
        """Test Wahoo callback with whitespace in authorization code."""
        test_code = "  test_code_with_spaces  "

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

    def test_wahoo_callback_multiple_parameters(self, client):
        """Test Wahoo callback with additional parameters."""
        test_code = "test_code_123"
        state = "test_state"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}&state={state}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

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


class TestWahooServiceIntegration:
    """Test integration between Wahoo API endpoints and service."""

    def test_wahoo_callback_basic_functionality(self, client):
        """Test Wahoo callback basic functionality."""
        test_code = "service_integration_test"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code

        # Verify logging was called (current implementation)
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

    def test_wahoo_callback_future_token_exchange(self, client):
        """Test how Wahoo callback might work with token exchange in the future."""
        test_code = "future_token_exchange_test"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code

        # Verify current behavior
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )

        # Note: The service is not currently used in the callback endpoint
        # but this test shows how token exchange could be integrated in the future


class TestWahooAuthUrlEndpoint:
    """Test Wahoo auth URL endpoint."""

    @patch("src.api.wahoo.get_wahoo_service")
    @patch("src.dependencies.server_config")
    def test_get_wahoo_auth_url_success(
        self, mock_server_config, mock_get_service, client
    ):
        """Test successful Wahoo auth URL generation."""
        # Mock the service and server config
        mock_service = mock_get_service.return_value
        mock_service.get_authorization_url.return_value = (
            "https://api.wahooligan.com/oauth/authorize?client_id=test"
        )
        mock_server_config.frontend_url = "http://localhost:3000"

        response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert (
            data["auth_url"]
            == "https://api.wahooligan.com/oauth/authorize?client_id=test"
        )

    @patch("src.api.wahoo.get_wahoo_service")
    @patch("src.dependencies.server_config")
    def test_get_wahoo_auth_url_with_state(
        self, mock_server_config, mock_get_service, client
    ):
        """Test Wahoo auth URL generation with custom state."""
        mock_service = mock_get_service.return_value
        mock_service.get_authorization_url.return_value = "https://api.wahooligan.com/oauth/authorize?client_id=test&state=custom_state"
        mock_server_config.frontend_url = "http://localhost:3000"

        response = client.get("/api/wahoo/auth-url?state=custom_state")

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        mock_service.get_authorization_url.assert_called_once_with("custom_state")

    @patch("src.api.wahoo.get_wahoo_service")
    def test_get_wahoo_auth_url_service_error(self, mock_get_service, client):
        """Test Wahoo auth URL generation with service error."""
        mock_get_service.side_effect = Exception("Service error")

        response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate authorization URL" in data["detail"]


class TestWahooExchangeCodeEndpoint:
    """Test Wahoo exchange code endpoint."""

    @patch("src.api.wahoo.get_wahoo_service")
    def test_exchange_wahoo_code_success(self, mock_get_service, client):
        """Test successful Wahoo code exchange."""
        mock_service = mock_get_service.return_value
        mock_service.exchange_code_for_token.return_value = {
            "access_token": "test_access_token",
            "expires_at": 1234567890,
        }

        response = client.post("/api/wahoo/exchange-code", data={"code": "test_code"})

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_access_token"
        assert data["expires_at"] == 1234567890
        mock_service.exchange_code_for_token.assert_called_once_with("test_code")

    @patch("src.api.wahoo.get_wahoo_service")
    def test_exchange_wahoo_code_missing_code(self, mock_get_service, client):
        """Test Wahoo code exchange without code."""
        response = client.post("/api/wahoo/exchange-code")

        assert response.status_code == 422  # Validation error

    @patch("src.api.wahoo.get_wahoo_service")
    def test_exchange_wahoo_code_service_error(self, mock_get_service, client):
        """Test Wahoo code exchange with service error."""
        mock_service = mock_get_service.return_value
        mock_service.exchange_code_for_token.side_effect = Exception("Exchange failed")

        response = client.post("/api/wahoo/exchange-code", data={"code": "test_code"})

        assert response.status_code == 400
        data = response.json()
        assert "Failed to exchange code" in data["detail"]


class TestWahooRefreshTokenEndpoint:
    """Test Wahoo refresh token endpoint."""

    @patch("src.api.wahoo.get_wahoo_service")
    def test_refresh_wahoo_token_success(self, mock_get_service, client):
        """Test successful Wahoo token refresh."""
        mock_service = mock_get_service.return_value
        mock_service.refresh_access_token.return_value = True

        response = client.post("/api/wahoo/refresh-token")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Token refreshed successfully"
        mock_service.refresh_access_token.assert_called_once()

    @patch("src.api.wahoo.get_wahoo_service")
    def test_refresh_wahoo_token_failure(self, mock_get_service, client):
        """Test Wahoo token refresh failure."""
        mock_service = mock_get_service.return_value
        mock_service.refresh_access_token.return_value = False

        response = client.post("/api/wahoo/refresh-token")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Failed to refresh token"

    @patch("src.api.wahoo.get_wahoo_service")
    def test_refresh_wahoo_token_service_error(self, mock_get_service, client):
        """Test Wahoo token refresh with service error."""
        mock_service = mock_get_service.return_value
        mock_service.refresh_access_token.side_effect = Exception("Refresh failed")

        response = client.post("/api/wahoo/refresh-token")

        assert response.status_code == 401
        data = response.json()
        assert "Failed to refresh token" in data["detail"]
