"""Tests for missing coverage in Wahoo client."""

from unittest.mock import patch

import pytest

from backend.src.services.wahoo.client import Client


class TestWahooClientMissing:
    """Test missing client coverage."""

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
            mock_create.side_effect = ValueError(
                "A route with an external_id already exists"
            )

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

    def test_upload_route_without_external_id(self):
        """Test upload_route without external_id parameter."""
        client = Client()

        with patch.object(client, "create_route") as mock_create:
            mock_create.return_value = {"id": 789, "name": "New Route"}

            result = client.upload_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="New Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 789, "name": "New Route"}

    def test_upload_route_with_all_parameters(self):
        """Test upload_route with all optional parameters."""
        client = Client()

        with patch.object(client, "create_route") as mock_create:
            mock_create.return_value = {"id": 999, "name": "Complete Route"}

            result = client.upload_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="complete.fit",
                route_name="Complete Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
                description="A complete test route",
                external_id="complete_123",
                provider_updated_at="2024-01-01T00:00:00",
                workout_type_family_id=1,
            )

            assert result == {"id": 999, "name": "Complete Route"}
            # Verify all parameters were passed
            mock_create.assert_called_once_with(
                route_file="data:application/vnd.fit;base64,test",
                filename="complete.fit",
                route_name="Complete Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
                description="A complete test route",
                external_id="complete_123",
                provider_updated_at="2024-01-01T00:00:00",
                workout_type_family_id=1,
            )
