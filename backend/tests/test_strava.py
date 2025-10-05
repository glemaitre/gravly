"""Tests for Strava API endpoints."""

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from src.utils.gpx import GPXBounds, GPXData, GPXPoint, GPXTotalStats


@pytest.fixture(autouse=True)
def setup_test_database_config():
    """Set up database and storage configuration for tests.

    IMPORTANT: This fixture must run BEFORE src.main is imported because:
    1. src.main calls load_environment_config() at import time
    2. If we import src.main at the top of this file, it would use real environment
       variables instead of our test configuration
    3. This fixture ensures test environment variables are set FIRST, then imports
       src.main with the correct test configuration

    This pattern prevents tests from failing due to missing or incorrect environment
    variables in the test environment.
    """
    test_config = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "test_cycling",
        "DB_USER": "test_postgres",
        "DB_PASSWORD": "test_password",
        "STORAGE_TYPE": "local",
        "LOCAL_STORAGE_ROOT": "./test_storage",
        "LOCAL_STORAGE_BASE_URL": "http://localhost:8000/storage",
        "STRAVA_CLIENT_ID": "test_client_id",
        "STRAVA_CLIENT_SECRET": "test_client_secret",
        "STRAVA_TOKENS_FILE_PATH": "/tmp/test_strava_tokens.json",
    }

    with patch.dict(os.environ, test_config, clear=False):
        # Import main module AFTER setting up environment variables
        # This ensures src.main loads with test configuration, not real environment
        import src.main as main_module

        # Make main_module available globally for tests as 'src'
        # This allows existing @patch decorators to work with src.main references
        globals()["src"] = type("MockSrc", (), {"main": main_module})()
        yield


@pytest.fixture
def main_module():
    """Get access to the main module for testing.

    This fixture provides access to the src.main module that was imported with
    test configuration by the setup_test_database_config fixture. Tests can use
    this fixture instead of accessing the global 'src' variable directly, which
    provides better type safety and cleaner test code.
    """
    import src.main

    return src.main


@pytest.fixture
def client(main_module):
    """Create a test client for the FastAPI application.

    This fixture creates a TestClient instance that can be used to make HTTP
    requests to the FastAPI application during testing. The client is configured
    with the main module that was imported with test configuration.

    Parameters
    ----------
    main_module : module
        The main FastAPI application module imported with test configuration.

    Returns
    -------
    TestClient
        A FastAPI TestClient instance for making HTTP requests during tests.
    """
    return TestClient(main_module.app)


class TestStravaEndpoints:
    """Test suite for Strava API endpoints."""

    def test_get_strava_auth_url_success(self, client):
        """Test successful generation of Strava authorization URL."""
        with patch("src.main.strava.get_authorization_url") as mock_get_auth_url:
            mock_get_auth_url.return_value = (
                "https://www.strava.com/oauth/authorize?client_id=123&redirect_uri=test"
            )

            response = client.get("/api/strava/auth-url")

            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert (
                data["auth_url"]
                == "https://www.strava.com/oauth/authorize?client_id=123&redirect_uri=test"
            )
            mock_get_auth_url.assert_called_once_with(
                "http://localhost:3000/strava-callback", "strava_auth"
            )

    def test_get_strava_auth_url_with_custom_state(self, client):
        """Test Strava authorization URL generation with custom state."""
        with patch("src.main.strava.get_authorization_url") as mock_get_auth_url:
            mock_get_auth_url.return_value = "https://www.strava.com/oauth/authorize?client_id=123&state=custom_state"

            response = client.get("/api/strava/auth-url?state=custom_state")

            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            mock_get_auth_url.assert_called_once_with(
                "http://localhost:3000/strava-callback", "custom_state"
            )

    def test_get_strava_auth_url_error(self, client):
        """Test Strava authorization URL generation error handling."""
        with patch("src.main.strava.get_authorization_url") as mock_get_auth_url:
            mock_get_auth_url.side_effect = Exception("Configuration error")

            response = client.get("/api/strava/auth-url")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to generate auth URL" in data["detail"]

    def test_exchange_strava_code_success(self, client):
        """Test successful Strava code exchange."""
        mock_token_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
            "athlete": {
                "id": 12345,
                "username": "test_user",
                "firstname": "Test",
                "lastname": "User",
            },
        }

        with patch("src.main.strava.exchange_code_for_token") as mock_exchange:
            mock_exchange.return_value = mock_token_response

            response = client.post(
                "/api/strava/exchange-code", data={"code": "test_code"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "test_access_token"
            assert data["expires_at"] == 9999999999
            assert data["athlete"]["id"] == 12345
            mock_exchange.assert_called_once_with("test_code")

    def test_exchange_strava_code_error(self, client):
        """Test Strava code exchange error handling."""
        with patch("src.main.strava.exchange_code_for_token") as mock_exchange:
            mock_exchange.side_effect = Exception("Invalid code")

            response = client.post(
                "/api/strava/exchange-code", data={"code": "invalid_code"}
            )

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Failed to exchange code" in data["detail"]

    def test_refresh_strava_token_success(self, client):
        """Test successful Strava token refresh."""
        with patch("src.main.strava.refresh_access_token") as mock_refresh:
            mock_refresh.return_value = True

            response = client.post("/api/strava/refresh-token")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Token refreshed successfully"
            mock_refresh.assert_called_once()

    def test_refresh_strava_token_failure(self, client):
        """Test Strava token refresh failure."""
        with patch("src.main.strava.refresh_access_token") as mock_refresh:
            mock_refresh.return_value = False

            response = client.post("/api/strava/refresh-token")

            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Failed to refresh token" in data["detail"]

    def test_refresh_strava_token_exception(self, client):
        """Test Strava token refresh exception handling."""
        with patch("src.main.strava.refresh_access_token") as mock_refresh:
            mock_refresh.side_effect = Exception("Token refresh error")

            response = client.post("/api/strava/refresh-token")

            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Failed to refresh token" in data["detail"]

    def test_get_strava_activities_success(self, client):
        """Test successful Strava activities retrieval."""
        mock_activities = [
            {
                "id": "12345",
                "name": "Morning Ride",
                "distance": 25000.0,
                "moving_time": 3600,
                "type": "Ride",
                "start_date": "2023-01-01T10:00:00",
            },
            {
                "id": "12346",
                "name": "Evening Run",
                "distance": 5000.0,
                "moving_time": 1800,
                "type": "Run",
                "start_date": "2023-01-01T18:00:00",
            },
        ]

        with patch("src.main.strava.get_activities") as mock_get_activities:
            mock_get_activities.return_value = mock_activities

            response = client.get("/api/strava/activities")

            assert response.status_code == 200
            data = response.json()
            assert "activities" in data
            assert len(data["activities"]) == 2
            assert data["page"] == 1
            assert data["per_page"] == 30
            assert data["total"] == 2
            assert data["activities"][0]["name"] == "Morning Ride"
            mock_get_activities.assert_called_once_with(1, 30)

    def test_get_strava_activities_with_pagination(self, client):
        """Test Strava activities retrieval with custom pagination."""
        mock_activities = [{"id": "12345", "name": "Test Activity"}]

        with patch("src.main.strava.get_activities") as mock_get_activities:
            mock_get_activities.return_value = mock_activities

            response = client.get("/api/strava/activities?page=2&per_page=10")

            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert data["per_page"] == 10
            mock_get_activities.assert_called_once_with(2, 10)

    def test_get_strava_activities_error(self, client):
        """Test Strava activities retrieval error handling."""
        with patch("src.main.strava.get_activities") as mock_get_activities:
            mock_get_activities.side_effect = Exception("API error")

            response = client.get("/api/strava/activities")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to fetch activities" in data["detail"]

    def test_get_strava_activities_http_exception(self, client):
        """Test Strava activities retrieval HTTPException handling."""

        with patch("src.main.strava.get_activities") as mock_get_activities:
            mock_get_activities.side_effect = HTTPException(
                status_code=401, detail="Unauthorized access"
            )

            response = client.get("/api/strava/activities")

            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert data["detail"] == "Unauthorized access"

    def test_get_strava_activity_gpx_success(self, client):
        """Test successful Strava activity GPX retrieval."""
        # Create proper GPX data objects
        gpx_point = GPXPoint(
            latitude=51.5074,
            longitude=-0.1278,
            elevation=10.0,
            time="2023-01-01T10:00:00Z",
        )

        total_stats = GPXTotalStats(
            total_points=1,
            total_distance=0.0,
            total_elevation_gain=0.0,
            total_elevation_loss=0.0,
        )

        bounds = GPXBounds(
            north=51.5074,
            south=51.5074,
            east=-0.1278,
            west=-0.1278,
            min_elevation=10.0,
            max_elevation=10.0,
        )

        mock_gpx_data = GPXData(
            file_id="test_file_id",
            track_name="Test Activity",
            points=[gpx_point],
            total_stats=total_stats,
            bounds=bounds,
        )

        mock_gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
    <trk>
        <name>Test Activity</name>
        <trkpt lat="51.5074" lon="-0.1278">
            <ele>10.0</ele>
            <time>2023-01-01T10:00:00Z</time>
        </trkpt>
    </trk>
</gpx>"""

        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("src.api.strava.extract_from_gpx_file") as mock_extract,
            patch("src.api.strava.gpxpy.parse"),
            patch("builtins.open", create=True),
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
        ):
            # Setup mocks for file processing
            mock_temp_dir.name = "/tmp/test_dir"
            mock_get_gpx.return_value = mock_gpx_string
            mock_extract.return_value = mock_gpx_data
            mock_exists.return_value = True

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 200
            data = response.json()
            assert "file_id" in data
            assert data["track_name"] == "Test Activity"
            assert len(data["points"]) == 1
            mock_get_gpx.assert_called_once_with("12345")

    def test_get_strava_activity_gpx_no_data(self, client):
        """Test Strava activity GPX retrieval when no GPX data available."""
        with patch("src.main.strava.get_activity_gpx") as mock_get_gpx:
            mock_get_gpx.return_value = None

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "No GPX data available for this activity" in data["detail"]

    def test_get_strava_activity_gpx_no_temp_dir(self, client):
        """Test Strava activity GPX retrieval when temp directory not initialized."""
        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir", None),
        ):
            mock_get_gpx.return_value = '<?xml version="1.0"?><gpx></gpx>'

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Temporary directory not initialized" in data["detail"]

    def test_get_strava_activity_gpx_save_error(self, client):
        """Test Strava activity GPX retrieval with file save error."""
        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("builtins.open", side_effect=OSError("Permission denied")),
        ):
            mock_get_gpx.return_value = '<?xml version="1.0"?><gpx></gpx>'
            mock_temp_dir.name = "/tmp/test_dir"

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to save GPX" in data["detail"]

    def test_get_strava_activity_gpx_parse_error(self, client):
        """Test Strava activity GPX retrieval with GPX parse error."""
        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("builtins.open", create=True),
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
            patch("src.api.strava.gpxpy.parse", side_effect=Exception("Invalid GPX")),
        ):
            mock_get_gpx.return_value = "invalid gpx content"
            mock_temp_dir.name = "/tmp/test_dir"
            mock_exists.return_value = True

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Invalid GPX file" in data["detail"]

    def test_get_strava_activity_gpx_extract_error(self, client):
        """Test Strava activity GPX retrieval with GPX extraction error."""
        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("builtins.open", create=True),
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
            patch("src.api.strava.gpxpy.parse"),
            patch(
                "src.api.strava.extract_from_gpx_file",
                side_effect=Exception("Processing error"),
            ),
        ):
            mock_get_gpx.return_value = '<?xml version="1.0"?><gpx></gpx>'
            mock_temp_dir.name = "/tmp/test_dir"
            mock_exists.return_value = True

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Invalid GPX file" in data["detail"]

    def test_get_strava_activity_gpx_general_error(self, client):
        """Test Strava activity GPX retrieval with general error."""
        with patch("src.main.strava.get_activity_gpx") as mock_get_gpx:
            mock_get_gpx.side_effect = Exception("Network error")

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to fetch GPX" in data["detail"]

    def test_get_strava_activity_gpx_http_exception(self, client):
        """Test Strava activity GPX retrieval HTTPException handling."""

        with patch("src.main.strava.get_activity_gpx") as mock_get_gpx:
            mock_get_gpx.side_effect = HTTPException(
                status_code=403, detail="Forbidden access to activity"
            )

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 403
            data = response.json()
            assert "detail" in data
            assert data["detail"] == "Forbidden access to activity"

    def test_get_strava_activities_with_stravalib_mock(self, client):
        """Test Strava activities retrieval using proper stravalib client mocking."""
        mock_activities = [
            {
                "id": "12345",
                "name": "Morning Ride",
                "distance": 25000.0,
                "moving_time": 3600,
                "type": "Ride",
                "start_date": "2023-01-01T10:00:00",
            },
            {
                "id": "12346",
                "name": "Evening Run",
                "distance": 5000.0,
                "moving_time": 1800,
                "type": "Run",
                "start_date": "2023-01-01T18:00:00",
            },
        ]

        # Mock the strava service's get_activities method directly (same as other
        # working tests)
        with patch("src.main.strava.get_activities") as mock_get_activities:
            # Configure the mock to return our mock activities
            mock_get_activities.return_value = mock_activities

            response = client.get("/api/strava/activities")

            assert response.status_code == 200
            data = response.json()
            assert "activities" in data
            assert len(data["activities"]) == 2
            assert data["activities"][0]["name"] == "Morning Ride"
            assert data["activities"][1]["name"] == "Evening Run"

    def test_get_strava_activity_gpx_with_stravalib_mock(self, client):
        """Test Strava activity GPX retrieval using proper stravalib client mocking."""
        mock_gpx_string = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
    <trk>
        <name>Test Activity</name>
        <trkpt lat="51.5074" lon="-0.1278">
            <ele>10.0</ele>
            <time>2023-01-01T10:00:00Z</time>
        </trkpt>
    </trk>
</gpx>"""

        with (
            patch("src.main.strava.get_activity_gpx") as mock_get_gpx,
            patch("src.main.temp_dir") as mock_temp_dir,
            patch("src.api.strava.extract_from_gpx_file") as mock_extract,
            patch("src.api.strava.gpxpy.parse"),
            patch("builtins.open", create=True),
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
        ):
            # Create proper GPX data objects
            from src.utils.gpx import GPXBounds, GPXData, GPXPoint, GPXTotalStats

            gpx_point = GPXPoint(
                latitude=51.5074,
                longitude=-0.1278,
                elevation=10.0,
                time="2023-01-01T10:00:00Z",
            )

            total_stats = GPXTotalStats(
                total_points=1,
                total_distance=0.0,
                total_elevation_gain=0.0,
                total_elevation_loss=0.0,
            )

            bounds = GPXBounds(
                north=51.5074,
                south=51.5074,
                east=-0.1278,
                west=-0.1278,
                min_elevation=10.0,
                max_elevation=10.0,
            )

            mock_gpx_data = GPXData(
                file_id="test_file_id",
                track_name="Test Activity",
                points=[gpx_point],
                total_stats=total_stats,
                bounds=bounds,
            )

            # Setup mocks for file processing
            mock_temp_dir.name = "/tmp/test_dir"
            mock_get_gpx.return_value = mock_gpx_string
            mock_extract.return_value = mock_gpx_data
            mock_exists.return_value = True

            response = client.get("/api/strava/activities/12345/gpx")

            assert response.status_code == 200
            data = response.json()
            assert "file_id" in data
            assert data["track_name"] == "Test Activity"
            assert len(data["points"]) == 1
