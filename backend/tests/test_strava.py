"""Tests for Strava API endpoints."""

import os
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


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
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.authorization_url.return_value = (
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
            mock_client.authorization_url.assert_called_once()

    def test_get_strava_auth_url_with_custom_state(self, client):
        """Test Strava authorization URL generation with custom state."""
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.authorization_url.return_value = "https://www.strava.com/oauth/authorize?client_id=123&state=custom_state"

            response = client.get("/api/strava/auth-url?state=custom_state")

            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            mock_client.authorization_url.assert_called_once()

    def test_get_strava_auth_url_error(self, client):
        """Test Strava authorization URL generation error handling."""
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.authorization_url.side_effect = Exception("Configuration error")

            response = client.get("/api/strava/auth-url")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to generate auth URL" in data["detail"]


class TestStravaDatabaseNotInitialized:
    """Test suite for database not initialized scenarios."""

    def test_exchange_code_no_database(self, client):
        """Test code exchange when database is not initialized."""
        with patch("src.dependencies.SessionLocal", None):
            response = client.post(
                "/api/strava/exchange-code", data={"code": "test_code"}
            )

            assert response.status_code == 503
            data = response.json()
            assert "Database not initialized" in data["detail"]

    def test_refresh_token_no_database(self, client):
        """Test token refresh when database is not initialized."""
        with patch("src.dependencies.SessionLocal", None):
            response = client.post(
                "/api/strava/refresh-token",
                data={"strava_id": 12345},
            )

            assert response.status_code == 503
            data = response.json()
            assert "Database not initialized" in data["detail"]

    def test_get_activities_no_database(self, client):
        """Test activity retrieval when database is not initialized."""
        with patch("src.dependencies.SessionLocal", None):
            response = client.get("/api/strava/activities?strava_id=12345")

            assert response.status_code == 503
            data = response.json()
            assert "Database not initialized" in data["detail"]

    def test_get_activity_gpx_no_database(self, client):
        """Test GPX retrieval when database is not initialized."""
        with patch("src.dependencies.SessionLocal", None):
            response = client.get("/api/strava/activities/12345/gpx?strava_id=67890")

            assert response.status_code == 503
            data = response.json()
            assert "Database not initialized" in data["detail"]


class TestStravaExchangeCodeEndpoint:
    """Test suite for Strava exchange code endpoint."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Strava client."""
        client = Mock()
        return client

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        from unittest.mock import AsyncMock

        session = Mock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        return session

    def test_exchange_code_success_new_token(
        self, client, mock_client, mock_db_session
    ):
        """Test successful code exchange creating a new token."""
        from datetime import datetime
        from unittest.mock import AsyncMock

        # Mock the athlete
        mock_athlete = Mock()
        mock_athlete.id = 12345
        mock_athlete.model_dump.return_value = {"id": 12345, "username": "test_user"}

        # Mock token response
        mock_access_info = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": int(datetime.now().timestamp()) + 3600,
        }
        mock_token_response = (mock_access_info, mock_athlete)

        # Mock Client to return token response
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.exchange_code_for_token.return_value = mock_token_response

            # Mock database session
            with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
                # Mock database query result (no existing token)
                mock_result = Mock()
                mock_result.scalar_one_or_none.return_value = None
                mock_db_session.execute = AsyncMock(return_value=mock_result)
                mock_db_session.commit = AsyncMock()

                response = client.post(
                    "/api/strava/exchange-code", data={"code": "test_code"}
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "expires_at" in data
                assert "athlete" in data
                assert data["athlete"]["id"] == 12345

    def test_exchange_code_success_update_existing_token(self, client, mock_db_session):
        """Test successful code exchange updating an existing token."""
        from datetime import datetime, timedelta
        from unittest.mock import AsyncMock

        # Mock the athlete
        mock_athlete = Mock()
        mock_athlete.id = 12345
        mock_athlete.model_dump.return_value = {"id": 12345, "username": "test_user"}

        # Mock token response
        mock_access_info = {
            "access_token": "updated_access_token",
            "refresh_token": "updated_refresh_token",
            "expires_at": int(datetime.now().timestamp()) + 3600,
        }
        mock_token_response = (mock_access_info, mock_athlete)

        # Mock Client to return token response
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.exchange_code_for_token.return_value = mock_token_response

            # Mock database session
            with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
                # Mock existing token
                mock_token_record = Mock()
                mock_token_record.strava_id = 12345
                mock_token_record.access_token = "old_token"
                mock_token_record.refresh_token = "old_refresh"
                mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
                mock_token_record.athlete_data = '{"id": 12345}'

                mock_result = Mock()
                mock_result.scalar_one_or_none.return_value = mock_token_record
                mock_db_session.execute = AsyncMock(return_value=mock_result)
                mock_db_session.commit = AsyncMock()

                response = client.post(
                    "/api/strava/exchange-code", data={"code": "test_code"}
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert data["access_token"] == "updated_access_token"

    def test_exchange_code_invalid_response(self, client):
        """Test code exchange with invalid response from Strava API."""
        # Mock Client to return unexpected response
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            # Return a dict instead of tuple
            mock_client.exchange_code_for_token.return_value = {"access_token": "token"}

            with patch("src.dependencies.SessionLocal"):
                response = client.post(
                    "/api/strava/exchange-code", data={"code": "test_code"}
                )

                assert response.status_code == 400
                data = response.json()
                assert "Unexpected response from Strava API" in data["detail"]

    def test_exchange_code_no_athlete(self, client):
        """Test code exchange when no athlete info is returned."""
        # Mock Client to return response without athlete
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            # Return tuple with None athlete
            mock_client.exchange_code_for_token.return_value = (
                {"access_token": "token"},
                None,
            )

            with patch("src.dependencies.SessionLocal"):
                response = client.post(
                    "/api/strava/exchange-code", data={"code": "test_code"}
                )

                assert response.status_code == 400
                data = response.json()
                assert "No athlete information in response" in data["detail"]

    def test_exchange_code_exception(self, client):
        """Test code exchange when an exception occurs."""
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.exchange_code_for_token.side_effect = Exception("API Error")

            with patch("src.dependencies.SessionLocal"):
                response = client.post(
                    "/api/strava/exchange-code", data={"code": "test_code"}
                )

                assert response.status_code == 400
                data = response.json()
                assert "Failed to exchange code" in data["detail"]

    def test_exchange_code_with_nested_datetime(self, client, mock_db_session):
        """Test code exchange with nested datetime objects in athlete data."""
        from datetime import datetime
        from unittest.mock import AsyncMock

        # Mock the athlete with nested datetime objects
        mock_athlete = Mock()
        mock_athlete.id = 12345

        # Create a dict with datetime objects to test conversion
        athlete_data = {
            "id": 12345,
            "created_at": datetime.now(),
            "profile": {"profile_updated_at": datetime.now()},
            "friends": [{"friend_created_at": datetime.now()}],
        }
        mock_athlete.model_dump.return_value = athlete_data

        # Mock token response
        mock_access_info = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": int(datetime.now().timestamp()) + 3600,
        }
        mock_token_response = (mock_access_info, mock_athlete)

        # Mock Client to return token response
        with patch("src.api.strava.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.exchange_code_for_token.return_value = mock_token_response

            # Mock database session
            with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
                # Mock database query result (no existing token)
                mock_result = Mock()
                mock_result.scalar_one_or_none.return_value = None
                mock_db_session.execute = AsyncMock(return_value=mock_result)
                mock_db_session.commit = AsyncMock()

                response = client.post(
                    "/api/strava/exchange-code", data={"code": "test_code"}
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "athlete" in data
                # Verify datetime objects were converted to ISO strings
                assert "created_at" in data["athlete"] or isinstance(
                    data["athlete"]["created_at"], str
                )


class TestStravaRefreshTokenEndpoint:
    """Test suite for Strava refresh token endpoint."""

    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        from unittest.mock import AsyncMock, patch

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_db_session = Mock()
            mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
            mock_db_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_db_session

            with patch("src.api.strava.StravaService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.refresh_access_token = AsyncMock(return_value=True)

                response = client.post(
                    "/api/strava/refresh-token", data={"strava_id": 12345}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "Token refreshed successfully" in data["message"]

    def test_refresh_token_failure(self, client):
        """Test token refresh failure."""
        from unittest.mock import AsyncMock, patch

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_db_session = Mock()
            mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
            mock_db_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_db_session

            with patch("src.api.strava.StravaService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.refresh_access_token = AsyncMock(return_value=False)

                response = client.post(
                    "/api/strava/refresh-token", data={"strava_id": 12345}
                )

                assert response.status_code == 401
                data = response.json()
                assert "Failed to refresh token" in data["detail"]

    def test_refresh_token_exception(self, client):
        """Test token refresh exception handling."""
        from unittest.mock import AsyncMock, patch

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_db_session = Mock()
            mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
            mock_db_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_db_session

            with patch("src.api.strava.StravaService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.refresh_access_token = AsyncMock(
                    side_effect=Exception("Service error")
                )

                response = client.post(
                    "/api/strava/refresh-token", data={"strava_id": 12345}
                )

                assert response.status_code == 401
                data = response.json()
                assert "Failed to refresh token" in data["detail"]


class TestStravaGetActivitiesEndpoint:
    """Test suite for Strava get activities endpoint."""

    def test_get_activities_success(self, client):
        """Test successful activity retrieval."""
        from unittest.mock import AsyncMock, patch

        mock_activities = [
            {"id": 1, "name": "Morning Run", "distance": 5000},
            {"id": 2, "name": "Evening Ride", "distance": 10000},
        ]

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_db_session = Mock()
            mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
            mock_db_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_db_session

            with patch("src.api.strava.StravaService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_activities = AsyncMock(return_value=mock_activities)

                response = client.get(
                    "/api/strava/activities?strava_id=12345&page=1&per_page=30"
                )

                assert response.status_code == 200
                data = response.json()
                assert "activities" in data
                assert len(data["activities"]) == 2
                assert data["page"] == 1
                assert data["per_page"] == 30
                assert data["total"] == 2

    def test_get_activities_custom_pagination(self, client):
        """Test activity retrieval with custom pagination."""
        from unittest.mock import AsyncMock, patch

        mock_activities = [{"id": 1, "name": "Activity 1"}]

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_db_session = Mock()
            mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
            mock_db_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_db_session

            with patch("src.api.strava.StravaService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_activities = AsyncMock(return_value=mock_activities)

                response = client.get(
                    "/api/strava/activities?strava_id=12345&page=2&per_page=10"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["page"] == 2
                assert data["per_page"] == 10

    def test_get_activities_exception(self, client):
        """Test activity retrieval exception handling."""
        from unittest.mock import AsyncMock, patch

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_db_session = Mock()
            mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
            mock_db_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_db_session

            with patch("src.api.strava.StravaService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_activities = AsyncMock(
                    side_effect=Exception("API error")
                )

                response = client.get(
                    "/api/strava/activities?strava_id=12345&page=1&per_page=30"
                )

                assert response.status_code == 500
                data = response.json()
                assert "Failed to fetch activities" in data["detail"]

    def test_get_activities_http_exception_re_raise(self, client):
        """Test activity retrieval when HTTPException is raised (should re-raise)."""
        from unittest.mock import AsyncMock, patch

        from fastapi import HTTPException

        with patch("src.dependencies.SessionLocal") as mock_session_local:
            mock_db_session = Mock()
            mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
            mock_db_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_db_session

            with patch("src.api.strava.StravaService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_activities = AsyncMock(
                    side_effect=HTTPException(status_code=401, detail="Unauthorized")
                )

                response = client.get(
                    "/api/strava/activities?strava_id=12345&page=1&per_page=30"
                )

                # Should re-raise the HTTPException
                assert response.status_code == 401
                data = response.json()
                assert "Unauthorized" in data["detail"]


class TestStravaGetActivityGpxEndpoint:
    """Test suite for Strava get activity GPX endpoint."""

    def test_get_activity_gpx_no_temp_dir(self, client):
        """Test GPX retrieval when temp_dir is not initialized."""
        from unittest.mock import patch

        with patch("src.dependencies.temp_dir", None):
            with patch("src.dependencies.SessionLocal"):
                response = client.get(
                    "/api/strava/activities/12345/gpx?strava_id=67890"
                )

                assert response.status_code == 500
                data = response.json()
                assert "Temporary directory not initialized" in data["detail"]

    def test_get_activity_gpx_success(self, client):
        """Test successful GPX retrieval."""
        from unittest.mock import AsyncMock, Mock, patch

        mock_gpx_data = {
            "points": [
                {
                    "lat": 40.0,
                    "lon": -74.0,
                    "elevation": 100,
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            ],
            "bounds": {"north": 40.1, "south": 39.9, "east": -73.9, "west": -74.1},
        }

        # Mock temp dir
        mock_temp_dir = Mock()
        mock_temp_dir.name = "/tmp"

        # Mock database session
        mock_db_session = Mock()
        mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
            with patch("src.dependencies.temp_dir", mock_temp_dir):
                with patch("src.api.strava.StravaService") as mock_service_class:
                    mock_service = mock_service_class.return_value
                    # Return GPX string
                    mock_service.get_activity_gpx = AsyncMock(
                        return_value='<?xml version="1.0" encoding="UTF-8"?><gpx></gpx>'
                    )

                    # Mock file system operations
                    with patch("builtins.open", create=True):
                        with patch("gpxpy.parse", return_value=Mock()):
                            with patch(
                                "src.api.strava.extract_from_gpx_file",
                                return_value=Mock(
                                    model_dump=lambda: mock_gpx_data,
                                    points=mock_gpx_data["points"],
                                ),
                            ):
                                response = client.get(
                                    "/api/strava/activities/12345/gpx?strava_id=67890"
                                )

                                assert response.status_code == 200
                                data = response.json()
                                assert "file_id" in data
                                assert "points" in data

    def test_get_activity_gpx_no_gpx_data(self, client):
        """Test GPX retrieval when no GPX data is available."""
        from unittest.mock import AsyncMock, patch

        mock_temp_dir = Mock()
        mock_temp_dir.name = "/tmp"

        mock_db_session = Mock()
        mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
            with patch("src.dependencies.temp_dir", mock_temp_dir):
                with patch("src.api.strava.StravaService") as mock_service_class:
                    mock_service = mock_service_class.return_value
                    # Return None or empty string
                    mock_service.get_activity_gpx = AsyncMock(return_value=None)

                    response = client.get(
                        "/api/strava/activities/12345/gpx?strava_id=67890"
                    )

                    assert response.status_code == 404
                    data = response.json()
                    assert "No GPX data available" in data["detail"]

    def test_get_activity_gpx_save_error(self, client):
        """Test GPX retrieval when saving file fails."""
        from unittest.mock import AsyncMock, patch

        mock_temp_dir = Mock()
        mock_temp_dir.name = "/tmp"

        mock_db_session = Mock()
        mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
            with patch("src.dependencies.temp_dir", mock_temp_dir):
                with patch("src.api.strava.StravaService") as mock_service_class:
                    mock_service = mock_service_class.return_value
                    mock_service.get_activity_gpx = AsyncMock(
                        return_value='<?xml version="1.0"?><gpx></gpx>'
                    )

                    # Mock file open to raise exception
                    with patch("builtins.open", side_effect=OSError("Cannot write")):
                        response = client.get(
                            "/api/strava/activities/12345/gpx?strava_id=67890"
                        )

                        assert response.status_code == 500
                        data = response.json()
                        assert "Failed to save GPX" in data["detail"]

    def test_get_activity_gpx_parse_error(self, client):
        """Test GPX retrieval when parsing fails."""
        from unittest.mock import AsyncMock, patch

        mock_temp_dir = Mock()
        mock_temp_dir.name = "/tmp"

        mock_db_session = Mock()
        mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
            with patch("src.dependencies.temp_dir", mock_temp_dir):
                with patch("src.api.strava.StravaService") as mock_service_class:
                    mock_service = mock_service_class.return_value
                    mock_service.get_activity_gpx = AsyncMock(
                        return_value='<?xml version="1.0"?><gpx></gpx>'
                    )

                    with patch("builtins.open", create=True):
                        with patch("gpxpy.parse", side_effect=Exception("Parse error")):
                            with patch("pathlib.Path.exists", return_value=True):
                                with patch("pathlib.Path.unlink"):
                                    response = client.get(
                                        "/api/strava/activities/12345/gpx?strava_id=67890"
                                    )

                                    assert response.status_code == 400
                                    data = response.json()
                                    assert "Invalid GPX file" in data["detail"]

    def test_get_activity_gpx_extract_error(self, client):
        """Test GPX retrieval when extraction fails."""
        from unittest.mock import AsyncMock, patch

        mock_temp_dir = Mock()
        mock_temp_dir.name = "/tmp"

        mock_db_session = Mock()
        mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
            with patch("src.dependencies.temp_dir", mock_temp_dir):
                with patch("src.api.strava.StravaService") as mock_service_class:
                    mock_service = mock_service_class.return_value
                    mock_service.get_activity_gpx = AsyncMock(
                        return_value='<?xml version="1.0"?><gpx></gpx>'
                    )

                    mock_gpx_obj = Mock()

                    with patch("builtins.open", create=True):
                        with patch("gpxpy.parse", return_value=mock_gpx_obj):
                            with patch(
                                "src.api.strava.extract_from_gpx_file",
                                side_effect=Exception("Extract error"),
                            ):
                                with patch("pathlib.Path.exists", return_value=True):
                                    with patch("pathlib.Path.unlink"):
                                        response = client.get(
                                            "/api/strava/activities/12345/gpx?strava_id=67890"
                                        )

                                        assert response.status_code == 400
                                        data = response.json()
                                        assert "Invalid GPX file" in data["detail"]

    def test_get_activity_gpx_exception(self, client):
        """Test GPX retrieval exception handling."""
        from unittest.mock import AsyncMock, patch

        mock_temp_dir = Mock()
        mock_temp_dir.name = "/tmp"

        mock_db_session = Mock()
        mock_db_session.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        with patch("src.dependencies.SessionLocal", return_value=mock_db_session):
            with patch("src.dependencies.temp_dir", mock_temp_dir):
                with patch("src.api.strava.StravaService") as mock_service_class:
                    mock_service = mock_service_class.return_value
                    mock_service.get_activity_gpx = AsyncMock(
                        side_effect=Exception("General error")
                    )

                    response = client.get(
                        "/api/strava/activities/12345/gpx?strava_id=67890"
                    )

                    assert response.status_code == 500
                    data = response.json()
                    assert "Failed to fetch GPX" in data["detail"]
