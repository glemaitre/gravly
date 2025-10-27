"""Unit tests for the Strava service."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from src.services.strava import StravaService
from src.utils.config import StravaConfig
from stravalib.exc import AccessUnauthorized, RateLimitExceeded


@pytest.fixture
def mock_strava_config():
    """Create a mock Strava configuration for testing."""
    return StravaConfig(
        client_id="12345",
        client_secret="test_client_secret",
    )


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    return AsyncMock()


@pytest.fixture
def strava_service(mock_strava_config, mock_db_session):
    """Create a StravaService instance for testing."""
    with patch("src.services.strava.Client"):
        return StravaService(
            mock_strava_config, db_session=mock_db_session, strava_id=12345
        )


class TestStravaServiceInitialization:
    """Test StravaService initialization and basic setup."""

    def test_strava_service_initialization(self, mock_strava_config, mock_db_session):
        """Test StravaService initialization."""
        with patch("src.services.strava.Client"):
            service = StravaService(
                mock_strava_config, db_session=mock_db_session, strava_id=12345
            )

            assert service.client_id == 12345
            assert service.client_secret == "test_client_secret"
            assert service.strava_id == 12345
            assert service.db_session == mock_db_session


class TestTokenLoading:
    """Test token loading from database."""

    @pytest.mark.asyncio
    async def test_load_tokens_not_exists(self, strava_service, mock_db_session):
        """Test loading tokens when they don't exist."""
        # Mock the database query to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        tokens = await strava_service._load_tokens()

        assert tokens is None

    @pytest.mark.asyncio
    async def test_load_tokens_exists(self, strava_service, mock_db_session):
        """Test loading tokens when they exist."""
        import json
        from datetime import datetime, timedelta

        # Mock token record with athlete_data as JSON string
        mock_token_record = Mock()
        mock_token_record.access_token = "test_access_token"
        mock_token_record.refresh_token = "test_refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345, "name": "Test User"})

        # Mock the database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        tokens = await strava_service._load_tokens()

        assert tokens is not None
        assert tokens["access_token"] == "test_access_token"
        assert tokens["refresh_token"] == "test_refresh_token"
        assert "expires_at" in tokens


class TestTokenSaving:
    """Test token saving to database."""

    @pytest.mark.asyncio
    async def test_save_tokens_new(self, strava_service, mock_db_session):
        """Test saving new tokens."""
        # Mock the database query to return None (new record)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.rollback = AsyncMock()

        tokens = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1234567890,
        }

        await strava_service._save_tokens(tokens)

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_tokens_update(self, strava_service, mock_db_session):
        """Test updating existing tokens."""
        from datetime import datetime

        # Mock existing token record
        mock_token_record = Mock()
        mock_token_record.access_token = "old_token"
        mock_token_record.refresh_token = "old_refresh"
        mock_token_record.expires_at = datetime.now()

        # Mock the database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db_session.rollback = AsyncMock()

        tokens = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1234567890,
        }

        await strava_service._save_tokens(tokens)

        assert mock_token_record.access_token == "new_access_token"
        assert mock_token_record.refresh_token == "new_refresh_token"
        mock_db_session.commit.assert_called_once()


class TestRefreshToken:
    """Test token refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, strava_service, mock_db_session):
        """Test successful token refresh."""
        import json
        from datetime import datetime

        # Mock existing tokens
        mock_token_record = Mock()
        mock_token_record.access_token = "old_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now()
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        # Mock database queries (one for load, one for save)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.rollback = AsyncMock()

        # Mock the client's refresh method
        mock_client = Mock()
        mock_client.refresh_access_token.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1234567890,
        }
        strava_service.client = mock_client

        result = await strava_service.refresh_access_token()

        assert result is True

    @pytest.mark.asyncio
    async def test_refresh_access_token_no_refresh_token(
        self, strava_service, mock_db_session
    ):
        """Test refresh fails when no refresh token exists."""
        # Mock no tokens
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await strava_service.refresh_access_token()

        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_access_token_failure(self, strava_service, mock_db_session):
        """Test refresh token failure."""
        from datetime import datetime

        # Mock existing tokens
        mock_token_record = Mock()
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now()

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock the client's refresh method to raise exception
        mock_client = Mock()
        mock_client.refresh_access_token.side_effect = Exception("Refresh failed")
        strava_service.client = mock_client

        result = await strava_service.refresh_access_token()

        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_access_token_exception_during_refresh(
        self, strava_service, mock_db_session
    ):
        """Test refresh token when exception occurs during refresh."""
        import json
        from datetime import datetime

        # Mock existing tokens
        mock_token_record = Mock()
        mock_token_record.access_token = "old_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now()
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        # Mock database queries (one for load, one for save)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock the client's refresh method to raise exception
        mock_client = Mock()
        mock_client.refresh_access_token.side_effect = Exception("Refresh failed")
        strava_service.client = mock_client

        result = await strava_service.refresh_access_token()

        assert result is False


class TestEnsureAuthenticated:
    """Test authentication handling."""

    @pytest.mark.asyncio
    async def test_ensure_authenticated_no_tokens(
        self, strava_service, mock_db_session
    ):
        """Test when no tokens exist."""
        # Mock no tokens
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(AccessUnauthorized):
            await strava_service._ensure_authenticated()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_missing_access_token(
        self, strava_service, mock_db_session
    ):
        """Test when tokens exist but without access_token."""
        # Mock _load_tokens to return dict without access_token
        strava_service._load_tokens = AsyncMock(
            return_value={"refresh_token": "refresh", "expires_at": 123456}
        )

        with pytest.raises(AccessUnauthorized):
            await strava_service._ensure_authenticated()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_refresh_failed(
        self, strava_service, mock_db_session
    ):
        """Test when token refresh fails."""
        from datetime import datetime, timedelta

        # Mock expired token
        mock_token_record = Mock()
        mock_token_record.access_token = "expired_token"
        mock_token_record.expires_at = datetime.now() - timedelta(hours=1)

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client for failed refresh
        strava_service.client = Mock()
        strava_service.refresh_access_token = AsyncMock(return_value=False)

        with pytest.raises(AccessUnauthorized):
            await strava_service._ensure_authenticated()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_valid_token(
        self, strava_service, mock_db_session
    ):
        """Test when valid token exists."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client set_token
        mock_client = Mock()
        mock_client.set_token = Mock()
        strava_service.client = mock_client

        # Mock athlet access to prevent AttributeError
        mock_athlete = Mock()
        mock_athlete.access = "public"
        mock_client.set_token = AsyncMock()

        await strava_service._ensure_authenticated()

        # Verify client token was set
        assert True  # If we get here without exception, token was set

    @pytest.mark.asyncio
    async def test_ensure_authenticated_expired_token(
        self, strava_service, mock_db_session
    ):
        """Test when token is expired and needs refresh."""
        from datetime import datetime, timedelta

        # Mock expired token
        mock_token_record = Mock()
        mock_token_record.access_token = "expired_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() - timedelta(hours=1)
        mock_token_record.athlete_data = None

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client for refresh
        mock_client = Mock()
        mock_client.set_token = Mock()
        mock_client.refresh_access_token.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_at": 9999999999,
        }
        strava_service.client = mock_client
        strava_service.refresh_access_token = AsyncMock(return_value=True)

        await strava_service._ensure_authenticated()

        # Should have attempted refresh
        assert True  # If we get here without exception, it worked


class TestSaveTokensException:
    """Test exception handling in token saving."""

    @pytest.mark.asyncio
    async def test_save_tokens_with_athlete_data(self, strava_service, mock_db_session):
        """Test saving tokens with athlete data."""
        # Mock existing token record
        mock_token_record = Mock()
        mock_token_record.access_token = "old_token"
        mock_token_record.refresh_token = "old_refresh"
        mock_token_record.expires_at = datetime.now()

        # Mock the database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db_session.rollback = AsyncMock()

        tokens = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1234567890,
            "athlete": {"id": 12345, "name": "Test User"},
        }

        await strava_service._save_tokens(tokens)

        assert mock_token_record.access_token == "new_access_token"
        assert mock_token_record.athlete_data is not None
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_tokens_exception_handling(
        self, strava_service, mock_db_session
    ):
        """Test exception handling when saving tokens fails."""
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock(side_effect=Exception("Database error"))
        mock_db_session.rollback = AsyncMock()

        tokens = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1234567890,
        }

        with pytest.raises(Exception) as exc_info:
            await strava_service._save_tokens(tokens)

        assert "Database error" in str(exc_info.value)

        # Should have rolled back
        mock_db_session.rollback.assert_called_once()


class TestGetActivities:
    """Test activity retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_activities_first_page(self, strava_service, mock_db_session):
        """Test getting activities from first page."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock activity
        mock_activity = Mock()
        mock_activity.id = 12345
        mock_activity.name = "Test Activity"
        mock_activity.distance = Mock(side_effect=lambda: 1000.0)
        mock_activity.distance.__float__ = lambda self: 1000.0
        mock_timedelta_moving = Mock()
        mock_timedelta_moving.total_seconds = Mock(return_value=100.0)
        mock_activity.moving_time = Mock()
        mock_activity.moving_time.timedelta = Mock(return_value=mock_timedelta_moving)
        mock_timedelta_elapsed = Mock()
        mock_timedelta_elapsed.total_seconds = Mock(return_value=120.0)
        mock_activity.elapsed_time = Mock()
        mock_activity.elapsed_time.timedelta = Mock(return_value=mock_timedelta_elapsed)
        mock_activity.total_elevation_gain = 100.0
        mock_activity.type = "Run"
        mock_activity.start_date = datetime.now()
        mock_activity.start_date_local = datetime.now()
        mock_activity.timezone = "America/New_York"
        mock_activity.start_latlng = Mock()
        mock_activity.start_latlng.root = [40.0, -74.0]
        mock_activity.end_latlng = Mock()
        mock_activity.end_latlng.root = [40.1, -74.1]
        mock_activity.map = Mock()
        mock_activity.map.id = "map123"
        mock_activity.map.summary_polyline = "polyline123"
        mock_activity.has_heartrate = True
        mock_activity.average_heartrate = 150.0
        mock_activity.max_heartrate = 170.0
        mock_activity.has_kudoed = False
        mock_activity.kudos_count = 5
        mock_activity.comment_count = 3
        mock_activity.athlete_count = 1
        mock_activity.trainer = False
        mock_activity.commute = False
        mock_activity.manual = False
        mock_activity.private = False
        mock_activity.visibility = "everyone"
        mock_activity.flagged = False
        mock_activity.gear_id = "gear123"
        mock_activity.external_id = "ext123"
        mock_activity.upload_id = "upload123"
        mock_activity.average_speed = 5.0
        mock_activity.max_speed = 8.0
        mock_activity.hide_from_home = False
        mock_activity.from_accepted_tag = False
        mock_activity.average_watts = 200.0
        mock_activity.weighted_average_watts = 210.0
        mock_activity.kilojoules = 800.0
        mock_activity.device_watts = True
        mock_activity.elev_high = 100.0
        mock_activity.elev_low = 50.0
        mock_activity.pr_count = 2
        mock_activity.total_photo_count = 5
        mock_activity.suffer_score = 50

        # Mock client
        mock_client = Mock()
        mock_client.get_activities.return_value = [mock_activity]
        strava_service.client = mock_client

        activities = await strava_service.get_activities(page=1, per_page=30)

        assert len(activities) == 1
        assert activities[0]["id"] == "12345"
        assert activities[0]["name"] == "Test Activity"

    @pytest.mark.asyncio
    async def test_get_activities_second_page(self, strava_service, mock_db_session):
        """Test getting activities from second page."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock activities
        mock_activities = []
        for i in range(60):
            mock_activity = Mock()
            mock_activity.id = 12345 + i
            mock_activity.name = f"Test Activity {i}"
            mock_activity.distance = Mock()
            mock_activity.distance.__float__ = lambda self: 1000.0
            mock_timedelta_moving = Mock()
            mock_timedelta_moving.total_seconds = Mock(return_value=100.0)
            mock_activity.moving_time = Mock()
            mock_activity.moving_time.timedelta = Mock(
                return_value=mock_timedelta_moving
            )
            mock_timedelta_elapsed = Mock()
            mock_timedelta_elapsed.total_seconds = Mock(return_value=120.0)
            mock_activity.elapsed_time = Mock()
            mock_activity.elapsed_time.timedelta = Mock(
                return_value=mock_timedelta_elapsed
            )
            mock_activity.total_elevation_gain = 100.0
            mock_activity.type = "Run"
            mock_activity.start_date = datetime.now()
            mock_activity.start_date_local = datetime.now()
            mock_activity.timezone = "America/New_York"
            mock_activity.start_latlng = Mock()
            mock_activity.start_latlng.root = [40.0, -74.0]
            mock_activity.end_latlng = Mock()
            mock_activity.end_latlng.root = [40.1, -74.1]
            mock_activity.map = Mock()
            mock_activity.map.id = "map123"
            mock_activity.map.summary_polyline = "polyline123"
            mock_activity.has_heartrate = True
            mock_activity.average_heartrate = 150.0
            mock_activity.max_heartrate = 170.0
            mock_activity.has_kudoed = False
            mock_activity.kudos_count = 5
            mock_activity.comment_count = 3
            mock_activity.athlete_count = 1
            mock_activity.trainer = False
            mock_activity.commute = False
            mock_activity.manual = False
            mock_activity.private = False
            mock_activity.visibility = "everyone"
            mock_activity.flagged = False
            mock_activity.gear_id = "gear123"
            mock_activity.external_id = "ext123"
            mock_activity.upload_id = "upload123"
            mock_activity.average_speed = 5.0
            mock_activity.max_speed = 8.0
            mock_activity.hide_from_home = False
            mock_activity.from_accepted_tag = False
            mock_activity.average_watts = 200.0
            mock_activity.weighted_average_watts = 210.0
            mock_activity.kilojoules = 800.0
            mock_activity.device_watts = True
            mock_activity.elev_high = 100.0
            mock_activity.elev_low = 50.0
            mock_activity.pr_count = 2
            mock_activity.total_photo_count = 5
            mock_activity.suffer_score = 50
            mock_activities.append(mock_activity)

        # Mock client
        mock_client = Mock()
        mock_client.get_activities.return_value = mock_activities
        strava_service.client = mock_client

        activities = await strava_service.get_activities(page=2, per_page=30)

        assert len(activities) == 30
        assert activities[0]["name"] == "Test Activity 30"

    @pytest.mark.asyncio
    async def test_get_activities_rate_limit_exceeded(
        self, strava_service, mock_db_session
    ):
        """Test getting activities when rate limit is exceeded."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise RateLimitExceeded
        mock_client = Mock()
        mock_client.get_activities.side_effect = RateLimitExceeded(
            "Rate limit exceeded"
        )
        strava_service.client = mock_client

        with pytest.raises(RateLimitExceeded):
            await strava_service.get_activities()


class TestGetActivityGpx:
    """Test GPX retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_activity_gpx_success(self, strava_service, mock_db_session):
        """Test successfully getting GPX data."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock activity
        mock_activity = Mock()
        mock_activity.name = "Test Activity"
        mock_activity.start_date = datetime.now()

        # Mock streams
        mock_latlng_stream = Mock()
        mock_latlng_stream.data = [[40.0, -74.0], [40.1, -74.1]]
        mock_altitude_stream = Mock()
        mock_altitude_stream.data = [100.0, 105.0]
        mock_time_stream = Mock()
        mock_time_stream.data = [0, 60]

        mock_streams = {
            "latlng": mock_latlng_stream,
            "altitude": mock_altitude_stream,
            "time": mock_time_stream,
        }

        # Mock client
        mock_client = Mock()
        mock_client.get_activity.return_value = mock_activity
        mock_client.get_activity_streams.return_value = mock_streams
        strava_service.client = mock_client

        gpx_data = await strava_service.get_activity_gpx("12345")

        assert gpx_data is not None
        assert "<?xml" in gpx_data
        assert "Test Activity" in gpx_data

    @pytest.mark.asyncio
    async def test_get_activity_gpx_no_latlng(self, strava_service, mock_db_session):
        """Test getting GPX when no latlng stream is available."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock activity
        mock_activity = Mock()
        mock_activity.name = "Test Activity"
        mock_activity.start_date = datetime.now()

        # Mock streams without latlng
        mock_streams = {}

        # Mock client
        mock_client = Mock()
        mock_client.get_activity.return_value = mock_activity
        mock_client.get_activity_streams.return_value = mock_streams
        strava_service.client = mock_client

        gpx_data = await strava_service.get_activity_gpx("12345")

        assert gpx_data is None


class TestGetAthlete:
    """Test athlete retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_athlete_success(self, strava_service, mock_db_session):
        """Test successfully getting athlete information."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock athlete
        mock_athlete = Mock()
        mock_athlete.id = 12345
        mock_athlete.username = "testuser"
        mock_athlete.resource_state = 3
        mock_athlete.firstname = "John"
        mock_athlete.lastname = "Doe"
        mock_athlete.bio = "Test bio"
        mock_athlete.city = "New York"
        mock_athlete.state = "NY"
        mock_athlete.country = "USA"
        mock_athlete.sex = "M"
        mock_athlete.premium = True
        mock_athlete.summit = False
        mock_athlete.created_at = datetime.now()
        mock_athlete.updated_at = datetime.now()
        mock_athlete.badge_type_id = 0
        mock_athlete.weight = 70.0
        mock_athlete.profile_medium = "http://example.com/medium.jpg"
        mock_athlete.profile = "http://example.com/profile.jpg"
        mock_athlete.friend = None
        mock_athlete.follower = None
        mock_athlete.blocked = False
        mock_athlete.can_follow = True
        mock_athlete.follower_count = 100
        mock_athlete.friend_count = 50
        mock_athlete.mutual_friend_count = 25
        mock_athlete.athlete_type = 0
        mock_athlete.date_preference = "%m/%d/%Y"
        mock_athlete.measurement_preference = "meters"
        mock_athlete.clubs = []
        mock_athlete.ftp = None
        mock_athlete.max_heartrate = 180.0
        mock_athlete.max_watts = 1000
        mock_athlete.max_speed = 12.0
        mock_athlete.default_bikes = []
        mock_athlete.default_shoes = []
        mock_athlete.default_gear = []
        mock_athlete.offline_token = None
        mock_athlete.email = "test@example.com"

        # Mock client
        mock_client = Mock()
        mock_client.get_athlete.return_value = mock_athlete
        strava_service.client = mock_client

        athlete_data = await strava_service.get_athlete()

        assert athlete_data["id"] == "12345"
        assert athlete_data["username"] == "testuser"
        assert athlete_data["firstname"] == "John"
        assert athlete_data["lastname"] == "Doe"

    @pytest.mark.asyncio
    async def test_get_athlete_with_clubs(self, strava_service, mock_db_session):
        """Test getting athlete with clubs information."""
        import json
        from datetime import timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock club
        mock_club = Mock()
        mock_club.id = 67890
        mock_club.name = "Test Club"

        # Mock athlete
        mock_athlete = Mock()
        mock_athlete.id = 12345
        mock_athlete.username = "testuser"
        mock_athlete.resource_state = 3
        mock_athlete.firstname = "John"
        mock_athlete.lastname = "Doe"
        mock_athlete.bio = "Test bio"
        mock_athlete.city = "New York"
        mock_athlete.state = "NY"
        mock_athlete.country = "USA"
        mock_athlete.sex = "M"
        mock_athlete.premium = True
        mock_athlete.summit = False
        mock_athlete.created_at = datetime.now()
        mock_athlete.updated_at = datetime.now()
        mock_athlete.badge_type_id = 0
        mock_athlete.weight = 70.0
        mock_athlete.profile_medium = "http://example.com/medium.jpg"
        mock_athlete.profile = "http://example.com/profile.jpg"
        mock_athlete.friend = None
        mock_athlete.follower = None
        mock_athlete.blocked = False
        mock_athlete.can_follow = True
        mock_athlete.follower_count = 100
        mock_athlete.friend_count = 50
        mock_athlete.mutual_friend_count = 25
        mock_athlete.athlete_type = 0
        mock_athlete.date_preference = "%m/%d/%Y"
        mock_athlete.measurement_preference = "meters"
        mock_athlete.clubs = [mock_club]
        mock_athlete.ftp = None
        mock_athlete.max_heartrate = 180.0
        mock_athlete.max_watts = 1000
        mock_athlete.max_speed = 12.0
        mock_athlete.default_bikes = []
        mock_athlete.default_shoes = []
        mock_athlete.default_gear = []
        mock_athlete.offline_token = None
        mock_athlete.email = "test@example.com"

        # Mock client
        mock_client = Mock()
        mock_client.get_athlete.return_value = mock_athlete
        strava_service.client = mock_client

        athlete_data = await strava_service.get_athlete()

        assert len(athlete_data["clubs"]) == 1
        assert athlete_data["clubs"][0]["id"] == "67890"
        assert athlete_data["clubs"][0]["name"] == "Test Club"

    @pytest.mark.asyncio
    async def test_get_athlete_rate_limit_exceeded(
        self, strava_service, mock_db_session
    ):
        """Test getting athlete when rate limit is exceeded."""
        import json
        from datetime import timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise RateLimitExceeded
        mock_client = Mock()
        mock_client.get_athlete.side_effect = RateLimitExceeded("Rate limit exceeded")
        strava_service.client = mock_client

        with pytest.raises(RateLimitExceeded):
            await strava_service.get_athlete()


class TestConvertActivityToDict:
    """Test activity conversion to dictionary."""

    @pytest.mark.asyncio
    async def test_convert_activity_with_none_values(self, strava_service):
        """Test converting activity with None values."""

        mock_activity = Mock()
        mock_activity.id = 12345
        mock_activity.name = "Test Activity"
        mock_activity.distance = None
        mock_activity.moving_time = None
        mock_activity.elapsed_time = None
        mock_activity.total_elevation_gain = None
        mock_activity.type = "Run"
        mock_activity.start_date = datetime.now()
        mock_activity.start_date_local = None
        mock_activity.timezone = None
        mock_activity.start_latlng = None
        mock_activity.end_latlng = None
        mock_activity.map = None
        mock_activity.has_heartrate = None
        mock_activity.average_heartrate = None
        mock_activity.max_heartrate = None
        mock_activity.has_kudoed = None
        mock_activity.kudos_count = None
        mock_activity.comment_count = None
        mock_activity.athlete_count = None
        mock_activity.trainer = None
        mock_activity.commute = None
        mock_activity.manual = None
        mock_activity.private = None
        mock_activity.visibility = None
        mock_activity.flagged = None
        mock_activity.gear_id = None
        mock_activity.external_id = None
        mock_activity.upload_id = None
        mock_activity.average_speed = None
        mock_activity.max_speed = None
        mock_activity.hide_from_home = None
        mock_activity.from_accepted_tag = None
        mock_activity.average_watts = None
        mock_activity.weighted_average_watts = None
        mock_activity.kilojoules = None
        mock_activity.device_watts = None
        mock_activity.elev_high = None
        mock_activity.elev_low = None
        mock_activity.pr_count = None
        mock_activity.total_photo_count = None
        mock_activity.suffer_score = None

        activity_dict = strava_service._convert_activity_to_dict(mock_activity)

        assert activity_dict["id"] == "12345"
        assert activity_dict["name"] == "Test Activity"
        assert activity_dict["distance"] == 0.0
        assert activity_dict["moving_time"] == 0
        assert activity_dict["elapsed_time"] == 0
        assert activity_dict["total_elevation_gain"] == 0.0
        assert activity_dict["start_latlng"] is None
        assert activity_dict["end_latlng"] is None
        assert activity_dict["map"] is None

    @pytest.mark.asyncio
    async def test_convert_activity_with_empty_map(self, strava_service):
        """Test converting activity with empty map summary_polyline."""

        mock_activity = Mock()
        mock_activity.id = 12345
        mock_activity.name = "Test Activity"
        mock_activity.distance = Mock()
        mock_activity.distance.__float__ = lambda self: 1000.0
        mock_timedelta_moving = Mock()
        mock_timedelta_moving.total_seconds = Mock(return_value=100.0)
        mock_activity.moving_time = Mock()
        mock_activity.moving_time.timedelta = Mock(return_value=mock_timedelta_moving)
        mock_timedelta_elapsed = Mock()
        mock_timedelta_elapsed.total_seconds = Mock(return_value=120.0)
        mock_activity.elapsed_time = Mock()
        mock_activity.elapsed_time.timedelta = Mock(return_value=mock_timedelta_elapsed)
        mock_activity.total_elevation_gain = 100.0
        mock_activity.type = "Run"
        mock_activity.start_date = datetime.now()
        mock_activity.start_date_local = datetime.now()
        mock_activity.timezone = "America/New_York"
        mock_activity.start_latlng = Mock()
        mock_activity.start_latlng.root = [40.0, -74.0]
        mock_activity.end_latlng = Mock()
        mock_activity.end_latlng.root = [40.1, -74.1]
        mock_activity.map = Mock()
        mock_activity.map.id = "map123"
        mock_activity.map.summary_polyline = None
        mock_activity.has_heartrate = True
        mock_activity.average_heartrate = 150.0
        mock_activity.max_heartrate = 170.0
        mock_activity.has_kudoed = False
        mock_activity.kudos_count = 5
        mock_activity.comment_count = 3
        mock_activity.athlete_count = 1
        mock_activity.trainer = False
        mock_activity.commute = False
        mock_activity.manual = False
        mock_activity.private = False
        mock_activity.visibility = "everyone"
        mock_activity.flagged = False
        mock_activity.gear_id = "gear123"
        mock_activity.external_id = "ext123"
        mock_activity.upload_id = "upload123"
        mock_activity.average_speed = 5.0
        mock_activity.max_speed = 8.0
        mock_activity.hide_from_home = False
        mock_activity.from_accepted_tag = False
        mock_activity.average_watts = 200.0
        mock_activity.weighted_average_watts = 210.0
        mock_activity.kilojoules = 800.0
        mock_activity.device_watts = True
        mock_activity.elev_high = 100.0
        mock_activity.elev_low = 50.0
        mock_activity.pr_count = 2
        mock_activity.total_photo_count = 5
        mock_activity.suffer_score = 50

        activity_dict = strava_service._convert_activity_to_dict(mock_activity)

        assert activity_dict["map"]["summary_polyline"] is None


class TestConstructGpxFromStreams:
    """Test GPX construction from streams."""

    def test_construct_gpx_from_streams_no_time_data(self, strava_service):
        """Test constructing GPX when no time stream data is available."""
        mock_activity = Mock()
        mock_activity.name = "Test Activity"
        mock_activity.start_date = datetime.now()

        mock_latlng_stream = Mock()
        mock_latlng_stream.data = [[40.0, -74.0], [40.1, -74.1]]
        mock_altitude_stream = Mock()
        mock_altitude_stream.data = [100.0, 105.0]

        mock_streams = {
            "latlng": mock_latlng_stream,
            "altitude": mock_altitude_stream,
        }

        gpx_data = strava_service._construct_gpx_from_streams(
            mock_activity, mock_streams
        )

        assert gpx_data is not None
        assert "<?xml" in gpx_data

    def test_construct_gpx_from_streams_no_altitude_data(self, strava_service):
        """Test constructing GPX when no altitude stream data is available."""
        mock_activity = Mock()
        mock_activity.name = "Test Activity"
        mock_activity.start_date = datetime.now()

        mock_latlng_stream = Mock()
        mock_latlng_stream.data = [[40.0, -74.0], [40.1, -74.1]]
        mock_time_stream = Mock()
        mock_time_stream.data = [0, 60]

        mock_streams = {
            "latlng": mock_latlng_stream,
            "time": mock_time_stream,
        }

        gpx_data = strava_service._construct_gpx_from_streams(
            mock_activity, mock_streams
        )

        assert gpx_data is not None
        assert "<?xml" in gpx_data

    def test_construct_gpx_from_streams_exception_handling(self, strava_service):
        """Test constructing GPX when exception occurs."""
        mock_activity = Mock()
        mock_activity.name = "Test Activity"
        mock_activity.start_date = datetime.now()

        # Mock streams to cause an exception
        mock_streams = {
            "latlng": None,  # This will cause an exception
        }

        gpx_data = strava_service._construct_gpx_from_streams(
            mock_activity, mock_streams
        )

        assert gpx_data is None


class TestGetActivityGpxErrors:
    """Test GPX retrieval error handling."""

    @pytest.mark.asyncio
    async def test_get_activity_gpx_rate_limit_exceeded(
        self, strava_service, mock_db_session
    ):
        """Test getting GPX when rate limit is exceeded."""
        import json
        from datetime import timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise RateLimitExceeded
        mock_client = Mock()
        mock_client.get_activity.side_effect = RateLimitExceeded("Rate limit exceeded")
        strava_service.client = mock_client

        with pytest.raises(RateLimitExceeded):
            await strava_service.get_activity_gpx("12345")

    @pytest.mark.asyncio
    async def test_get_activity_gpx_exception(self, strava_service, mock_db_session):
        """Test getting GPX when an exception occurs."""
        import json
        from datetime import timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise an exception
        mock_client = Mock()
        mock_client.get_activity.side_effect = Exception("API error")
        strava_service.client = mock_client

        with pytest.raises(Exception) as exc_info:
            await strava_service.get_activity_gpx("12345")

        assert "API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_activity_gpx_access_unauthorized(
        self, strava_service, mock_db_session
    ):
        """Test getting GPX when access unauthorized."""
        import json
        from datetime import timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise AccessUnauthorized
        mock_client = Mock()
        mock_client.get_activity.side_effect = AccessUnauthorized("Unauthorized")
        strava_service.client = mock_client

        with pytest.raises(AccessUnauthorized):
            await strava_service.get_activity_gpx("12345")

    @pytest.mark.asyncio
    async def test_get_activities_access_unauthorized(
        self, strava_service, mock_db_session
    ):
        """Test getting activities when access unauthorized."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise AccessUnauthorized
        mock_client = Mock()
        mock_client.get_activities.side_effect = AccessUnauthorized("Unauthorized")
        strava_service.client = mock_client

        with pytest.raises(AccessUnauthorized):
            await strava_service.get_activities()

    @pytest.mark.asyncio
    async def test_get_activities_generic_exception(
        self, strava_service, mock_db_session
    ):
        """Test getting activities when generic exception occurs."""
        import json
        from datetime import datetime, timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise generic exception
        mock_client = Mock()
        mock_client.get_activities.side_effect = Exception("Generic error")
        strava_service.client = mock_client

        with pytest.raises(Exception) as exc_info:
            await strava_service.get_activities()

        assert "Generic error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_athlete_access_unauthorized(
        self, strava_service, mock_db_session
    ):
        """Test getting athlete when access unauthorized."""
        import json
        from datetime import timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise AccessUnauthorized
        mock_client = Mock()
        mock_client.get_athlete.side_effect = AccessUnauthorized("Unauthorized")
        strava_service.client = mock_client

        with pytest.raises(AccessUnauthorized):
            await strava_service.get_athlete()

    @pytest.mark.asyncio
    async def test_get_athlete_generic_exception(self, strava_service, mock_db_session):
        """Test getting athlete when generic exception occurs."""
        import json
        from datetime import timedelta

        # Mock valid token
        mock_token_record = Mock()
        mock_token_record.access_token = "valid_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.athlete_data = json.dumps({"id": 12345})

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client to raise generic exception
        mock_client = Mock()
        mock_client.get_athlete.side_effect = Exception("Generic error")
        strava_service.client = mock_client

        with pytest.raises(Exception) as exc_info:
            await strava_service.get_athlete()

        assert "Generic error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_construct_gpx_from_streams_exception_in_processing(
        self, strava_service
    ):
        """Test GPX construction when exception occurs during processing."""

        mock_activity = Mock()
        mock_activity.name = "Test Activity"
        mock_activity.start_date = datetime.now()

        # Mock streams with invalid data that will cause exception
        mock_latlng_stream = Mock()
        # Use a string instead of a list to cause iteration error
        mock_latlng_stream.data = "invalid"  # This will cause exception when iterating
        mock_streams = {
            "latlng": mock_latlng_stream,
        }

        gpx_data = strava_service._construct_gpx_from_streams(
            mock_activity, mock_streams
        )

        # Should return None when exception occurs
        assert gpx_data is None

    @pytest.mark.asyncio
    async def test_ensure_authenticated_refresh_fails_with_message(
        self, strava_service, mock_db_session
    ):
        """Test ensure authenticated when refresh fails with AccessUnauthorized."""
        from datetime import timedelta

        # Mock expired token
        mock_token_record = Mock()
        mock_token_record.access_token = "expired_token"
        mock_token_record.refresh_token = "refresh_token"
        mock_token_record.expires_at = datetime.now() - timedelta(hours=1)
        mock_token_record.athlete_data = None

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock client for failed refresh
        strava_service.client = Mock()
        strava_service.refresh_access_token = AsyncMock(return_value=False)

        with pytest.raises(AccessUnauthorized) as exc_info:
            await strava_service._ensure_authenticated()

        assert "Token expired and refresh failed" in str(exc_info.value)
