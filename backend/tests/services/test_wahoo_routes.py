"""Tests for Wahoo route creation and update functionality."""

from unittest.mock import patch

import pytest

from backend.src.services.wahoo.client import Client
from backend.src.services.wahoo.protocol import ApiV1
from backend.src.services.wahoo.service import WahooService
from backend.src.utils.config import WahooConfig


class TestWahooProtocolRoutes:
    """Test Wahoo protocol route methods."""

    def test_create_route_with_data_parameter(self):
        """Test create_route uses data parameter in _request."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"id": 123}

            result = protocol.create_route(
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

            assert result == {"id": 123}
            mock_request.assert_called_once()

            # Verify that data parameter was passed
            call_args = mock_request.call_args
            # call_args is a tuple: (args_tuple, kwargs_dict)
            # First arg is the URL
            assert len(call_args[0]) > 0
            assert "routes" in call_args[0][0]
            assert call_args[1]["method"] == "POST"
            assert "data" in call_args[1]

    def test_update_route_with_data_parameter(self):
        """Test update_route uses data parameter in _request."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"id": 456}

            result = protocol.update_route(
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
            mock_request.assert_called_once()

            # Verify that data parameter was passed
            call_args = mock_request.call_args
            # First arg is the URL
            assert len(call_args[0]) > 0
            assert "routes/456" in call_args[0][0]
            assert call_args[1]["method"] == "PUT"
            assert "data" in call_args[1]


class TestWahooClientRoutes:
    """Test Wahoo client route methods."""

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
            mock_create.assert_called_once_with(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Test Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
                description="",
                external_id=None,
                provider_updated_at=None,
                workout_type_family_id=0,
            )

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
            mock_update.assert_called_once_with(
                route_id=456,
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Test Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
                description="",
                provider_updated_at=None,
                workout_type_family_id=0,
            )


class TestWahooServiceRoutes:
    """Test Wahoo service route methods."""

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

    def test_create_route_success(self, service):
        """Test successful route creation."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
        ):
            mock_create.return_value = {"id": 123, "name": "Test Route"}

            result = service.create_route(
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

    def test_create_route_unauthorized(self, service):
        """Test route creation with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            from backend.src.services.wahoo.exceptions import WahooAccessUnauthorized

            mock_create.side_effect = ValueError("401 Unauthorized")

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

    def test_update_route_success(self, service):
        """Test successful route update."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
        ):
            mock_update.return_value = {"id": 456, "name": "Updated Route"}

            result = service.update_route(
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

            assert result == {"id": 456, "name": "Updated Route"}
            mock_update.assert_called_once()

    def test_update_route_unauthorized(self, service):
        """Test route update with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            from backend.src.services.wahoo.exceptions import WahooAccessUnauthorized

            mock_update.side_effect = ValueError("401 Unauthorized")

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
