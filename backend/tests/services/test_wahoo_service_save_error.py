"""Tests for Wahoo service _save_tokens error handling."""

from unittest.mock import mock_open, patch

from backend.src.services.wahoo.service import WahooService
from backend.src.utils.config import WahooConfig


class TestWahooServiceSaveError:
    """Tests for Wahoo service _save_tokens error handling."""

    def test_save_tokens_file_write_error(self):
        """Test _save_tokens when file write fails."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Mock open to raise an exception
            with patch("builtins.open", side_effect=OSError("Permission denied")):
                with patch("backend.src.services.wahoo.service.logger") as mock_logger:
                    tokens = {"access_token": "test_token"}
                    service._save_tokens(tokens)

                    # Should log the error
                    mock_logger.error.assert_called_once_with(
                        "Failed to save tokens: Permission denied"
                    )

    def test_save_tokens_json_dump_error(self):
        """Test _save_tokens when json.dump fails."""
        config = WahooConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            tokens_file_path="/tmp/test_tokens.json",
            callback_url="https://test.example.com/wahoo-callback",
        )

        with patch("backend.src.services.wahoo.service.Client"):
            service = WahooService(config)

            # Mock json.dump to raise an exception
            with patch("builtins.open", mock_open()):
                with patch(
                    "backend.src.services.wahoo.service.json.dump",
                    side_effect=TypeError("Not JSON serializable"),
                ):
                    with patch(
                        "backend.src.services.wahoo.service.logger"
                    ) as mock_logger:
                        tokens = {"access_token": "test_token"}
                        service._save_tokens(tokens)

                        # Should log the error
                        mock_logger.error.assert_called_once_with(
                            "Failed to save tokens: Not JSON serializable"
                        )
