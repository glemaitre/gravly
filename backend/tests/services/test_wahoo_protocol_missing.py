"""Tests for missing coverage in Wahoo protocol."""

from unittest.mock import Mock, patch

import pytest
from requests import Session

from backend.src.services.wahoo.protocol import ApiV1


class TestWahooProtocolMissing:
    """Test missing protocol coverage."""

    def test_request_logs_authorization_header_truncated(self):
        """Test that authorization headers are logged truncated."""
        protocol = ApiV1(access_token="test_token")

        # Mock the session
        mock_session = Mock(spec=Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_session.get.return_value = mock_response

        protocol.rsession = mock_session

        long_auth_value = "Bearer " + "x" * 50  # Long authorization header

        with patch.object(protocol.log, "info") as mock_log:
            protocol._request(
                "test/endpoint",
                headers={"Authorization": long_auth_value},
                method="GET",
            )

            # Check that the log was called with a truncated version
            log_calls = [str(call) for call in mock_log.call_args_list]
            assert any("Authorization" in str(call) for call in log_calls)
            # Check that it was truncated (ends with ...)
            assert any("xxx..." in str(call) for call in log_calls)

    def test_request_logs_non_authorization_headers(self):
        """Test that non-authorization headers are logged normally."""
        protocol = ApiV1(access_token="test_token")

        # Mock the session
        mock_session = Mock(spec=Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_session.post.return_value = mock_response

        protocol.rsession = mock_session

        with patch.object(protocol.log, "info") as mock_log:
            protocol._request(
                "test/endpoint",
                headers={"Content-Type": "application/json", "X-Custom": "value"},
                method="POST",
            )

            # Check that non-authorization headers were logged
            log_calls_str = str(mock_log.call_args_list)
            assert "Content-Type" in log_calls_str or "X-Custom" in log_calls_str

    def test_handle_protocol_error_with_error_field(self):
        """Test _handle_protocol_error with error field in response."""
        protocol = ApiV1()

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.json.return_value = {
            "error": "Invalid parameter",
            "message": "Some message",
        }

        with pytest.raises(ValueError, match="400 Bad Request"):
            protocol._handle_protocol_error(mock_response)

    def test_get_user_without_access_token(self):
        """Test get_user raises error without access token."""
        protocol = ApiV1(access_token=None)

        with pytest.raises(ValueError, match="No access token available"):
            protocol.get_user()

    def test_get_user_success(self):
        """Test successful get_user call."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"id": 123, "name": "Test User"}

            result = protocol.get_user()

            assert result == {"id": 123, "name": "Test User"}
            mock_request.assert_called_once()

    def test_get_route_without_access_token(self):
        """Test get_route raises error without access token."""
        protocol = ApiV1(access_token=None)

        with pytest.raises(ValueError, match="No access token available"):
            protocol.get_route(123)

    def test_get_route_success(self):
        """Test successful get_route call."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"id": 123, "name": "Test Route"}

            result = protocol.get_route(123)

            assert result == {"id": 123, "name": "Test Route"}
            mock_request.assert_called_once()

    def test_get_routes_without_access_token(self):
        """Test get_routes raises error without access token."""
        protocol = ApiV1(access_token=None)

        with pytest.raises(ValueError, match="No access token available"):
            protocol.get_routes()

    def test_get_routes_success(self):
        """Test successful get_routes call."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = [{"id": 1}, {"id": 2}]

            result = protocol.get_routes()

            assert result == [{"id": 1}, {"id": 2}]
            mock_request.assert_called_once()

    def test_update_route_without_access_token(self):
        """Test update_route raises error without access token."""
        protocol = ApiV1(access_token=None)

        with pytest.raises(ValueError, match="No access token available"):
            protocol.update_route(
                route_id=123,
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Test Route",
                start_lat=45.0,
                start_lng=5.0,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

    def test_update_route_with_provider_updated_at(self):
        """Test update_route includes provider_updated_at when provided."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"id": 123}

            result = protocol.update_route(
                route_id=123,
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Test Route",
                start_lat=45.0,
                start_lng=5.0,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
                provider_updated_at="2024-01-01T00:00:00",
            )

            assert result == {"id": 123}
            call_args = mock_request.call_args
            # Check that data was passed
            assert "data" in call_args[1]

            # Verify provider_updated_at was included in data
            data_dict = call_args[1]["data"]
            assert "route[provider_updated_at]" in data_dict
            assert data_dict["route[provider_updated_at]"] == "2024-01-01T00:00:00"

    def test_update_route_without_provider_updated_at(self):
        """Test update_route without provider_updated_at."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"id": 123}

            result = protocol.update_route(
                route_id=123,
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Test Route",
                start_lat=45.0,
                start_lng=5.0,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 123}

    def test_deauthorize_without_access_token(self):
        """Test deauthorize raises error without access token."""
        protocol = ApiV1(access_token=None)

        with pytest.raises(ValueError, match="No access token available"):
            protocol.deauthorize()

    def test_deauthorize_success(self):
        """Test successful deauthorize call."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {}

            protocol.deauthorize()

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # Check it was DELETE method
            assert call_args[1]["method"] == "DELETE"
            # Check it uses permissions endpoint
            assert "permissions" in call_args[0][0]

    def test_get_method_with_params(self):
        """Test generic get method with parameters."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"result": "test"}

            result = protocol.get("test/endpoint", param1="value1", param2="value2")

            assert result == {"result": "test"}
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # Check params were passed
            assert "params" in call_args[1]
            assert call_args[1]["params"]["param1"] == "value1"

    def test_post_method_with_files(self):
        """Test generic post method with files."""
        protocol = ApiV1(access_token="test_token")

        mock_file = Mock()
        files = {"file": ("test.txt", mock_file, "text/plain")}

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"result": "uploaded"}

            result = protocol.post("upload", files=files)

            assert result == {"result": "uploaded"}
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # Check files were passed
            assert "files" in call_args[1]

    def test_put_method(self):
        """Test generic put method."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"result": "updated"}

            result = protocol.put("test/endpoint", param1="value1")

            assert result == {"result": "updated"}
            mock_request.assert_called_once()

    def test_delete_method(self):
        """Test generic delete method."""
        protocol = ApiV1(access_token="test_token")

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {}

            result = protocol.delete("test/endpoint")

            assert result == {}
            mock_request.assert_called_once()
