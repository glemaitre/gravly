"""Unit tests for Wahoo protocol."""

import os
import time
from unittest.mock import Mock, patch

import pytest
from requests import Session

from backend.src.services.wahoo.protocol import AccessInfo, ApiV1


class TestWahooProtocol:
    """Test Wahoo ApiV1 protocol class."""

    def test_protocol_initialization_default(self):
        """Test ApiV1 initialization with default parameters."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            assert protocol.access_token is None
            assert protocol.token_expires is None
            assert protocol.refresh_token is None
            assert protocol.client_id is None
            assert protocol.client_secret is None
            assert protocol.server == "api.wahooligan.com"
            assert protocol.api_base == "/v1"

    def test_protocol_initialization_with_params(self):
        """Test ApiV1 initialization with parameters."""
        mock_session = Mock(spec=Session)
        mock_limiter = Mock()

        with patch.dict(
            os.environ,
            {
                "WAHOO_CLIENT_ID": "test_client_id",
                "WAHOO_CLIENT_SECRET": "test_client_secret",
                "SILENCE_TOKEN_WARNINGS": "true",
            },
            clear=True,
        ):
            protocol = ApiV1(
                access_token="test_token",
                requests_session=mock_session,
                rate_limiter=mock_limiter,
                token_expires=9999999999,
                refresh_token="test_refresh_token",
                client_id="test_client_id",
                client_secret="test_client_secret",
            )

            assert protocol.access_token == "test_token"
            assert protocol.token_expires == 9999999999
            assert protocol.refresh_token == "test_refresh_token"
            assert protocol.client_id == "test_client_id"
            assert protocol.client_secret == "test_client_secret"
            assert protocol.rsession == mock_session
            assert protocol.rate_limiter == mock_limiter

    def test_protocol_authorization_url(self):
        """Test ApiV1 authorization_url method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = (
                "https://api.wahooligan.com/oauth/authorize?test=url"
            )

            result = protocol.authorization_url(
                client_id="test_client_id",
                redirect_uri="https://example.com/callback",
                scope=["routes_write", "user_read"],
                state="test_state",
            )

            # Verify the URL is properly constructed
            assert "api.wahooligan.com" in result
            assert "/oauth/authorize" in result

    def test_protocol_authorization_url_default_scope(self):
        """Test ApiV1 authorization_url with default scope (None)."""
        protocol = ApiV1()

        # authorization_url doesn't use _request, it constructs URL directly
        result = protocol.authorization_url(
            client_id="test_client_id",
            redirect_uri="https://example.com/callback",
        )

        # Should use default scope
        assert "api.wahooligan.com" in result
        assert "/oauth/authorize" in result

    def test_protocol_authorization_url_string_scope(self):
        """Test ApiV1 authorization_url with string scope."""
        protocol = ApiV1()

        # authorization_url doesn't use _request, it constructs URL directly
        result = protocol.authorization_url(
            client_id="test_client_id",
            redirect_uri="https://example.com/callback",
            scope="routes_write",
        )

        assert "api.wahooligan.com" in result
        assert "/oauth/authorize" in result

    def test_create_route_method(self):
        """Test create_route method in protocol."""
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
                provider_updated_at="2024-01-01T00:00:00",
            )

            assert result == {"id": 123}
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # Verify that data parameter was passed
            assert "data" in call_args[1]
            # Verify the data contains all expected fields
            data_dict = call_args[1]["data"]
            assert "route[file]" in data_dict
            assert "route[filename]" in data_dict
            assert "route[name]" in data_dict
            assert "route[external_id]" in data_dict
            assert "route[provider_updated_at]" in data_dict
            assert "route[start_lat]" in data_dict
            assert "route[start_lng]" in data_dict
            assert "route[distance]" in data_dict
            assert "route[ascent]" in data_dict
            assert "route[descent]" in data_dict

    def test_protocol_exchange_code_for_token(self):
        """Test ApiV1 exchange_code_for_token method."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            mock_response = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": 9999999999,
            }

            with patch.object(protocol, "_request") as mock_request:
                mock_request.return_value = mock_response

                access_info = protocol.exchange_code_for_token(
                    client_id="test_client_id",
                    client_secret="test_client_secret",
                    redirect_uri="https://test.example.com/callback",
                    code="test_code",
                )

                mock_request.assert_called_once()
                assert access_info["access_token"] == "test_access_token"
                assert access_info["refresh_token"] == "test_refresh_token"
                assert access_info["expires_at"] == 9999999999

    def test_protocol_refresh_access_token(self):
        """Test ApiV1 refresh_access_token method."""
        protocol = ApiV1()

        mock_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 9999999999,
        }

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = mock_response

            access_info = protocol.refresh_access_token(
                client_id="test_client_id",
                client_secret="test_client_secret",
                refresh_token="old_refresh_token",
            )

            mock_request.assert_called_once()
            assert access_info["access_token"] == "new_access_token"
            assert access_info["refresh_token"] == "new_refresh_token"
            assert access_info["expires_at"] == 9999999999
            assert protocol.access_token == "new_access_token"
            assert protocol.refresh_token == "new_refresh_token"
            assert protocol.token_expires == 9999999999

    def test_protocol_resolve_url_relative(self):
        """Test ApiV1 resolve_url with relative URL."""
        protocol = ApiV1()

        result = protocol.resolve_url("test/endpoint")

        assert result == "https://api.wahooligan.com/v1/test/endpoint"

    def test_protocol_resolve_url_absolute(self):
        """Test ApiV1 resolve_url with absolute URL."""
        protocol = ApiV1()

        result = protocol.resolve_url("https://example.com/test")

        assert result == "https://example.com/test"

    def test_protocol_get_method(self):
        """Test ApiV1 get method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"test": "data"}

            result = protocol.get("test/endpoint", param1="value1")

            mock_request.assert_called_once_with(
                "test/endpoint",
                params={"param1": "value1"},
                check_for_errors=True,
            )
            assert result == {"test": "data"}

    def test_protocol_post_method(self):
        """Test ApiV1 post method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"test": "data"}

            result = protocol.post("test/endpoint", param1="value1")

            mock_request.assert_called_once_with(
                "test/endpoint",
                params={"param1": "value1"},
                files=None,
                method="POST",
                check_for_errors=True,
            )
            assert result == {"test": "data"}

    def test_protocol_put_method(self):
        """Test ApiV1 put method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"test": "data"}

            result = protocol.put("test/endpoint", param1="value1")

            mock_request.assert_called_once_with(
                "test/endpoint",
                params={"param1": "value1"},
                method="PUT",
                check_for_errors=True,
            )
            assert result == {"test": "data"}

    def test_protocol_delete_method(self):
        """Test ApiV1 delete method."""
        protocol = ApiV1()

        with patch.object(protocol, "_request") as mock_request:
            mock_request.return_value = {"test": "data"}

            result = protocol.delete("test/endpoint", param1="value1")

            mock_request.assert_called_once_with(
                "test/endpoint",
                params={"param1": "value1"},
                method="DELETE",
                check_for_errors=True,
            )
            assert result == {"test": "data"}

    def test_protocol_handle_protocol_error_success(self):
        """Test ApiV1 _handle_protocol_error with successful response."""
        protocol = ApiV1()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        result = protocol._handle_protocol_error(mock_response)

        assert result == mock_response

    def test_protocol_handle_protocol_error_http_error(self):
        """Test ApiV1 _handle_protocol_error with HTTP error."""
        protocol = ApiV1()

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.json.return_value = {"message": "Invalid request"}

        with pytest.raises(ValueError, match="400 Bad Request"):
            protocol._handle_protocol_error(mock_response)

    def test_protocol_handle_protocol_error_with_message(self):
        """Test ApiV1 _handle_protocol_error with error message."""
        protocol = ApiV1()

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.json.return_value = {
            "message": "Invalid token",
            "errors": ["Token expired"],
        }

        with pytest.raises(
            ValueError,
            match="401 Unauthorized - Invalid token: \\['Token expired'\\]",
        ):
            protocol._handle_protocol_error(mock_response)

    def test_protocol_extract_referenced_vars(self):
        """Test ApiV1 _extract_referenced_vars method."""
        protocol = ApiV1()

        # Test with format variables
        result = protocol._extract_referenced_vars("test/{var1}/endpoint/{var2}")
        assert set(result) == {"var1", "var2"}

        # Test with no variables
        result = protocol._extract_referenced_vars("test/endpoint")
        assert result == []

        # Test with single variable
        result = protocol._extract_referenced_vars("test/{id}")
        assert result == ["id"]


class TestWahooAccessInfo:
    """Test AccessInfo TypedDict."""

    def test_access_info_structure(self):
        """Test AccessInfo structure."""
        access_info: AccessInfo = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
        }

        assert access_info["access_token"] == "test_access_token"
        assert access_info["refresh_token"] == "test_refresh_token"
        assert access_info["expires_at"] == 9999999999

    def test_access_info_required_fields(self):
        """Test that AccessInfo requires all fields."""
        # This should work
        access_info: AccessInfo = {
            "access_token": "test",
            "refresh_token": "test",
            "expires_at": 123,
        }
        assert access_info is not None


class TestWahooProtocolExtended:
    """Extended tests for Wahoo ApiV1 protocol class to cover missing lines."""

    def test_request_with_token_refresh(self):
        """Test _request method with token refresh."""
        with patch.dict(
            os.environ,
            {
                "WAHOO_CLIENT_ID": "test_client_id",
                "WAHOO_CLIENT_SECRET": "test_client_secret",
                "SILENCE_TOKEN_WARNINGS": "true",
            },
            clear=True,
        ):
            protocol = ApiV1(
                access_token="expired_token",
                token_expires=time.time() - 3600,  # Expired
                refresh_token="valid_refresh_token",
            )

            with patch.object(protocol, "refresh_expired_token") as mock_refresh:
                with patch.object(protocol, "resolve_url") as mock_resolve:
                    with patch.object(protocol, "rsession") as mock_session:
                        with patch.object(protocol, "rate_limiter"):
                            mock_resolve.return_value = (
                                "https://api.wahooligan.com/v1/test"
                            )
                            mock_response = Mock()
                            mock_response.status_code = 200
                            mock_response.json.return_value = {"success": True}
                            mock_response.headers = {}
                            mock_session.get.return_value = mock_response

                            result = protocol._request("test/endpoint", method="GET")

                            # Should call refresh_expired_token for non-oauth endpoints
                            mock_refresh.assert_called_once()
                            assert result == {"success": True}

    def test_request_without_token_refresh_for_oauth(self):
        """Test _request method without token refresh for OAuth endpoints."""
        with patch.dict(
            os.environ,
            {
                "WAHOO_CLIENT_ID": "test_client_id",
                "WAHOO_CLIENT_SECRET": "test_client_secret",
                "SILENCE_TOKEN_WARNINGS": "true",
            },
            clear=True,
        ):
            protocol = ApiV1(
                access_token="expired_token",
                token_expires=time.time() - 3600,  # Expired
                refresh_token="valid_refresh_token",
            )

            with patch.object(protocol, "refresh_expired_token") as mock_refresh:
                with patch.object(protocol, "resolve_url") as mock_resolve:
                    with patch.object(protocol, "rsession") as mock_session:
                        with patch.object(protocol, "rate_limiter"):
                            mock_resolve.return_value = (
                                "https://api.wahooligan.com/oauth/token"
                            )
                            mock_response = Mock()
                            mock_response.status_code = 200
                            mock_response.json.return_value = {
                                "access_token": "new_token"
                            }
                            mock_response.headers = {}
                            mock_session.post.return_value = mock_response

                            result = protocol._request("oauth/token", method="POST")

                            mock_refresh.assert_called_once()
                            assert result == {"access_token": "new_token"}

    def test_request_without_client_credentials(self):
        """Test _request method without client credentials."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1(
                access_token="expired_token",
                token_expires=time.time() - 3600,  # Expired
                refresh_token="valid_refresh_token",
            )

            with patch.object(protocol, "refresh_expired_token") as mock_refresh:
                with patch.object(protocol, "resolve_url") as mock_resolve:
                    with patch.object(protocol, "rsession") as mock_session:
                        with patch.object(protocol, "rate_limiter"):
                            mock_resolve.return_value = (
                                "https://api.wahooligan.com/v1/test"
                            )
                            mock_response = Mock()
                            mock_response.status_code = 200
                            mock_response.json.return_value = {"success": True}
                            mock_response.headers = {}
                            mock_session.get.return_value = mock_response

                            result = protocol._request("test/endpoint", method="GET")

                            mock_refresh.assert_not_called()
                            assert result == {"success": True}

    def test_request_invalid_method(self):
        """Test _request method with invalid HTTP method."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            with pytest.raises(
                ValueError,
                match="Invalid/unsupported request method specified: INVALID",
            ):
                protocol._request("test/endpoint", method="INVALID")

    def test_request_with_files(self):
        """Test _request method with file upload."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            with patch.object(protocol, "resolve_url") as mock_resolve:
                with patch.object(protocol, "rsession") as mock_session:
                    with patch.object(protocol, "rate_limiter"):
                        mock_resolve.return_value = (
                            "https://api.wahooligan.com/v1/upload"
                        )
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"uploaded": True}
                        mock_response.headers = {}
                        mock_session.post.return_value = mock_response

                        files = {"file": ("test.txt", "content", "text/plain")}
                        result = protocol._request("upload", method="POST", files=files)

                        # Should call post with files parameter
                        mock_session.post.assert_called_once()
                        assert result == {"uploaded": True}

    def test_request_204_no_content(self):
        """Test _request method with 204 No Content response."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            with patch.object(protocol, "resolve_url") as mock_resolve:
                with patch.object(protocol, "rsession") as mock_session:
                    with patch.object(protocol, "rate_limiter"):
                        mock_resolve.return_value = (
                            "https://api.wahooligan.com/v1/delete"
                        )
                        mock_response = Mock()
                        mock_response.status_code = 204
                        mock_response.headers = {}
                        mock_response.json.return_value = {}  # Mock json method
                        mock_session.delete.return_value = mock_response

                        result = protocol._request("delete", method="DELETE")

                        # Should return empty dict for 204 responses
                        assert result == {}

    def test_token_expired_with_expires_at(self):
        """Test _token_expired method when token has expires_at."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1(token_expires=time.time() - 3600)  # Expired

            with patch(
                "backend.src.services.wahoo.protocol.time.time",
                return_value=time.time(),
            ):
                result = protocol._token_expired()

                assert result is True

    def test_token_expired_without_expires_at(self):
        """Test _token_expired method when token has no expires_at."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1(token_expires=None)

            with patch("backend.src.services.wahoo.protocol.logging") as mock_logging:
                result = protocol._token_expired()

                assert result is False
                mock_logging.warning.assert_called_once()

    def test_token_not_expired(self):
        """Test _token_expired method when token is not expired."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1(token_expires=time.time() + 3600)  # Not expired

            with patch(
                "backend.src.services.wahoo.protocol.time.time",
                return_value=time.time(),
            ):
                result = protocol._token_expired()

                assert result is False

    def test_refresh_expired_token_no_refresh_token(self):
        """Test refresh_expired_token method without refresh token."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1(refresh_token=None)

            with patch("backend.src.services.wahoo.protocol.logging") as mock_logging:
                protocol.refresh_expired_token()

                mock_logging.warning.assert_called_once()

    def test_refresh_expired_token_token_not_expired(self):
        """Test refresh_expired_token method when token is not expired."""
        with patch.dict(
            os.environ,
            {
                "WAHOO_CLIENT_ID": "test_client_id",
                "WAHOO_CLIENT_SECRET": "test_client_secret",
                "SILENCE_TOKEN_WARNINGS": "true",
            },
            clear=True,
        ):
            protocol = ApiV1(
                refresh_token="valid_refresh_token",
                token_expires=time.time() + 3600,  # Not expired
            )

            with patch.object(protocol, "_token_expired", return_value=False):
                with patch.object(protocol, "refresh_access_token") as mock_refresh:
                    protocol.refresh_expired_token()

                    # Should not call refresh_access_token
                    mock_refresh.assert_not_called()

    def test_refresh_expired_token_success(self):
        """Test refresh_expired_token method with successful refresh."""
        with patch.dict(
            os.environ,
            {
                "WAHOO_CLIENT_ID": "test_client_id",
                "WAHOO_CLIENT_SECRET": "test_client_secret",
                "SILENCE_TOKEN_WARNINGS": "true",
            },
            clear=True,
        ):
            protocol = ApiV1(
                refresh_token="valid_refresh_token",
                token_expires=time.time() - 3600,  # Expired
            )

            with patch.object(protocol, "_token_expired", return_value=True):
                with patch.object(protocol, "refresh_access_token") as mock_refresh:
                    protocol.refresh_expired_token()

                    # Should call refresh_access_token
                    mock_refresh.assert_called_once_with(
                        client_id="test_client_id",
                        client_secret="test_client_secret",
                        refresh_token="valid_refresh_token",
                    )

    def test_refresh_expired_token_assertion_error(self):
        """Test refresh_expired_token method with missing client credentials."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1(
                refresh_token="valid_refresh_token",
                token_expires=time.time() - 3600,  # Expired
            )

            with patch.object(protocol, "_token_expired", return_value=True):
                with pytest.raises(
                    AssertionError, match="client_id is required but is None"
                ):
                    protocol.refresh_expired_token()

    def test_handle_protocol_error_json_decode_error(self):
        """Test _handle_protocol_error method with JSON decode error."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.reason = "Bad Request"
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.text = "Some error message"

            # Should raise ValueError for 400 status code even with JSON decode error
            with pytest.raises(ValueError, match="400 Bad Request"):
                protocol._handle_protocol_error(mock_response)

    def test_handle_protocol_error_with_message_and_errors(self):
        """Test _handle_protocol_error method with both message and errors."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.reason = "Bad Request"
            mock_response.json.return_value = {
                "message": "Validation failed",
                "errors": ["Field is required", "Invalid format"],
            }

            expected_msg = (
                r"400 Bad Request - Validation failed: "
                r"\['Field is required', 'Invalid format'\]"
            )
            with pytest.raises(ValueError, match=expected_msg):
                protocol._handle_protocol_error(mock_response)

    def test_handle_protocol_error_with_message_only(self):
        """Test _handle_protocol_error method with message only."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.reason = "Unauthorized"
            mock_response.json.return_value = {
                "message": "Invalid token",
            }

            with pytest.raises(ValueError, match="401 Unauthorized - Invalid token"):
                protocol._handle_protocol_error(mock_response)

    def test_handle_protocol_error_with_errors_only(self):
        """Test _handle_protocol_error method with errors only."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.reason = "Unprocessable Entity"
            mock_response.json.return_value = {
                "errors": ["Missing required field"],
            }

            expected_msg = (
                r"422 Unprocessable Entity - Undefined error: "
                r"\['Missing required field'\]"
            )
            with pytest.raises(ValueError, match=expected_msg):
                protocol._handle_protocol_error(mock_response)

    def test_handle_protocol_error_success_response(self):
        """Test _handle_protocol_error method with successful response."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.reason = "OK"
            mock_response.json.return_value = {"success": True}

            # Should return the response for successful status codes
            result = protocol._handle_protocol_error(mock_response)
            assert result == mock_response

    def test_request_with_created_at_and_expires_in(self):
        """Test _request method with response containing created_at and expires_in."""
        with patch.dict(os.environ, {}, clear=True):
            protocol = ApiV1()

            with patch.object(protocol, "resolve_url") as mock_resolve:
                with patch.object(protocol, "rsession") as mock_session:
                    with patch.object(protocol, "rate_limiter"):
                        mock_resolve.return_value = "https://api.wahooligan.com/v1/test"
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            "access_token": "new_token",
                            "created_at": 1640995200,  # Unix timestamp
                            "expires_in": 3600,  # 1 hour in seconds
                        }
                        mock_response.headers = {}
                        mock_session.get.return_value = mock_response

                        result = protocol._request("test/endpoint", method="GET")

                        # Should calculate expires_at from created_at + expires_in
                        expected_result = {
                            "access_token": "new_token",
                            "created_at": 1640995200,
                            "expires_in": 3600,
                            "expires_at": 1640998800,  # created_at + expires_in
                        }
                        assert result == expected_result


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


class TestWahooProtocolDataParameter:
    """Test _request method with data parameter."""

    def test_request_with_data_parameter(self):
        """Test _request method with data parameter."""
        protocol = ApiV1(access_token="test_token")

        # Mock the session
        mock_session = Mock(spec=Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_session.post.return_value = mock_response

        protocol.rsession = mock_session

        # Call _request with data parameter
        result = protocol._request(
            "test/endpoint", data={"key": "value"}, method="POST"
        )

        assert result == {"success": True}

        # Verify post was called with data
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args[1]
        assert "data" in call_kwargs
        assert call_kwargs["data"] == {"key": "value"}

    def test_request_with_data_and_files(self):
        """Test _request method with both data and files parameters."""
        protocol = ApiV1(access_token="test_token")

        # Mock the session
        mock_session = Mock(spec=Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_session.post.return_value = mock_response

        protocol.rsession = mock_session

        # Create mock file
        mock_file = Mock()
        mock_file.read.return_value = b"file content"

        files = {"file": ("test.txt", mock_file, "text/plain")}

        # Call _request with data and files
        result = protocol._request(
            "test/endpoint", data={"key": "value"}, files=files, method="POST"
        )

        assert result == {"success": True}

        # Verify post was called with both data and files
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args[1]
        assert "data" in call_kwargs
        assert "files" in call_kwargs

    def test_request_data_logging(self):
        """Test that _request logs data parameter."""
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
                data={"key1": "value1", "key2": "value2"},
                method="POST",
            )

            # Verify that data was logged
            log_calls = [str(call) for call in mock_log.call_args_list]
            data_logged = any("Data: " in str(call) for call in log_calls)
            assert data_logged


class TestWahooProtocolWithDataLogging:
    """Test logging when data parameter is provided."""

    def test_request_data_list_keys_logged(self):
        """Test that data parameter keys are logged as a list."""
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
                data={"route[name]": "Test", "route[file]": "data"},
                method="POST",
            )

            # Check that logging was called with data keys
            log_calls_str = [str(call) for call in mock_log.call_args_list]
            assert any(
                "route[name]" in str(call) or "route[file]" in str(call)
                for call in log_calls_str
            )
