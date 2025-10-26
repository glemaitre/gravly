"""Tests for missing coverage in Wahoo service."""

from unittest.mock import patch

import pytest

from backend.src.services.wahoo.exceptions import WahooAccessUnauthorized
from backend.src.services.wahoo.service import WahooService
from backend.src.utils.config import WahooConfig


class TestWahooServiceMissing:
    """Test missing service coverage."""

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

    def test_get_user_unauthorized_error(self, service):
        """Test get_user with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_user") as mock_get_user,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_user.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                service.get_user()

    def test_get_user_other_value_error(self, service):
        """Test get_user with other ValueError."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_user") as mock_get_user,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_user.side_effect = ValueError("Network error")

            with pytest.raises(ValueError, match="Network error"):
                service.get_user()

    def test_get_user_exception(self, service):
        """Test get_user with general exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_user") as mock_get_user,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_user.side_effect = Exception("Unexpected error")

            with pytest.raises(Exception, match="Unexpected error"):
                service.get_user()

    def test_get_route_unauthorized_error(self, service):
        """Test get_route with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_route") as mock_get_route,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_route.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                service.get_route(123)

    def test_get_route_other_value_error(self, service):
        """Test get_route with other ValueError."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_route") as mock_get_route,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_route.side_effect = ValueError("Not found")

            with pytest.raises(ValueError, match="Not found"):
                service.get_route(999)

    def test_get_route_exception(self, service):
        """Test get_route with general exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_route") as mock_get_route,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_route.side_effect = Exception("Unexpected error")

            with pytest.raises(Exception, match="Unexpected error"):
                service.get_route(456)

    def test_get_routes_unauthorized_error(self, service):
        """Test get_routes with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_routes") as mock_get_routes,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_routes.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                service.get_routes()

    def test_get_routes_other_value_error(self, service):
        """Test get_routes with other ValueError."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_routes") as mock_get_routes,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_routes.side_effect = ValueError("Network error")

            with pytest.raises(ValueError, match="Network error"):
                service.get_routes()

    def test_get_routes_exception(self, service):
        """Test get_routes with general exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_routes") as mock_get_routes,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_get_routes.side_effect = Exception("Unexpected error")

            with pytest.raises(Exception, match="Unexpected error"):
                service.get_routes()

    def test_create_route_value_error_other(self, service):
        """Test create_route with ValueError that is not unauthorized."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("Invalid route data")

            with pytest.raises(ValueError, match="Invalid route data"):
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

    def test_create_route_exception(self, service):
        """Test create_route with non-ValueError exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
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

    def test_update_route_value_error_other(self, service):
        """Test update_route with ValueError that is not unauthorized."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_update.side_effect = ValueError("Route not found")

            with pytest.raises(ValueError, match="Route not found"):
                service.update_route(
                    route_id=999,
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Updated Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_update_route_exception(self, service):
        """Test update_route with non-ValueError exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_update.side_effect = Exception("Network error")

            with pytest.raises(Exception, match="Network error"):
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

    def test_upload_route_success(self, service):
        """Test upload_route successful creation."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.return_value = {"id": 789, "name": "Uploaded Route"}

            result = service.upload_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Uploaded Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
                external_id="test_789",
            )

            assert result == {"id": 789, "name": "Uploaded Route"}

    def test_upload_route_unauthorized_error(self, service):
        """Test upload_route with unauthorized error."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("401 Unauthorized")

            with pytest.raises(WahooAccessUnauthorized):
                service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_upload_route_already_exists(self, service):
        """Test upload_route when route already exists."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("Route already exists")

            with pytest.raises(ValueError, match="Update not implemented yet"):
                service.upload_route(
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

    def test_upload_route_other_value_error(self, service):
        """Test upload_route with other ValueError."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = ValueError("Invalid route data")

            with pytest.raises(ValueError, match="Invalid route data"):
                service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_upload_route_exception(self, service):
        """Test upload_route with general exception."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service, "create_route") as mock_create,
            patch("backend.src.services.wahoo.service.logger"),
        ):
            mock_create.side_effect = Exception("Network timeout")

            with pytest.raises(Exception, match="Network timeout"):
                service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Test Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    def test_get_user_success(self, service):
        """Test get_user successful execution."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {"id": 123, "name": "Test User"}

            result = service.get_user()

            assert result == {"id": 123, "name": "Test User"}

    def test_get_route_success(self, service):
        """Test get_route successful execution."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_route") as mock_get_route,
        ):
            mock_get_route.return_value = {"id": 456, "name": "Test Route"}

            result = service.get_route(456)

            assert result == {"id": 456, "name": "Test Route"}

    def test_get_routes_success(self, service):
        """Test get_routes successful execution."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "get_routes") as mock_get_routes,
        ):
            mock_get_routes.return_value = [
                {"id": 1, "name": "Route 1"},
                {"id": 2, "name": "Route 2"},
            ]

            result = service.get_routes()

            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 2

    def test_create_route_success_execution(self, service):
        """Test create_route successful execution (not just errors)."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "create_route") as mock_create,
        ):
            mock_create.return_value = {"id": 111, "name": "Success Route"}

            result = service.create_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Success Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 111, "name": "Success Route"}

    def test_update_route_success_execution(self, service):
        """Test update_route successful execution (not just errors)."""
        with (
            patch.object(service, "_ensure_authenticated"),
            patch.object(service.client, "update_route") as mock_update,
        ):
            mock_update.return_value = {"id": 222, "name": "Updated Route"}

            result = service.update_route(
                route_id=222,
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Updated Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 222, "name": "Updated Route"}
