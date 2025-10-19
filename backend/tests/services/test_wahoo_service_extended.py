"""Extended unit tests for Wahoo service to cover missing lines."""

from unittest.mock import patch

import pytest

from backend.src.services.wahoo.exceptions import WahooAccessUnauthorized
from backend.src.services.wahoo.service import WahooService
from backend.src.utils.config import WahooConfig


class TestWahooServiceExtended:
    """Extended tests for WahooService to cover missing lines."""

    def test_save_tokens_convert_datetime_recursive_dict(self):
        """Test _save_tokens with nested datetime objects in dict."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Create tokens with nested datetime objects
            from datetime import datetime

            tokens = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "expires_at": 9999999999,
                "user_info": {
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
                "metadata": {
                    "nested": {
                        "timestamp": datetime.now(),
                    },
                },
            }

            with patch("builtins.open", mock_open()):
                with patch("json.dump") as mock_json_dump:
                    service._save_tokens(tokens)

                    # Should call json.dump with serialized tokens
                    mock_json_dump.assert_called_once()
                    call_args = mock_json_dump.call_args[0][0]

                    # Check that datetime objects are converted to ISO format
                    assert isinstance(call_args["user_info"]["created_at"], str)
                    assert isinstance(call_args["user_info"]["updated_at"], str)
                    assert isinstance(call_args["metadata"]["nested"]["timestamp"], str)

    def test_save_tokens_convert_datetime_recursive_list(self):
        """Test _save_tokens with datetime objects in list."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Create tokens with datetime objects in list
            from datetime import datetime

            tokens = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "expires_at": 9999999999,
                "timestamps": [datetime.now(), datetime.now()],
                "nested_list": [
                    {"created": datetime.now()},
                    {"updated": datetime.now()},
                ],
            }

            with patch("builtins.open", mock_open()):
                with patch("json.dump") as mock_json_dump:
                    service._save_tokens(tokens)

                    # Should call json.dump with serialized tokens
                    mock_json_dump.assert_called_once()
                    call_args = mock_json_dump.call_args[0][0]

                    # Check that datetime objects in list are converted
                    assert all(isinstance(ts, str) for ts in call_args["timestamps"])
                    # Check that datetime objects in nested list items are converted
                    for item in call_args["nested_list"]:
                        if "created" in item:
                            assert isinstance(item["created"], str)
                        if "updated" in item:
                            assert isinstance(item["updated"], str)

    def test_save_tokens_convert_datetime_other_types(self):
        """Test _save_tokens with other types that should pass through."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Create tokens with various types
            tokens = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "expires_at": 9999999999,
                "user_id": 12345,
                "is_active": True,
                "metadata": None,
            }

            with patch("builtins.open", mock_open()):
                with patch("json.dump") as mock_json_dump:
                    service._save_tokens(tokens)

                    # Should call json.dump with tokens unchanged
                    mock_json_dump.assert_called_once()
                    call_args = mock_json_dump.call_args[0][0]

                    # Check that non-datetime types pass through unchanged
                    assert call_args["access_token"] == "test_token"
                    assert call_args["refresh_token"] == "test_refresh"
                    assert call_args["expires_at"] == 9999999999
                    assert call_args["user_id"] == 12345
                    assert call_args["is_active"] is True
                    assert call_args["metadata"] is None

    def test_deauthorize_401_unauthorized_error(self):
        """Test deauthorize method with 401 Unauthorized error."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Setup valid tokens
            valid_tokens = {
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token",
                "expires_at": 9999999999,
            }
            service._save_tokens(valid_tokens)

            with patch.object(service.client, "deauthorize") as mock_deauth:
                mock_deauth.side_effect = ValueError("401 Unauthorized")

                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    with pytest.raises(WahooAccessUnauthorized):
                        service.deauthorize()

                    mock_logger.error.assert_called_with(
                        "Wahoo API access unauthorized: 401 Unauthorized"
                    )

    def test_deauthorize_unauthorized_error_lowercase(self):
        """Test deauthorize method with unauthorized error (lowercase)."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Setup valid tokens
            valid_tokens = {
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token",
                "expires_at": 9999999999,
            }
            service._save_tokens(valid_tokens)

            with patch.object(service.client, "deauthorize") as mock_deauth:
                mock_deauth.side_effect = ValueError("access unauthorized")

                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    with pytest.raises(WahooAccessUnauthorized):
                        service.deauthorize()

                    mock_logger.error.assert_called_with(
                        "Wahoo API access unauthorized: access unauthorized"
                    )

    def test_deauthorize_general_error(self):
        """Test deauthorize method with general error."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Setup valid tokens
            valid_tokens = {
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token",
                "expires_at": 9999999999,
            }
            service._save_tokens(valid_tokens)

            with patch.object(service.client, "deauthorize") as mock_deauth:
                mock_deauth.side_effect = ValueError("Network error")

                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    with pytest.raises(ValueError, match="Network error"):
                        service.deauthorize()

                    mock_logger.error.assert_called_with(
                        "Failed to deauthorize: Network error"
                    )

    def test_deauthorize_exception_during_deauthorize(self):
        """Test deauthorize method with exception during deauthorize."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Setup valid tokens
            valid_tokens = {
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token",
                "expires_at": 9999999999,
            }
            service._save_tokens(valid_tokens)

            with patch.object(service.client, "deauthorize") as mock_deauth:
                mock_deauth.side_effect = Exception("Unexpected error")

                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    with pytest.raises(Exception, match="Unexpected error"):
                        service.deauthorize()

                    mock_logger.error.assert_called_with(
                        "Failed to deauthorize: Unexpected error"
                    )


def mock_open():
    """Mock open function for testing file operations."""
    from unittest.mock import mock_open as _mock_open

    return _mock_open()
