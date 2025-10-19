"""Tests for Wahoo API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from ..main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestWahooCallback:
    """Test Wahoo callback endpoint."""

    def test_wahoo_callback_success(self, client):
        """Test successful Wahoo callback with authorization code."""
        test_code = "test_authorization_code_123"
        
        with patch('builtins.print') as mock_print:
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
        
        with patch('builtins.print') as mock_print:
            response = client.get(f"/api/wahoo/callback?code={test_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code
        mock_print.assert_called_once_with(f"Wahoo authorization code: {test_code}")

    def test_wahoo_callback_long_code(self, client):
        """Test Wahoo callback with a very long authorization code."""
        test_code = "a" * 1000  # Very long code
        
        with patch('builtins.print') as mock_print:
            response = client.get(f"/api/wahoo/callback?code={test_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_code
        mock_print.assert_called_once_with(f"Wahoo authorization code: {test_code}")

    @patch('builtins.print')
    def test_wahoo_callback_logging(self, mock_print, client):
        """Test that Wahoo callback logs the received code."""
        test_code = "logging_test_code"
        
        with patch('logging.getLogger') as mock_logger:
            mock_log_instance = MagicMock()
            mock_logger.return_value = mock_log_instance
            
            response = client.get(f"/api/wahoo/callback?code={test_code}")
        
        assert response.status_code == 200
        # Verify that info logging was called
        mock_log_instance.info.assert_called_once_with(f"Received Wahoo authorization code: {test_code}")
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
