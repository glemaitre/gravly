"""Extended unit tests for Wahoo protocol to cover missing lines."""

import os
import time
from unittest.mock import Mock, patch

import pytest

from backend.src.services.wahoo.protocol import ApiV1


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
