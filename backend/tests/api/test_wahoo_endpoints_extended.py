"""Extended tests for Wahoo API endpoints to cover missing lines."""

from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from src.main import app


class TestWahooEndpointsExtended:
    """Extended tests for Wahoo API endpoints."""

    def test_wahoo_callback_general_exception(self):
        """Test Wahoo callback endpoint with general exception handling."""
        client = TestClient(app)

        with patch("src.api.wahoo.logger") as mock_logger:
            # Mock logger.info to raise an exception
            mock_logger.info.side_effect = Exception("Unexpected error")

            response = client.get("/api/wahoo/callback?code=test_code")

            assert response.status_code == 500
            data = response.json()
            assert "Failed to handle callback: Unexpected error" in data["detail"]

    def test_wahoo_callback_http_exception_passthrough(self):
        """Test that HTTPException is passed through without modification."""
        client = TestClient(app)

        with patch("src.api.wahoo.logger") as mock_logger:
            # Mock logger.info to raise an HTTPException
            mock_logger.info.side_effect = HTTPException(
                status_code=400, detail="Bad request"
            )

            response = client.get("/api/wahoo/callback?code=test_code")

            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "Bad request"
