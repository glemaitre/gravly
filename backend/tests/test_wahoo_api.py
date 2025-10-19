"""Tests for Wahoo API endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestWahooCallback:
    """Test Wahoo callback endpoint."""

    def test_wahoo_callback_success(self, client):
        """Test successful Wahoo callback with authorization code."""
        test_code = "test_authorization_code_123"

        with patch("builtins.print") as mock_print:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Wahoo authorization code received successfully"
        assert data["code"] == test_code
        assert data["status"] == "success"

        # Verify that the code was printed
        mock_print.assert_called_once_with(f"Wahoo authorization code: {test_code}")

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

        with patch("builtins.print") as mock_print:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        # The test client may URL decode the code, so we check that it contains
        # the expected parts
        assert "test_code_with_special_chars" in data["code"]
        # The print call may also be URL decoded, so we check the call was made
        mock_print.assert_called_once()
        # Verify the call contains the expected text
        call_args = mock_print.call_args[0][0]
        assert "Wahoo authorization code:" in call_args
        assert "test_code_with_special_chars" in call_args

    def test_wahoo_callback_long_code(self, client):
        """Test Wahoo callback with a very long authorization code."""
        test_code = "a" * 1000  # Very long code

        with patch("builtins.print") as mock_print:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code
        mock_print.assert_called_once_with(f"Wahoo authorization code: {test_code}")

    @patch("builtins.print")
    def test_wahoo_callback_logging(self, mock_print, client):
        """Test that Wahoo callback logs the received code."""
        test_code = "logging_test_code"

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get(f"/api/wahoo/callback?code={test_code}")

        assert response.status_code == 200
        # Verify that info logging was called
        mock_logger.info.assert_called_once_with(
            f"Received Wahoo authorization code: {test_code}"
        )
        # Verify that print was called
        mock_print.assert_called_once_with(f"Wahoo authorization code: {test_code}")

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


class TestWahooAuthorizationUrl:
    """Test Wahoo authorization URL endpoint."""

    @patch("src.api.wahoo.get_wahoo_service")
    def test_get_authorization_url_success(self, mock_get_service, client):
        """Test successful authorization URL generation."""
        # Mock the WahooService instance
        mock_wahoo_service = mock_get_service.return_value
        expected_auth_url = "https://api.wahooligan.com/oauth/authorize?client_id=test&redirect_uri=test&response_type=code&scope=routes_write+user_read&state=wahoo_auth"
        mock_wahoo_service.get_authorization_url.return_value = expected_auth_url

        response = client.get("/api/wahoo/authorization-url")

        assert response.status_code == 200
        data = response.json()
        assert data["authorization_url"] == expected_auth_url
        assert data["status"] == "success"

        # Verify that the service was called without parameters
        mock_wahoo_service.get_authorization_url.assert_called_once_with()

    @patch("src.api.wahoo.get_wahoo_service")
    def test_get_authorization_url_service_error(self, mock_get_service, client):
        """Test authorization URL generation when service raises an exception."""
        # Mock the WahooService to raise an exception
        mock_wahoo_service = mock_get_service.return_value
        mock_wahoo_service.get_authorization_url.side_effect = Exception(
            "Service error"
        )

        response = client.get("/api/wahoo/authorization-url")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate authorization URL" in data["detail"]
        assert "Service error" in data["detail"]

    @patch("src.api.wahoo.get_wahoo_service")
    def test_get_authorization_url_service_initialization_error(
        self, mock_get_service, client
    ):
        """Test authorization URL generation when service initialization fails."""
        # Mock the service to raise an exception during initialization
        mock_get_service.side_effect = Exception("Service initialization error")

        response = client.get("/api/wahoo/authorization-url")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate authorization URL" in data["detail"]
        assert "Service initialization error" in data["detail"]

    @patch("src.api.wahoo.get_wahoo_service")
    def test_get_authorization_url_logging(self, mock_get_service, client):
        """Test that authorization URL generation logs correctly."""
        # Mock the WahooService instance
        mock_wahoo_service = mock_get_service.return_value
        expected_auth_url = "https://api.wahooligan.com/oauth/authorize?test=123"
        mock_wahoo_service.get_authorization_url.return_value = expected_auth_url

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get("/api/wahoo/authorization-url")

        assert response.status_code == 200
        # Verify that info logging was called
        mock_logger.info.assert_called_once_with("Generated Wahoo authorization URL")

    @patch("src.api.wahoo.get_wahoo_service")
    def test_get_authorization_url_response_format(self, mock_get_service, client):
        """Test that authorization URL endpoint returns the expected response format."""
        # Mock the WahooService instance
        mock_wahoo_service = mock_get_service.return_value
        expected_auth_url = "https://api.wahooligan.com/oauth/authorize?test=123"
        mock_wahoo_service.get_authorization_url.return_value = expected_auth_url

        response = client.get("/api/wahoo/authorization-url")

        assert response.status_code == 200
        data = response.json()

        # Check that all expected fields are present
        assert "authorization_url" in data
        assert "status" in data

        # Check field types
        assert isinstance(data["authorization_url"], str)
        assert isinstance(data["status"], str)

        # Check field values
        assert data["authorization_url"] == expected_auth_url
        assert data["status"] == "success"
