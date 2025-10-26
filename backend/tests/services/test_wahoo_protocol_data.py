"""Tests for Wahoo protocol _request data parameter handling."""

from unittest.mock import Mock, patch

from requests import Session

from backend.src.services.wahoo.protocol import ApiV1


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
