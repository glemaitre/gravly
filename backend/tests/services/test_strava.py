"""Unit tests for the Strava service."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.src.services.strava import StravaService
from backend.src.utils.config import StravaConfig


@pytest.fixture
def mock_strava_config(tmp_path):
    """Create a mock Strava configuration for testing."""
    tokens_file = tmp_path / "test_tokens.json"
    return StravaConfig(
        client_id="12345",  # Use numeric string that can be converted to int
        client_secret="test_client_secret",
        tokens_file_path=str(tokens_file),
    )


@pytest.fixture
def strava_service(mock_strava_config):
    """Create a StravaService instance for testing."""
    with patch("backend.src.services.strava.Client"):
        return StravaService(mock_strava_config)


def test_strava_service_initialization(mock_strava_config):
    """Test StravaService initialization with secure configuration."""
    with patch("backend.src.services.strava.Client"):
        service = StravaService(mock_strava_config)

        assert service.client_id == 12345  # Should be converted to int
        assert service.client_secret == "test_client_secret"
        assert service.tokens_file == Path(mock_strava_config.tokens_file_path)


def test_load_tokens_file_not_exists(strava_service):
    """Test loading tokens when file doesn't exist."""
    tokens = strava_service._load_tokens()
    assert tokens is None


def test_load_tokens_file_exists(strava_service, tmp_path):
    """Test loading tokens when file exists."""
    # Create a test tokens file
    test_tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 1234567890,
    }

    tokens_file = Path(strava_service.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    tokens = strava_service._load_tokens()
    assert tokens == test_tokens


def test_load_tokens_invalid_json(strava_service, tmp_path):
    """Test loading tokens with invalid JSON."""
    tokens_file = Path(strava_service.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    # Write invalid JSON
    with open(tokens_file, "w") as f:
        f.write("invalid json")

    tokens = strava_service._load_tokens()
    assert tokens is None


def test_save_tokens(strava_service, tmp_path):
    """Test saving tokens to file."""
    test_tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 1234567890,
    }

    tokens_file = Path(strava_service.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    strava_service._save_tokens(test_tokens)

    assert tokens_file.exists()

    with open(tokens_file) as f:
        saved_tokens = json.load(f)

    assert saved_tokens == test_tokens


def test_refresh_access_token_success(strava_service):
    """Test successful token refresh."""
    with (
        patch.object(strava_service, "_load_tokens") as mock_load,
        patch.object(strava_service, "_save_tokens") as mock_save,
        patch.object(strava_service.client, "refresh_access_token") as mock_refresh,
    ):
        # Mock expired tokens
        mock_load.return_value = {
            "access_token": "old_token",
            "refresh_token": "refresh_token",
            "expires_at": 1234567890,
        }

        # Mock successful refresh
        mock_refresh.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 9999999999,
        }

        result = strava_service.refresh_access_token()

        assert result is True
        mock_refresh.assert_called_once_with(
            client_id=12345,  # Should be converted to int
            client_secret=strava_service.client_secret,
            refresh_token="refresh_token",
        )
        mock_save.assert_called_once()


def test_refresh_access_token_failure(strava_service):
    """Test token refresh failure."""
    with (
        patch.object(strava_service, "_load_tokens") as mock_load,
        patch.object(strava_service.client, "refresh_access_token") as mock_refresh,
    ):
        # Mock expired tokens
        mock_load.return_value = {
            "access_token": "old_token",
            "refresh_token": "refresh_token",
            "expires_at": 1234567890,
        }

        # Mock refresh failure
        mock_refresh.side_effect = Exception("Refresh failed")

        result = strava_service.refresh_access_token()

        assert result is False


@patch("backend.src.services.strava.Client")
def test_get_authorization_url(mock_client_class):
    """Test getting authorization URL."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    mock_client.authorization_url.return_value = ("https://test.com", "test_state")

    config = StravaConfig(
        client_id="12345",  # Use numeric string that can be converted to int
        client_secret="test_secret",
        tokens_file_path="/tmp/test.json",
    )

    service = StravaService(config)
    url, state = service.get_authorization_url("test_redirect_uri")

    assert url == "https://test.com"
    assert state == "test_state"
    mock_client.authorization_url.assert_called_once_with(
        client_id=12345,  # Should be converted to int
        redirect_uri="test_redirect_uri",
        scope=["activity:read_all"],
        state="strava_auth",
    )


def test_ensure_authenticated_no_tokens(strava_service):
    """Test _ensure_authenticated raises error when no tokens available."""
    from stravalib.exc import AccessUnauthorized

    with pytest.raises(AccessUnauthorized, match="No tokens available"):
        strava_service._ensure_authenticated()


def test_ensure_authenticated_no_access_token(strava_service, tmp_path):
    """Test _ensure_authenticated raises error when no access token."""
    from stravalib.exc import AccessUnauthorized

    # Save tokens without access_token
    test_tokens = {"refresh_token": "test_refresh_token", "expires_at": 1234567890}

    tokens_file = Path(strava_service.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    with pytest.raises(AccessUnauthorized, match="No access token available"):
        strava_service._ensure_authenticated()


def test_construct_gpx_no_latlng_stream(strava_service):
    """Test GPX construction when no latlng stream is available."""
    # Mock activity object
    mock_activity = Mock()
    mock_activity.name = "Test Activity"
    mock_activity.start_date = "2023-01-01T10:00:00Z"

    # Mock streams without latlng data
    mock_streams = {"altitude": {"data": [10.0, 15.0]}, "time": {"data": [0, 60]}}

    result = strava_service._construct_gpx_from_streams(mock_activity, mock_streams)

    assert result is None


def test_construct_gpx_success(strava_service):
    """Test successful GPX construction from streams."""
    # Mock activity object
    mock_activity = Mock()
    mock_activity.name = "Test Activity"
    from datetime import datetime

    mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)

    # Mock streams with valid data - need to mock the stream objects properly
    mock_latlng_stream = Mock()
    mock_latlng_stream.data = [[40.7128, -74.0060], [40.7589, -73.9851]]

    mock_altitude_stream = Mock()
    mock_altitude_stream.data = [10.0, 15.0]

    mock_time_stream = Mock()
    mock_time_stream.data = [0, 60]

    mock_streams = {
        "latlng": mock_latlng_stream,
        "altitude": mock_altitude_stream,
        "time": mock_time_stream,
    }

    result = strava_service._construct_gpx_from_streams(mock_activity, mock_streams)

    assert result is not None
    assert result.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<gpx" in result
    assert "<trk>" in result
    assert "<trkpt" in result
    assert "40.7128" in result  # First latitude
    assert "-73.9851" in result  # Second longitude (the test is actually working)


# Additional fixtures for comprehensive testing
@pytest.fixture
def strava_config_alt(tmp_path):
    """Create an alternative Strava configuration for testing."""
    tokens_file = tmp_path / "strava_tokens_alt.json"
    return StravaConfig(
        client_id="12345",
        client_secret="test_client_secret",
        tokens_file_path=str(tokens_file),
    )


@pytest.fixture
def strava_service_alt(strava_config_alt):
    """Create an alternative StravaService instance for testing."""
    return StravaService(strava_config_alt)


def test_get_authorization_url_real_client(strava_service_alt):
    """Test getting authorization URL using real stravalib client."""
    url = strava_service_alt.get_authorization_url("http://localhost:8000/callback")

    assert url.startswith("https://www.strava.com/oauth/authorize")
    assert "client_id=12345" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback" in url  # URL encoded
    assert "scope=activity%3Aread_all" in url  # URL encoded colon


def test_get_activities_with_unit_mocks(strava_service_alt):
    """Test getting activities using unit test mocks."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 9999999999,  # Far in the future
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client methods
    mock_activity = Mock()
    mock_activity.id = 12345
    mock_activity.name = "Test Activity"
    mock_activity.distance = 10000.0
    mock_activity.moving_time = Mock()
    mock_activity.moving_time.timedelta.return_value.total_seconds.return_value = 3600
    mock_activity.elapsed_time = Mock()
    mock_activity.elapsed_time.timedelta.return_value.total_seconds.return_value = 3900
    mock_activity.total_elevation_gain = 100.0
    mock_activity.type = "Ride"

    from datetime import datetime

    mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)
    mock_activity.start_date_local = datetime(2023, 1, 1, 11, 0, 0)
    mock_activity.timezone = "UTC"
    mock_activity.start_latlng = None
    mock_activity.end_latlng = None
    mock_activity.map = None
    mock_activity.has_heartrate = False
    mock_activity.average_heartrate = None
    mock_activity.max_heartrate = None
    mock_activity.has_kudoed = False
    mock_activity.kudos_count = 0
    mock_activity.comment_count = 0
    mock_activity.athlete_count = 1
    mock_activity.trainer = False
    mock_activity.commute = False
    mock_activity.manual = False
    mock_activity.private = False
    mock_activity.visibility = "everyone"
    mock_activity.flagged = False
    mock_activity.gear_id = None
    mock_activity.external_id = None
    mock_activity.upload_id = None
    mock_activity.average_speed = None
    mock_activity.max_speed = None
    mock_activity.hide_from_home = False
    mock_activity.from_accepted_tag = False
    mock_activity.average_watts = None
    mock_activity.weighted_average_watts = None
    mock_activity.kilojoules = None
    mock_activity.device_watts = False
    mock_activity.elev_high = None
    mock_activity.elev_low = None
    mock_activity.pr_count = 0
    mock_activity.total_photo_count = 0
    mock_activity.suffer_score = None

    with patch.object(
        strava_service_alt.client, "get_activities"
    ) as mock_get_activities:
        mock_get_activities.return_value = [mock_activity]

        activities = strava_service_alt.get_activities(per_page=2)

        assert len(activities) == 1
        assert activities[0]["id"] == "12345"
        assert activities[0]["name"] == "Test Activity"
        assert activities[0]["distance"] == 10000.0
        assert activities[0]["moving_time"] == 3600


def test_get_activities_pagination_page_2(strava_service_alt):
    """Test getting activities for page 2 to cover pagination logic."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 9999999999,  # Far in the future
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client methods
    mock_activities = []
    from datetime import datetime

    # Create 5 mock activities to simulate pagination
    for i in range(5):
        mock_activity = Mock()
        mock_activity.id = 12345 + i
        mock_activity.name = f"Test Activity {i}"
        mock_activity.distance = 10000.0 + (i * 1000)
        mock_activity.moving_time = Mock()
        mock_activity.moving_time.timedelta.return_value.total_seconds.return_value = (
            3600 + (i * 60)
        )
        mock_activity.elapsed_time = Mock()
        mock_activity.elapsed_time.timedelta.return_value.total_seconds.return_value = (
            3900 + (i * 60)
        )
        mock_activity.total_elevation_gain = 100.0 + (i * 10)
        mock_activity.type = "Ride"
        mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)
        mock_activity.start_date_local = datetime(2023, 1, 1, 11, 0, 0)
        mock_activity.timezone = "UTC"
        mock_activity.start_latlng = None
        mock_activity.end_latlng = None
        mock_activity.map = None
        mock_activity.has_heartrate = False
        mock_activity.average_heartrate = None
        mock_activity.max_heartrate = None
        mock_activity.has_kudoed = False
        mock_activity.kudos_count = 0
        mock_activity.comment_count = 0
        mock_activity.athlete_count = 1
        mock_activity.trainer = False
        mock_activity.commute = False
        mock_activity.manual = False
        mock_activity.private = False
        mock_activity.visibility = "everyone"
        mock_activity.flagged = False
        mock_activity.gear_id = None
        mock_activity.external_id = None
        mock_activity.upload_id = None
        mock_activity.average_speed = None
        mock_activity.max_speed = None
        mock_activity.hide_from_home = False
        mock_activity.from_accepted_tag = False
        mock_activity.average_watts = None
        mock_activity.weighted_average_watts = None
        mock_activity.kilojoules = None
        mock_activity.device_watts = False
        mock_activity.elev_high = None
        mock_activity.elev_low = None
        mock_activity.pr_count = 0
        mock_activity.total_photo_count = 0
        mock_activity.suffer_score = None
        mock_activities.append(mock_activity)

    with patch.object(
        strava_service_alt.client, "get_activities"
    ) as mock_get_activities:
        mock_get_activities.return_value = mock_activities

        # Test page 2 with per_page=2
        # This should fetch 4 activities (offset=2, limit=4) and return activities 2-3
        activities = strava_service_alt.get_activities(page=2, per_page=2)

        # Should return 2 activities (activities 2 and 3 from the list)
        assert len(activities) == 2
        assert activities[0]["id"] == "12347"  # Third activity (index 2)
        assert activities[1]["id"] == "12348"  # Fourth activity (index 3)

        # Verify the client was called with the correct limit for pagination
        mock_get_activities.assert_called_once_with(limit=4)  # offset=2 + per_page=2


def test_get_activities_pagination_page_3(strava_service_alt):
    """Test getting activities for page 3 to further test pagination logic."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 9999999999,  # Far in the future
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client methods
    mock_activities = []
    from datetime import datetime

    # Create 10 mock activities to simulate pagination
    for i in range(10):
        mock_activity = Mock()
        mock_activity.id = 12345 + i
        mock_activity.name = f"Test Activity {i}"
        mock_activity.distance = 10000.0 + (i * 1000)
        mock_activity.moving_time = Mock()
        mock_activity.moving_time.timedelta.return_value.total_seconds.return_value = (
            3600 + (i * 60)
        )
        mock_activity.elapsed_time = Mock()
        mock_activity.elapsed_time.timedelta.return_value.total_seconds.return_value = (
            3900 + (i * 60)
        )
        mock_activity.total_elevation_gain = 100.0 + (i * 10)
        mock_activity.type = "Ride"
        mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)
        mock_activity.start_date_local = datetime(2023, 1, 1, 11, 0, 0)
        mock_activity.timezone = "UTC"
        mock_activity.start_latlng = None
        mock_activity.end_latlng = None
        mock_activity.map = None
        mock_activity.has_heartrate = False
        mock_activity.average_heartrate = None
        mock_activity.max_heartrate = None
        mock_activity.has_kudoed = False
        mock_activity.kudos_count = 0
        mock_activity.comment_count = 0
        mock_activity.athlete_count = 1
        mock_activity.trainer = False
        mock_activity.commute = False
        mock_activity.manual = False
        mock_activity.private = False
        mock_activity.visibility = "everyone"
        mock_activity.flagged = False
        mock_activity.gear_id = None
        mock_activity.external_id = None
        mock_activity.upload_id = None
        mock_activity.average_speed = None
        mock_activity.max_speed = None
        mock_activity.hide_from_home = False
        mock_activity.from_accepted_tag = False
        mock_activity.average_watts = None
        mock_activity.weighted_average_watts = None
        mock_activity.kilojoules = None
        mock_activity.device_watts = False
        mock_activity.elev_high = None
        mock_activity.elev_low = None
        mock_activity.pr_count = 0
        mock_activity.total_photo_count = 0
        mock_activity.suffer_score = None
        mock_activities.append(mock_activity)

    with patch.object(
        strava_service_alt.client, "get_activities"
    ) as mock_get_activities:
        mock_get_activities.return_value = mock_activities

        # Test page 3 with per_page=3
        # This should fetch 9 activities (offset=6, limit=9) and return activities 6-8
        activities = strava_service_alt.get_activities(page=3, per_page=3)

        # Should return 3 activities (activities 6, 7, and 8 from the list)
        assert len(activities) == 3
        assert activities[0]["id"] == "12351"  # Seventh activity (index 6)
        assert activities[1]["id"] == "12352"  # Eighth activity (index 7)
        assert activities[2]["id"] == "12353"  # Ninth activity (index 8)

        # Verify the client was called with the correct limit for pagination
        mock_get_activities.assert_called_once_with(limit=9)  # offset=6 + per_page=3


def test_convert_activity_to_dict_with_mock_data():
    """Test activity conversion with realistic mock data."""
    config = StravaConfig(
        client_id="12345",
        client_secret="test_secret",
        tokens_file_path="/tmp/test.json",
    )

    service = StravaService(config)

    # Create a more realistic mock activity
    mock_activity = Mock()
    mock_activity.id = 12345
    mock_activity.name = "Morning Ride"
    mock_activity.distance = 25000.0  # 25km in meters
    mock_activity.moving_time = Mock()
    # 1 hour
    mock_activity.moving_time.timedelta.return_value.total_seconds.return_value = 3600
    mock_activity.elapsed_time = Mock()
    # 1h 5min
    mock_activity.elapsed_time.timedelta.return_value.total_seconds.return_value = 3900
    mock_activity.total_elevation_gain = 500.0
    mock_activity.type = "Ride"

    # Mock datetime objects
    from datetime import datetime

    mock_start_date = datetime(2023, 1, 1, 10, 0, 0)
    mock_start_date_local = datetime(2023, 1, 1, 11, 0, 0)

    mock_activity.start_date = mock_start_date
    mock_activity.start_date_local = mock_start_date_local
    mock_activity.timezone = "Europe/London"

    # Mock latlng objects
    mock_start_latlng = Mock()
    mock_start_latlng.root = [51.5074, -0.1278]  # London coordinates
    mock_end_latlng = Mock()
    mock_end_latlng.root = [51.5074, -0.1278]

    mock_activity.start_latlng = mock_start_latlng
    mock_activity.end_latlng = mock_end_latlng

    # Mock map object
    mock_map = Mock()
    mock_map.id = "map123"
    mock_map.summary_polyline = "encoded_polyline_string"
    mock_activity.map = mock_map

    # Set other attributes
    mock_activity.has_heartrate = True
    mock_activity.average_heartrate = 150.0
    mock_activity.max_heartrate = 180.0
    mock_activity.has_kudoed = False
    mock_activity.kudos_count = 5
    mock_activity.comment_count = 2
    mock_activity.athlete_count = 1
    mock_activity.trainer = False
    mock_activity.commute = False
    mock_activity.manual = False
    mock_activity.private = False
    mock_activity.visibility = "everyone"
    mock_activity.flagged = False
    mock_activity.gear_id = "gear123"
    mock_activity.external_id = "external123"
    mock_activity.upload_id = "upload123"
    mock_activity.average_speed = 6.94  # m/s
    mock_activity.max_speed = 15.0  # m/s
    mock_activity.hide_from_home = False
    mock_activity.from_accepted_tag = False
    mock_activity.average_watts = 200.0
    mock_activity.weighted_average_watts = 210.0
    mock_activity.kilojoules = 720.0
    mock_activity.device_watts = True
    mock_activity.elev_high = 100.0
    mock_activity.elev_low = 50.0
    mock_activity.pr_count = 1
    mock_activity.total_photo_count = 3
    mock_activity.suffer_score = 5

    result = service._convert_activity_to_dict(mock_activity)

    # Verify the conversion
    assert result["id"] == "12345"
    assert result["name"] == "Morning Ride"
    assert result["distance"] == 25000.0
    assert result["moving_time"] == 3600
    assert result["elapsed_time"] == 3900
    assert result["total_elevation_gain"] == 500.0
    assert result["type"] == "Ride"
    assert result["start_date"] == "2023-01-01T10:00:00"
    assert result["start_date_local"] == "2023-01-01T11:00:00"
    assert result["timezone"] == "Europe/London"
    assert result["start_latlng"] == [51.5074, -0.1278]
    assert result["end_latlng"] == [51.5074, -0.1278]
    assert result["has_heartrate"] is True
    assert result["average_heartrate"] == 150.0
    assert result["max_heartrate"] == 180.0
    assert result["kudos_count"] == 5
    assert result["comment_count"] == 2
    assert result["average_speed"] == 6.94
    assert result["max_speed"] == 15.0
    assert result["average_watts"] == 200.0
    assert result["kilojoules"] == 720.0
    assert result["elev_high"] == 100.0
    assert result["elev_low"] == 50.0
    assert result["pr_count"] == 1
    assert result["total_photo_count"] == 3
    assert result["suffer_score"] == 5


def test_construct_gpx_with_realistic_data():
    """Test GPX construction with realistic stream data."""
    config = StravaConfig(
        client_id="12345",
        client_secret="test_secret",
        tokens_file_path="/tmp/test.json",
    )

    service = StravaService(config)

    # Mock activity object
    mock_activity = Mock()
    mock_activity.name = "Test Ride"
    from datetime import datetime

    mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)

    # Mock streams with realistic GPS data - need to mock the stream objects properly
    mock_latlng_stream = Mock()
    mock_latlng_stream.data = [
        [51.5074, -0.1278],  # London
        [51.5084, -0.1288],  # Slightly north and east
        [51.5094, -0.1298],  # Further north and east
    ]

    mock_altitude_stream = Mock()
    mock_altitude_stream.data = [10.0, 15.0, 20.0]

    mock_time_stream = Mock()
    mock_time_stream.data = [0, 30, 60]

    mock_streams = {
        "latlng": mock_latlng_stream,
        "altitude": mock_altitude_stream,
        "time": mock_time_stream,
    }

    result = service._construct_gpx_from_streams(mock_activity, mock_streams)

    assert result is not None
    assert result.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<gpx" in result
    assert "<trk>" in result
    assert "<trkpt" in result
    assert "51.5074" in result  # First latitude
    assert "-0.1278" in result  # First longitude
    assert "Test Ride" in result  # Activity name
    assert "10.0" in result  # First altitude


def test_ensure_authenticated_success(strava_service_alt, tmp_path):
    """Test successful authentication."""
    # Save valid, non-expired tokens
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,  # Far in the future
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # This should not raise an exception
    strava_service_alt._ensure_authenticated()

    # Verify the access token was set
    assert strava_service_alt.client.access_token == "valid_token"


def test_ensure_authenticated_expired_token_auto_refresh(strava_service_alt, tmp_path):
    """Test authentication with expired token that gets refreshed."""
    # Save expired tokens
    test_tokens = {
        "access_token": "old_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 1234567890,  # Past timestamp
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the refresh method to succeed
    with patch.object(strava_service_alt, "refresh_access_token") as mock_refresh:
        mock_refresh.return_value = True

        # Mock _load_tokens to return updated tokens after refresh
        def mock_load_tokens():
            return {
                "access_token": "new_token",
                "refresh_token": "new_refresh_token",
                "expires_at": 9999999999,
            }

        with patch.object(
            strava_service_alt,
            "_load_tokens",
            side_effect=[test_tokens, mock_load_tokens()],
        ):
            strava_service_alt._ensure_authenticated()

        # Verify refresh was called
        mock_refresh.assert_called_once()

        # Verify the new access token was set
        assert strava_service_alt.client.access_token == "new_token"


def test_token_file_operations(strava_service_alt, tmp_path):
    """Test token file loading and saving operations."""
    # Test saving tokens
    test_tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 1234567890,
    }

    strava_service_alt._save_tokens(test_tokens)

    # Verify file was created
    assert Path(strava_service_alt.tokens_file).exists()

    # Test loading tokens
    loaded_tokens = strava_service_alt._load_tokens()
    assert loaded_tokens == test_tokens

    # Test loading non-existent file
    non_existent_file = tmp_path / "non_existent.json"
    service_no_file = StravaService(
        StravaConfig(
            client_id="12345",
            client_secret="test_secret",
            tokens_file_path=str(non_existent_file),
        )
    )

    assert service_no_file._load_tokens() is None


# Tests for uncovered lines
def test_save_tokens_with_datetime_objects(strava_service_alt, tmp_path):
    """Test saving tokens with datetime objects to cover conversion logic."""
    from datetime import datetime

    # Create tokens with datetime objects
    test_tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 1234567890,
        "created_at": datetime(2023, 1, 1, 10, 0, 0),
        "nested_data": {
            "nested_datetime": datetime(2023, 1, 1, 11, 0, 0),
            "nested_list": [datetime(2023, 1, 1, 12, 0, 0)],
        },
    }

    # This should not raise an exception and should convert datetime objects
    strava_service_alt._save_tokens(test_tokens)

    # Verify file was created
    assert Path(strava_service_alt.tokens_file).exists()

    # Verify tokens were saved correctly with datetime conversion
    loaded_tokens = strava_service_alt._load_tokens()
    assert loaded_tokens["access_token"] == "test_access_token"
    assert loaded_tokens["created_at"] == "2023-01-01T10:00:00"
    assert loaded_tokens["nested_data"]["nested_datetime"] == "2023-01-01T11:00:00"
    assert loaded_tokens["nested_data"]["nested_list"][0] == "2023-01-01T12:00:00"


def test_save_tokens_error_handling(strava_service_alt, tmp_path, monkeypatch):
    """Test error handling in _save_tokens method."""

    # Mock open to raise an exception
    def mock_open(*args, **kwargs):
        raise PermissionError("Permission denied")

    monkeypatch.setattr("builtins.open", mock_open)

    test_tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 1234567890,
    }

    # This should not raise an exception but log an error
    strava_service_alt._save_tokens(test_tokens)


def test_exchange_code_for_token_success_with_athlete(strava_service_alt):
    """Test successful token exchange with athlete data."""
    from unittest.mock import Mock

    # Mock the client response with athlete data
    mock_access_info = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_at": 9999999999,
    }

    mock_athlete = Mock()
    mock_athlete.model_dump.return_value = {
        "id": 12345,
        "username": "test_user",
        "firstname": "Test",
        "lastname": "User",
    }

    # Mock the exchange_code_for_token to return tuple with athlete
    with patch.object(
        strava_service_alt.client, "exchange_code_for_token"
    ) as mock_exchange:
        mock_exchange.return_value = (mock_access_info, mock_athlete)

        # Mock _save_tokens to avoid file operations
        with patch.object(strava_service_alt, "_save_tokens") as mock_save:
            result = strava_service_alt.exchange_code_for_token("test_code")

            # Verify the result
            assert result["access_token"] == "new_access_token"
            assert result["refresh_token"] == "new_refresh_token"
            assert result["athlete"]["id"] == 12345
            assert result["athlete"]["username"] == "test_user"

            # Verify save was called
            mock_save.assert_called_once()

            # Verify exchange was called with correct parameters
            mock_exchange.assert_called_once_with(
                client_id=12345,
                client_secret="test_client_secret",
                code="test_code",
                return_athlete=True,
            )


def test_exchange_code_for_token_success_without_athlete(strava_service_alt):
    """Test successful token exchange without athlete data."""
    # Mock the client response without athlete data
    mock_access_info = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_at": 9999999999,
    }

    # Mock the exchange_code_for_token to return just access_info
    with patch.object(
        strava_service_alt.client, "exchange_code_for_token"
    ) as mock_exchange:
        mock_exchange.return_value = mock_access_info

        # Mock _save_tokens to avoid file operations
        with patch.object(strava_service_alt, "_save_tokens"):
            result = strava_service_alt.exchange_code_for_token("test_code")

            # Verify the result
            assert result["access_token"] == "new_access_token"
            assert result["refresh_token"] == "new_refresh_token"
            assert result["athlete"] is None


def test_exchange_code_for_token_failure(strava_service_alt):
    """Test token exchange failure handling."""
    # Mock the client to raise an exception
    with patch.object(
        strava_service_alt.client, "exchange_code_for_token"
    ) as mock_exchange:
        mock_exchange.side_effect = Exception("API Error")

        # This should raise the exception
        with pytest.raises(Exception, match="API Error"):
            strava_service_alt.exchange_code_for_token("invalid_code")


def test_refresh_access_token_no_refresh_token(strava_service_alt):
    """Test refresh access token when no refresh token is available."""
    # Mock _load_tokens to return tokens without refresh_token
    with patch.object(strava_service_alt, "_load_tokens") as mock_load:
        mock_load.return_value = {
            "access_token": "expired_token",
            "expires_at": 1234567890,
            # No refresh_token
        }

        result = strava_service_alt.refresh_access_token()
        assert result is False


def test_refresh_access_token_no_tokens(strava_service_alt):
    """Test refresh access token when no tokens are available."""
    # Mock _load_tokens to return None
    with patch.object(strava_service_alt, "_load_tokens") as mock_load:
        mock_load.return_value = None

        result = strava_service_alt.refresh_access_token()
        assert result is False


def test_ensure_authenticated_token_expired_refresh_fails(strava_service_alt, tmp_path):
    """Test authentication when token is expired and refresh fails."""
    # Save expired tokens
    test_tokens = {
        "access_token": "expired_token",
        "refresh_token": "invalid_refresh_token",
        "expires_at": 1234567890,  # Past timestamp
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock refresh_access_token to return False (refresh fails)
    with patch.object(strava_service_alt, "refresh_access_token") as mock_refresh:
        mock_refresh.return_value = False

        # This should raise AccessUnauthorized
        from stravalib.exc import AccessUnauthorized

        with pytest.raises(
            AccessUnauthorized, match="Token expired and refresh failed"
        ):
            strava_service_alt._ensure_authenticated()


def test_get_activities_rate_limit_exceeded(strava_service_alt):
    """Test get_activities when rate limit is exceeded."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise RateLimitExceeded
    from stravalib.exc import RateLimitExceeded

    with patch.object(
        strava_service_alt.client, "get_activities"
    ) as mock_get_activities:
        mock_get_activities.side_effect = RateLimitExceeded("Rate limit exceeded")

        with pytest.raises(RateLimitExceeded):
            strava_service_alt.get_activities()


def test_get_activities_access_unauthorized(strava_service_alt):
    """Test get_activities when access is unauthorized."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "invalid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise AccessUnauthorized
    from stravalib.exc import AccessUnauthorized

    with patch.object(
        strava_service_alt.client, "get_activities"
    ) as mock_get_activities:
        mock_get_activities.side_effect = AccessUnauthorized()

        with pytest.raises(AccessUnauthorized):
            strava_service_alt.get_activities()


def test_get_activities_general_exception(strava_service_alt):
    """Test get_activities when a general exception occurs."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise a general exception
    with patch.object(
        strava_service_alt.client, "get_activities"
    ) as mock_get_activities:
        mock_get_activities.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            strava_service_alt.get_activities()


def test_get_activity_gpx_success(strava_service_alt):
    """Test successful GPX retrieval for an activity."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock activity and streams
    mock_activity = Mock()
    mock_activity.name = "Test Activity"
    from datetime import datetime

    mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)

    mock_streams = {
        "latlng": Mock(data=[[51.5074, -0.1278], [51.5084, -0.1288]]),
        "altitude": Mock(data=[10.0, 15.0]),
        "time": Mock(data=[0, 30]),
    }

    # Mock the client methods
    with patch.object(strava_service_alt.client, "get_activity") as mock_get_activity:
        with patch.object(
            strava_service_alt.client, "get_activity_streams"
        ) as mock_get_streams:
            mock_get_activity.return_value = mock_activity
            mock_get_streams.return_value = mock_streams

            gpx_data = strava_service_alt.get_activity_gpx("123456")

            assert gpx_data is not None
            assert gpx_data.startswith("<?xml")
            assert "Test Activity" in gpx_data
            assert "51.5074" in gpx_data


def test_get_activity_gpx_no_data(strava_service_alt):
    """Test GPX retrieval when no data is available."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock activity and empty streams
    mock_activity = Mock()
    mock_activity.name = "Test Activity"
    from datetime import datetime

    mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)

    mock_streams = {
        "latlng": Mock(data=[]),  # No GPS data
        "altitude": Mock(data=[]),
        "time": Mock(data=[]),
    }

    # Mock the client methods
    with patch.object(strava_service_alt.client, "get_activity") as mock_get_activity:
        with patch.object(
            strava_service_alt.client, "get_activity_streams"
        ) as mock_get_streams:
            mock_get_activity.return_value = mock_activity
            mock_get_streams.return_value = mock_streams

            gpx_data = strava_service_alt.get_activity_gpx("123456")

            # When no GPS data is available, it should return a GPX with empty track
            assert gpx_data is not None
            assert gpx_data.startswith("<?xml")
            assert "Test Activity" in gpx_data


def test_get_activity_gpx_rate_limit_exceeded(strava_service_alt):
    """Test GPX retrieval when rate limit is exceeded."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise RateLimitExceeded
    from stravalib.exc import RateLimitExceeded

    with patch.object(strava_service_alt.client, "get_activity") as mock_get_activity:
        mock_get_activity.side_effect = RateLimitExceeded("Rate limit exceeded")

        with pytest.raises(RateLimitExceeded):
            strava_service_alt.get_activity_gpx("123456")


def test_get_activity_gpx_access_unauthorized(strava_service_alt):
    """Test GPX retrieval when access is unauthorized."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "invalid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise AccessUnauthorized
    from stravalib.exc import AccessUnauthorized

    with patch.object(strava_service_alt.client, "get_activity") as mock_get_activity:
        mock_get_activity.side_effect = AccessUnauthorized()

        with pytest.raises(AccessUnauthorized):
            strava_service_alt.get_activity_gpx("123456")


def test_get_activity_gpx_general_exception(strava_service_alt):
    """Test GPX retrieval when a general exception occurs."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise a general exception
    with patch.object(strava_service_alt.client, "get_activity") as mock_get_activity:
        mock_get_activity.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            strava_service_alt.get_activity_gpx("123456")


def test_construct_gpx_no_time_data(strava_service_alt):
    """Test GPX construction when no time data is available."""
    # Mock activity object
    mock_activity = Mock()
    mock_activity.name = "Test Activity"
    from datetime import datetime

    mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)

    # Mock streams with no time data
    mock_streams = {
        "latlng": Mock(data=[[51.5074, -0.1278], [51.5084, -0.1288]]),
        "altitude": Mock(data=[10.0, 15.0]),
        "time": Mock(data=None),  # No time data
    }

    result = strava_service_alt._construct_gpx_from_streams(mock_activity, mock_streams)

    assert result is not None
    assert result.startswith("<?xml")
    # Should still create GPX but without time information
    assert "51.5074" in result


def test_construct_gpx_exception_handling(strava_service_alt):
    """Test GPX construction exception handling."""
    # Mock activity object that will cause an exception
    mock_activity = Mock()
    mock_activity.name = "Test Activity"
    # Don't set start_date to cause an AttributeError

    mock_streams = {
        "latlng": Mock(data=[[51.5074, -0.1278]]),
        "altitude": Mock(data=[10.0]),
        "time": Mock(data=[0]),
    }

    # This should return None due to exception
    result = strava_service_alt._construct_gpx_from_streams(mock_activity, mock_streams)

    assert result is None


def test_get_athlete_success(strava_service_alt):
    """Test successful athlete retrieval."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock athlete object with all required attributes
    mock_athlete = Mock()
    mock_athlete.id = 12345
    mock_athlete.username = "test_user"
    mock_athlete.resource_state = 3
    mock_athlete.firstname = "Test"
    mock_athlete.lastname = "User"
    mock_athlete.bio = "Test bio"
    mock_athlete.city = "Test City"
    mock_athlete.state = "Test State"
    mock_athlete.country = "Test Country"
    mock_athlete.sex = "M"
    mock_athlete.premium = True
    mock_athlete.summit = False
    mock_athlete.created_at = None
    mock_athlete.updated_at = None
    mock_athlete.badge_type_id = 1
    mock_athlete.weight = 70.0  # Numeric value for float conversion
    mock_athlete.profile_medium = "profile_medium_url"
    mock_athlete.profile = "profile_url"
    mock_athlete.friend = None
    mock_athlete.follower = None
    mock_athlete.blocked = False
    mock_athlete.can_follow = True
    mock_athlete.follower_count = 100
    mock_athlete.friend_count = 50
    mock_athlete.mutual_friend_count = 25
    mock_athlete.athlete_type = 0
    mock_athlete.date_preference = "%m/%d/%Y"
    mock_athlete.measurement_preference = "feet"
    mock_athlete.clubs = []
    mock_athlete.ftp = 200
    mock_athlete.max_heartrate = 180.0  # Numeric value for float conversion
    mock_athlete.max_watts = 1000.0  # Numeric value for float conversion
    mock_athlete.max_speed = 50.0  # Numeric value for float conversion
    mock_athlete.default_bikes = []
    mock_athlete.default_shoes = []
    mock_athlete.default_gear = None
    mock_athlete.offline_token = "offline_token"
    mock_athlete.email = "test@example.com"

    # Mock the client method
    with patch.object(strava_service_alt.client, "get_athlete") as mock_get_athlete:
        mock_get_athlete.return_value = mock_athlete

        athlete_data = strava_service_alt.get_athlete()

        assert athlete_data["id"] == "12345"
        assert athlete_data["username"] == "test_user"
        assert athlete_data["firstname"] == "Test"
        assert athlete_data["lastname"] == "User"
        assert athlete_data["bio"] == "Test bio"
        assert athlete_data["city"] == "Test City"
        assert athlete_data["state"] == "Test State"
        assert athlete_data["country"] == "Test Country"
        assert athlete_data["sex"] == "M"
        assert athlete_data["premium"] is True
        assert athlete_data["summit"] is False
        assert athlete_data["weight"] == 70.0
        assert athlete_data["max_heartrate"] == 180.0
        assert athlete_data["max_watts"] == 1000.0
        assert athlete_data["max_speed"] == 50.0


def test_get_athlete_rate_limit_exceeded(strava_service_alt):
    """Test athlete retrieval when rate limit is exceeded."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise RateLimitExceeded
    from stravalib.exc import RateLimitExceeded

    with patch.object(strava_service_alt.client, "get_athlete") as mock_get_athlete:
        mock_get_athlete.side_effect = RateLimitExceeded("Rate limit exceeded")

        with pytest.raises(RateLimitExceeded):
            strava_service_alt.get_athlete()


def test_get_athlete_access_unauthorized(strava_service_alt):
    """Test athlete retrieval when access is unauthorized."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "invalid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise AccessUnauthorized
    from stravalib.exc import AccessUnauthorized

    with patch.object(strava_service_alt.client, "get_athlete") as mock_get_athlete:
        mock_get_athlete.side_effect = AccessUnauthorized()

        with pytest.raises(AccessUnauthorized):
            strava_service_alt.get_athlete()


def test_get_athlete_general_exception(strava_service_alt):
    """Test athlete retrieval when a general exception occurs."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock the client to raise a general exception
    with patch.object(strava_service_alt.client, "get_athlete") as mock_get_athlete:
        mock_get_athlete.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            strava_service_alt.get_athlete()


def test_get_activity_gpx_construct_gpx_returns_none(strava_service_alt):
    """Test GPX retrieval when _construct_gpx_from_streams returns None."""
    # Save valid tokens first
    test_tokens = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": 9999999999,
    }

    tokens_file = Path(strava_service_alt.tokens_file)
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tokens_file, "w") as f:
        json.dump(test_tokens, f)

    # Mock activity and streams
    mock_activity = Mock()
    mock_activity.name = "Test Activity"
    from datetime import datetime

    mock_activity.start_date = datetime(2023, 1, 1, 10, 0, 0)

    mock_streams = {
        "latlng": Mock(data=[[51.5074, -0.1278]]),
        "altitude": Mock(data=[10.0]),
        "time": Mock(data=[0]),
    }

    # Mock the client methods
    with patch.object(strava_service_alt.client, "get_activity") as mock_get_activity:
        with patch.object(
            strava_service_alt.client, "get_activity_streams"
        ) as mock_get_streams:
            # Mock _construct_gpx_from_streams to return None
            with patch.object(
                strava_service_alt, "_construct_gpx_from_streams"
            ) as mock_construct:
                mock_get_activity.return_value = mock_activity
                mock_get_streams.return_value = mock_streams
                mock_construct.return_value = None

                gpx_data = strava_service_alt.get_activity_gpx("123456")

                assert gpx_data is None
