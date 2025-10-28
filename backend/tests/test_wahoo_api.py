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


class TestWahooAuthorizationUrl:
    """Test Wahoo authorization URL endpoint."""

    @patch("src.api.wahoo.Client")
    def test_get_authorization_url_success(self, mock_client_class, client):
        """Test successful authorization URL generation."""
        # Mock the Client
        mock_client = mock_client_class.return_value
        expected_auth_url = "https://api.wahooligan.com/oauth/authorize?client_id=test&redirect_uri=test&response_type=code&scope=routes_write+user_read&state=wahoo_auth"
        mock_client.authorization_url.return_value = expected_auth_url

        response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 200
        data = response.json()
        assert data["auth_url"] == expected_auth_url

    @patch("src.api.wahoo.Client")
    def test_get_authorization_url_service_error(self, mock_client_class, client):
        """Test authorization URL generation when service raises an exception."""
        # Mock the Client to raise an exception
        mock_client = mock_client_class.return_value
        mock_client.authorization_url.side_effect = Exception("Service error")

        response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate authorization URL" in data["detail"]
        assert "Service error" in data["detail"]

    @patch("src.api.wahoo.Client")
    def test_get_authorization_url_service_initialization_error(
        self, mock_client_class, client
    ):
        """Test authorization URL generation when service initialization fails."""
        # Mock the client to raise an exception during initialization
        mock_client_class.side_effect = Exception("Service initialization error")

        response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate authorization URL" in data["detail"]
        assert "Service initialization error" in data["detail"]

    @patch("src.api.wahoo.Client")
    def test_get_authorization_url_logging(self, mock_client_class, client):
        """Test that authorization URL generation logs correctly."""
        # Mock the Client
        mock_client = mock_client_class.return_value
        expected_auth_url = "https://api.wahooligan.com/oauth/authorize?test=123"
        mock_client.authorization_url.return_value = expected_auth_url

        with patch("src.api.wahoo.logger") as mock_logger:
            response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 200
        # Verify that info logging was called
        mock_logger.info.assert_called_once_with("Generated Wahoo authorization URL")

    @patch("src.api.wahoo.Client")
    def test_get_authorization_url_response_format(self, mock_client_class, client):
        """Test that authorization URL endpoint returns the expected response format."""
        # Mock the Client
        mock_client = mock_client_class.return_value
        expected_auth_url = "https://api.wahooligan.com/oauth/authorize?test=123"
        mock_client.authorization_url.return_value = expected_auth_url

        response = client.get("/api/wahoo/auth-url")

        assert response.status_code == 200
        data = response.json()

        # Check that all expected fields are present
        assert "auth_url" in data

        # Check field types
        assert isinstance(data["auth_url"], str)

        # Check field values
        assert data["auth_url"] == expected_auth_url
