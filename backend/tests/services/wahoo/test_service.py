"""Unit tests for the Wahoo service."""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.wahoo.client import Client
from src.services.wahoo.exceptions import WahooAccessUnauthorized
from src.services.wahoo.service import WahooService
from src.utils.config import WahooConfig


@pytest.fixture
def mock_wahoo_config():
    """Create a mock Wahoo configuration for testing."""
    return WahooConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        callback_url="https://example.com/callback",
        scopes=["routes_write", "user_read"],
    )


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def wahoo_service(mock_wahoo_config, mock_db_session):
    """Create a WahooService instance for testing."""
    return WahooService(
        wahoo_config=mock_wahoo_config,
        db_session=mock_db_session,
        wahoo_id=12345,
    )


class TestWahooServiceInitialization:
    """Test WahooService initialization and basic setup."""

    def test_wahoo_service_initialization(self, mock_wahoo_config, mock_db_session):
        """Test WahooService initialization."""
        service = WahooService(
            wahoo_config=mock_wahoo_config,
            db_session=mock_db_session,
            wahoo_id=12345,
        )

        assert service.client_id == "test_client_id"
        assert service.client_secret == "test_client_secret"
        assert service.callback_url == "https://example.com/callback"
        assert service.scopes == ["routes_write", "user_read"]
        assert service.wahoo_id == 12345
        assert service.db_session == mock_db_session
        assert isinstance(service.client, Client)


class TestLoadTokens:
    """Test token loading from database."""

    @pytest.mark.asyncio
    async def test_load_tokens_not_exists(self, wahoo_service, mock_db_session):
        """Test loading tokens when they don't exist."""
        # Mock the database query to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        tokens = await wahoo_service._load_tokens()

        assert tokens is None

    @pytest.mark.asyncio
    async def test_load_tokens_exists_without_user_data(
        self, wahoo_service, mock_db_session
    ):
        """Test loading tokens when they exist without user data."""
        # Mock token record
        mock_token_record = Mock()
        mock_token_record.access_token = "test_access_token"
        mock_token_record.refresh_token = "test_refresh_token"
        expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.expires_at = expires_at
        mock_token_record.user_data = None

        # Mock the database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        tokens = await wahoo_service._load_tokens()

        assert tokens is not None
        assert tokens["access_token"] == "test_access_token"
        assert tokens["refresh_token"] == "test_refresh_token"
        assert "expires_at" in tokens
        assert "user" not in tokens

    @pytest.mark.asyncio
    async def test_load_tokens_exists_with_user_data(
        self, wahoo_service, mock_db_session
    ):
        """Test loading tokens when they exist with user data."""
        user_data = {"id": 12345, "name": "Test User"}
        # Mock token record with user_data as JSON string
        mock_token_record = Mock()
        mock_token_record.access_token = "test_access_token"
        mock_token_record.refresh_token = "test_refresh_token"
        expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.expires_at = expires_at
        mock_token_record.user_data = json.dumps(user_data)

        # Mock the database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        tokens = await wahoo_service._load_tokens()

        assert tokens is not None
        assert tokens["access_token"] == "test_access_token"
        assert tokens["refresh_token"] == "test_refresh_token"
        assert tokens["user"] == user_data

    @pytest.mark.asyncio
    async def test_load_tokens_exception(self, wahoo_service, mock_db_session):
        """Test loading tokens when an exception occurs."""
        # Mock the database query to raise an exception
        mock_db_session.execute = AsyncMock(side_effect=Exception("Database error"))

        tokens = await wahoo_service._load_tokens()

        assert tokens is None


class TestSaveTokens:
    """Test token saving to database."""

    @pytest.mark.asyncio
    async def test_save_tokens_new(self, wahoo_service, mock_db_session):
        """Test saving new tokens."""
        from datetime import datetime

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
            "expires_at": int(datetime.now().timestamp()),
        }

        await wahoo_service._save_tokens(tokens)

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_tokens_update(self, wahoo_service, mock_db_session):
        """Test updating existing tokens."""
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
            "expires_at": int(datetime.now().timestamp()),
        }

        await wahoo_service._save_tokens(tokens)

        assert mock_token_record.access_token == "new_access_token"
        assert mock_token_record.refresh_token == "new_refresh_token"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_tokens_with_user_data(self, wahoo_service, mock_db_session):
        """Test saving tokens with user data."""
        # Mock the database query to return None (new record)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.rollback = AsyncMock()

        user_data = {"id": 12345, "name": "Test User"}
        tokens = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": int(datetime.now().timestamp()),
            "user": user_data,
        }

        await wahoo_service._save_tokens(tokens)

        # Verify user_data was JSON serialized
        call_args = mock_db_session.add.call_args
        token_record = call_args[0][0]
        assert token_record.user_data == json.dumps(user_data)

    @pytest.mark.asyncio
    async def test_save_tokens_exception(self, wahoo_service, mock_db_session):
        """Test saving tokens when an exception occurs."""
        # Mock the database query to raise an exception
        mock_db_session.execute = AsyncMock(side_effect=RuntimeError("Database error"))
        mock_db_session.rollback = AsyncMock()

        tokens = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": int(datetime.now().timestamp()),
        }

        with pytest.raises(RuntimeError):
            await wahoo_service._save_tokens(tokens)

        mock_db_session.rollback.assert_called_once()


class TestGetAuthorizationUrl:
    """Test authorization URL generation."""

    def test_get_authorization_url_default_state(self, wahoo_service):
        """Test generating authorization URL with default state."""
        with patch.object(wahoo_service.client, "authorization_url") as mock_auth_url:
            mock_auth_url.return_value = "https://api.wahooligan.com/oauth/authorize"
            result = wahoo_service.get_authorization_url()

            assert result == "https://api.wahooligan.com/oauth/authorize"
            mock_auth_url.assert_called_once()

    def test_get_authorization_url_custom_state(self, wahoo_service):
        """Test generating authorization URL with custom state."""
        with patch.object(wahoo_service.client, "authorization_url") as mock_auth_url:
            mock_auth_url.return_value = "https://api.wahooligan.com/oauth/authorize"
            result = wahoo_service.get_authorization_url(state="custom_state")

            assert result == "https://api.wahooligan.com/oauth/authorize"
            mock_auth_url.assert_called_once()


class TestExchangeCodeForToken:
    """Test code exchange for token."""

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(
        self, wahoo_service, mock_db_session
    ):
        """Test successful code exchange."""
        # Mock client response
        access_info = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": int(datetime.now().timestamp()),
        }
        wahoo_service.client.exchange_code_for_token = Mock(return_value=access_info)

        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.rollback = AsyncMock()

        # Mock _save_tokens
        with patch.object(wahoo_service, "_save_tokens") as mock_save_tokens:
            mock_save_tokens.return_value = AsyncMock()
            result = await wahoo_service.exchange_code_for_token("test_code")

            assert result["access_token"] == "new_access_token"
            assert result["refresh_token"] == "new_refresh_token"
            mock_save_tokens.assert_called_once()

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self, wahoo_service):
        """Test code exchange when it fails."""
        # Mock client to raise an exception
        wahoo_service.client.exchange_code_for_token = Mock(
            side_effect=Exception("Invalid code")
        )

        with pytest.raises(Exception) as exc_info:
            await wahoo_service.exchange_code_for_token("invalid_code")

        assert "Invalid code" in str(exc_info.value)


class TestRefreshAccessToken:
    """Test token refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, wahoo_service, mock_db_session):
        """Test successful token refresh."""
        # Mock existing tokens
        mock_token_record = Mock()
        mock_token_record.access_token = "old_token"
        mock_token_record.refresh_token = "refresh_token"
        expires_at = datetime.now() + timedelta(hours=1)
        mock_token_record.expires_at = expires_at
        mock_token_record.user_data = None

        # Mock database queries (one for load, one for save)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token_record
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db_session.rollback = AsyncMock()

        # Mock the client's refresh method
        refresh_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": int(datetime.now().timestamp()),
        }
        wahoo_service.client.refresh_access_token = Mock(return_value=refresh_response)

        # Mock _save_tokens
        with patch.object(wahoo_service, "_save_tokens") as mock_save_tokens:
            mock_save_tokens.return_value = AsyncMock()
            result = await wahoo_service.refresh_access_token()

            assert result is True
            mock_save_tokens.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_access_token_no_refresh_token(
        self, wahoo_service, mock_db_session
    ):
        """Test refresh fails when no refresh token exists."""
        # Mock no tokens
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await wahoo_service.refresh_access_token()

        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_access_token_client_exception(self, wahoo_service):
        """Test refresh fails when client raises an exception."""
        # Mock load to return tokens
        with patch.object(wahoo_service, "_load_tokens") as mock_load:
            mock_load.return_value = {
                "access_token": "old_token",
                "refresh_token": "refresh_token",
                "expires_at": int(datetime.now().timestamp()),
            }

            # Mock client to raise an exception
            wahoo_service.client.refresh_access_token = Mock(
                side_effect=Exception("Refresh failed")
            )

            result = await wahoo_service.refresh_access_token()

            assert result is False


class TestEnsureAuthenticated:
    """Test authentication check."""

    @pytest.mark.asyncio
    async def test_ensure_authenticated_with_valid_token(self, wahoo_service):
        """Test authentication with valid token."""
        with patch.object(wahoo_service, "_load_tokens") as mock_load:
            mock_load.return_value = {
                "access_token": "valid_token",
                "expires_at": int((datetime.now() + timedelta(hours=1)).timestamp()),
            }

            await wahoo_service._ensure_authenticated()

            assert wahoo_service.client.access_token == "valid_token"

    @pytest.mark.asyncio
    async def test_ensure_authenticated_no_tokens(self, wahoo_service):
        """Test authentication fails when no tokens exist."""
        with patch.object(wahoo_service, "_load_tokens") as mock_load:
            mock_load.return_value = None

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service._ensure_authenticated()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_no_access_token(self, wahoo_service):
        """Test authentication fails when no access token exists."""
        with patch.object(wahoo_service, "_load_tokens") as mock_load:
            mock_load.return_value = {
                "refresh_token": "refresh_token",
                "expires_at": int(datetime.now().timestamp()),
            }

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service._ensure_authenticated()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_expired_token_success(
        self, wahoo_service, mock_db_session
    ):
        """Test authentication with expired token that successfully refreshes."""
        with (
            patch.object(wahoo_service, "_load_tokens") as mock_load,
            patch.object(wahoo_service, "refresh_access_token") as mock_refresh,
        ):
            # First call returns expired token
            # Second call returns fresh token after refresh
            expired_time = int((datetime.now() - timedelta(hours=1)).timestamp())
            fresh_time = int((datetime.now() + timedelta(hours=1)).timestamp())
            mock_load.side_effect = [
                {
                    "access_token": "expired_token",
                    "refresh_token": "refresh_token",
                    "expires_at": expired_time,
                },
                {
                    "access_token": "new_token",
                    "refresh_token": "refresh_token",
                    "expires_at": fresh_time,
                },
            ]
            mock_refresh.return_value = True

            await wahoo_service._ensure_authenticated()

            assert wahoo_service.client.access_token == "new_token"
            mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_expired_token_refresh_fails(
        self, wahoo_service
    ):
        """Test authentication when token refresh fails."""
        with (
            patch.object(wahoo_service, "_load_tokens") as mock_load,
            patch.object(wahoo_service, "refresh_access_token") as mock_refresh,
        ):
            mock_load.return_value = {
                "access_token": "expired_token",
                "refresh_token": "refresh_token",
                "expires_at": int((datetime.now() - timedelta(hours=1)).timestamp()),
            }
            mock_refresh.return_value = False

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service._ensure_authenticated()


class TestDeauthorize:
    """Test deauthorization."""

    @pytest.mark.asyncio
    async def test_deauthorize_success(self, wahoo_service):
        """Test successful deauthorization."""
        # Mock authentication
        with patch.object(wahoo_service, "_ensure_authenticated") as mock_ensure:
            wahoo_service.client.deauthorize = Mock()

            await wahoo_service.deauthorize()

            mock_ensure.assert_called_once()
            wahoo_service.client.deauthorize.assert_called_once()

    @pytest.mark.asyncio
    async def test_deauthorize_value_error_401(self, wahoo_service):
        """Test deauthorization with 401 error."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.deauthorize = Mock(side_effect=ValueError("401"))

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service.deauthorize()

    @pytest.mark.asyncio
    async def test_deauthorize_value_error_other(self, wahoo_service):
        """Test deauthorization with other ValueError."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.deauthorize = Mock(
                side_effect=ValueError("Connection error")
            )

            with pytest.raises(ValueError):
                await wahoo_service.deauthorize()

    @pytest.mark.asyncio
    async def test_deauthorize_exception(self, wahoo_service):
        """Test deauthorization with generic exception."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.deauthorize = Mock(
                side_effect=RuntimeError("Unknown error")
            )

            with pytest.raises(RuntimeError):
                await wahoo_service.deauthorize()


class TestGetUser:
    """Test get user method."""

    @pytest.mark.asyncio
    async def test_get_user_success(self, wahoo_service):
        """Test successful user retrieval."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            user_data = {"id": 12345, "name": "Test"}
            wahoo_service.client.get_user = Mock(return_value=user_data)

            result = await wahoo_service.get_user()

            assert result == user_data

    @pytest.mark.asyncio
    async def test_get_user_value_error_401(self, wahoo_service):
        """Test get user with 401 error."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_user = Mock(
                side_effect=ValueError("401 unauthorized")
            )

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service.get_user()

    @pytest.mark.asyncio
    async def test_get_user_value_error_other(self, wahoo_service):
        """Test get user with other ValueError."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_user = Mock(
                side_effect=ValueError("Parsing error")
            )

            with pytest.raises(ValueError):
                await wahoo_service.get_user()

    @pytest.mark.asyncio
    async def test_get_user_exception(self, wahoo_service):
        """Test get user with generic exception."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_user = Mock(
                side_effect=RuntimeError("Network error")
            )

            with pytest.raises(RuntimeError):
                await wahoo_service.get_user()


class TestGetRoute:
    """Test get route method."""

    @pytest.mark.asyncio
    async def test_get_route_success(self, wahoo_service):
        """Test successful route retrieval."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            route_data = {"id": 123, "name": "Route"}
            wahoo_service.client.get_route = Mock(return_value=route_data)

            result = await wahoo_service.get_route(123)

            assert result == route_data

    @pytest.mark.asyncio
    async def test_get_route_value_error_401(self, wahoo_service):
        """Test get route with 401 error."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_route = Mock(side_effect=ValueError("401"))

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service.get_route(123)

    @pytest.mark.asyncio
    async def test_get_route_value_error_other(self, wahoo_service):
        """Test get route with other ValueError."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_route = Mock(side_effect=ValueError("Invalid ID"))

            with pytest.raises(ValueError):
                await wahoo_service.get_route(123)

    @pytest.mark.asyncio
    async def test_get_route_exception(self, wahoo_service):
        """Test get route with generic exception."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_route = Mock(
                side_effect=RuntimeError("Network error")
            )

            with pytest.raises(RuntimeError):
                await wahoo_service.get_route(123)


class TestGetRoutes:
    """Test get routes method."""

    @pytest.mark.asyncio
    async def test_get_routes_success(self, wahoo_service):
        """Test successful routes retrieval."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_routes = Mock(return_value=[{"id": 1}, {"id": 2}])

            result = await wahoo_service.get_routes()

            assert result == [{"id": 1}, {"id": 2}]

    @pytest.mark.asyncio
    async def test_get_routes_value_error_401(self, wahoo_service):
        """Test get routes with 401 error."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_routes = Mock(side_effect=ValueError("401"))

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service.get_routes()

    @pytest.mark.asyncio
    async def test_get_routes_value_error_other(self, wahoo_service):
        """Test get routes with other ValueError."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_routes = Mock(
                side_effect=ValueError("Parse error")
            )

            with pytest.raises(ValueError):
                await wahoo_service.get_routes()

    @pytest.mark.asyncio
    async def test_get_routes_exception(self, wahoo_service):
        """Test get routes with generic exception."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.get_routes = Mock(
                side_effect=RuntimeError("Network error")
            )

            with pytest.raises(RuntimeError):
                await wahoo_service.get_routes()


class TestCreateRoute:
    """Test create route method."""

    @pytest.mark.asyncio
    async def test_create_route_success(self, wahoo_service):
        """Test successful route creation."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.create_route = Mock(
                return_value={"id": 123, "name": "New Route"}
            )

            result = await wahoo_service.create_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="New Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 123, "name": "New Route"}

    @pytest.mark.asyncio
    async def test_create_route_value_error_401(self, wahoo_service):
        """Test create route with 401 error."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.create_route = Mock(side_effect=ValueError("401"))

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service.create_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="New Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    @pytest.mark.asyncio
    async def test_create_route_value_error_other(self, wahoo_service):
        """Test create route with other ValueError."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.create_route = Mock(
                side_effect=ValueError("Invalid data")
            )

            with pytest.raises(ValueError):
                await wahoo_service.create_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="New Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    @pytest.mark.asyncio
    async def test_create_route_exception(self, wahoo_service):
        """Test create route with generic exception."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.create_route = Mock(
                side_effect=RuntimeError("Network error")
            )

            with pytest.raises(RuntimeError):
                await wahoo_service.create_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="New Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )


class TestUpdateRoute:
    """Test update route method."""

    @pytest.mark.asyncio
    async def test_update_route_success(self, wahoo_service):
        """Test successful route update."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.update_route = Mock(
                return_value={"id": 123, "name": "Updated Route"}
            )

            result = await wahoo_service.update_route(
                route_id=123,
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Updated Route",
                start_lat=45.123,
                start_lng=5.987,
                distance=10000.0,
                ascent=500.0,
                descent=100.0,
            )

            assert result == {"id": 123, "name": "Updated Route"}

    @pytest.mark.asyncio
    async def test_update_route_value_error_401(self, wahoo_service):
        """Test update route with 401 error."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.update_route = Mock(side_effect=ValueError("401"))

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service.update_route(
                    route_id=123,
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Updated Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    @pytest.mark.asyncio
    async def test_update_route_value_error_other(self, wahoo_service):
        """Test update route with other ValueError."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.update_route = Mock(
                side_effect=ValueError("Invalid ID")
            )

            with pytest.raises(ValueError):
                await wahoo_service.update_route(
                    route_id=123,
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Updated Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )

    @pytest.mark.asyncio
    async def test_update_route_exception(self, wahoo_service):
        """Test update route with generic exception."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.update_route = Mock(
                side_effect=RuntimeError("Network error")
            )

            with pytest.raises(RuntimeError):
                await wahoo_service.update_route(
                    route_id=123,
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Updated Route",
                    start_lat=45.123,
                    start_lng=5.987,
                    distance=10000.0,
                    ascent=500.0,
                    descent=100.0,
                )


class TestDeleteRoute:
    """Test delete route method."""

    @pytest.mark.asyncio
    async def test_delete_route_success(self, wahoo_service):
        """Test successful route deletion."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.delete_route = Mock()

            await wahoo_service.delete_route(123)

            wahoo_service.client.delete_route.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_delete_route_value_error_401(self, wahoo_service):
        """Test delete route with 401 error."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.delete_route = Mock(side_effect=ValueError("401"))

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service.delete_route(123)

    @pytest.mark.asyncio
    async def test_delete_route_value_error_other(self, wahoo_service):
        """Test delete route with other ValueError."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.delete_route = Mock(
                side_effect=ValueError("Not found")
            )

            with pytest.raises(ValueError):
                await wahoo_service.delete_route(123)

    @pytest.mark.asyncio
    async def test_delete_route_exception(self, wahoo_service):
        """Test delete route with generic exception."""
        with patch.object(wahoo_service, "_ensure_authenticated"):
            wahoo_service.client.delete_route = Mock(
                side_effect=RuntimeError("Network error")
            )

            with pytest.raises(RuntimeError):
                await wahoo_service.delete_route(123)


class TestUploadRoute:
    """Test upload route method."""

    @pytest.mark.asyncio
    async def test_upload_route_success(self, wahoo_service):
        """Test successful route upload."""
        with (
            patch.object(wahoo_service, "_ensure_authenticated"),
            patch.object(wahoo_service, "create_route") as mock_create_route,
        ):
            mock_create_route.return_value = {"id": 123, "name": "Uploaded Route"}

            result = await wahoo_service.upload_route(
                route_file="data:application/vnd.fit;base64,test",
                filename="test.fit",
                route_name="Uploaded Route",
            )

            assert result == {"id": 123, "name": "Uploaded Route"}

    @pytest.mark.asyncio
    async def test_upload_route_value_error_401(self, wahoo_service):
        """Test upload route with 401 error."""
        with (
            patch.object(wahoo_service, "_ensure_authenticated"),
            patch.object(wahoo_service, "create_route") as mock_create_route,
        ):
            mock_create_route.side_effect = ValueError("401")

            with pytest.raises(WahooAccessUnauthorized):
                await wahoo_service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Uploaded Route",
                )

    @pytest.mark.asyncio
    async def test_upload_route_already_exists(self, wahoo_service):
        """Test upload route when route already exists."""
        with (
            patch.object(wahoo_service, "_ensure_authenticated"),
            patch.object(wahoo_service, "create_route") as mock_create_route,
        ):
            mock_create_route.side_effect = ValueError("already exists")

            with pytest.raises(ValueError) as exc_info:
                await wahoo_service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Uploaded Route",
                )

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_route_value_error_other(self, wahoo_service):
        """Test upload route with other ValueError."""
        with (
            patch.object(wahoo_service, "_ensure_authenticated"),
            patch.object(wahoo_service, "create_route") as mock_create_route,
        ):
            mock_create_route.side_effect = ValueError("Invalid data")

            with pytest.raises(ValueError):
                await wahoo_service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Uploaded Route",
                )

    @pytest.mark.asyncio
    async def test_upload_route_exception(self, wahoo_service):
        """Test upload route with generic exception."""
        with (
            patch.object(wahoo_service, "_ensure_authenticated"),
            patch.object(wahoo_service, "create_route") as mock_create_route,
        ):
            mock_create_route.side_effect = RuntimeError("Network error")

            with pytest.raises(RuntimeError):
                await wahoo_service.upload_route(
                    route_file="data:application/vnd.fit;base64,test",
                    filename="test.fit",
                    route_name="Uploaded Route",
                )
