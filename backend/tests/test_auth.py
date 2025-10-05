"""Tests for authentication API endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Get the FastAPI app instance."""
    from src.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def client(tmp_path, app):
    """Create a test client with temporary directory."""
    with TestClient(app) as test_client:
        yield test_client


def test_authorization_check_unauthorized_user(client):
    """Test authorization check for unauthorized user."""
    # Test with unauthorized Strava ID
    with patch("src.dependencies.SessionLocal", None):
        response = client.get("/api/auth/check-authorization?strava_id=123456")

    # Should return 503 when database is not initialized in test env
    assert response.status_code == 503
    assert "Database not initialized" in response.json()["detail"]


def test_authorization_check_invalid_strava_id(client):
    """Test authorization check with invalid Strava ID."""
    # Test with non-numeric Strava ID
    response = client.get("/api/auth/check-authorization?strava_id=invalid")

    assert response.status_code == 422  # Validation error


def test_authorization_check_missing_strava_id(client):
    """Test authorization check without Strava ID."""
    response = client.get("/api/auth/check-authorization")

    assert response.status_code == 422  # Validation error


def test_authorization_users_list(client):
    """Test listing authorized users endpoint."""
    with patch("src.dependencies.SessionLocal", None):
        response = client.get("/api/auth/users")

    # Should return 503 when database is not initialized in test env
    assert response.status_code == 503
    assert "Database not initialized" in response.json()["detail"]


def test_authorization_check_authorized_user_success(client):
    """Test authorization check for authorized user - success path."""
    from datetime import datetime

    from src.models.auth_user import AuthUser

    # Create a mock AuthUser
    mock_auth_user = AuthUser(
        id=1,
        strava_id=820773,
        firstname="Test",
        lastname="User",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    class MockResult:
        def scalar_one_or_none(self):
            return mock_auth_user

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            return MockResult()

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    with patch("src.dependencies.SessionLocal", new=MockSessionLocal()):
        response = client.get("/api/auth/check-authorization?strava_id=820773")

    assert response.status_code == 200
    data = response.json()
    assert data["authorized"] is True
    assert data["user"]["strava_id"] == 820773
    assert data["user"]["firstname"] == "Test"
    assert data["user"]["lastname"] == "User"


def test_authorization_check_unauthorized_user_success(client):
    """Test authorization check for unauthorized user - success path."""

    class MockResult:
        def scalar_one_or_none(self):
            return None  # No matching user found

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            return MockResult()

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    with patch("src.dependencies.SessionLocal", new=MockSessionLocal()):
        response = client.get("/api/auth/check-authorization?strava_id=123456")

    assert response.status_code == 200
    data = response.json()
    assert data["authorized"] is False
    assert data["user"] is None


def test_authorization_check_database_error(client):
    """Test authorization check with database error."""

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            raise Exception("Database connection failed")

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    with patch("src.dependencies.SessionLocal", new=MockSessionLocal()):
        response = client.get("/api/auth/check-authorization?strava_id=820773")

    assert response.status_code == 500
    data = response.json()
    assert "Failed to check authorization" in data["detail"]


def test_authorization_users_list_success(client):
    """Test listing authorized users - success path."""
    from datetime import datetime

    from src.models.auth_user import AuthUser

    # Create mock authorized users
    mock_users = [
        AuthUser(
            id=1,
            strava_id=820773,
            firstname="Test",
            lastname="User",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        AuthUser(
            id=2,
            strava_id=123456,
            firstname="Another",
            lastname="User",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    class MockResult:
        def scalars(self):
            class MockScalars:
                def all(self):
                    return mock_users

            return MockScalars()

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            return MockResult()

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    with patch("src.dependencies.SessionLocal", new=MockSessionLocal()):
        response = client.get("/api/auth/users")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["strava_id"] == 820773
    assert data[0]["firstname"] == "Test"
    assert data[1]["strava_id"] == 123456


def test_authorization_users_list_empty(client):
    """Test listing authorized users when no users exist."""

    class MockResult:
        def scalars(self):
            class MockScalars:
                def all(self):
                    return []

            return MockScalars()

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            return MockResult()

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    with patch("src.dependencies.SessionLocal", new=MockSessionLocal()):
        response = client.get("/api/auth/users")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_authorization_users_list_database_error(client):
    """Test listing authorized users with database error."""

    class MockSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def execute(self, stmt):
            raise Exception("Database connection failed")

    class MockSessionLocal:
        def __call__(self):
            return MockSession()

    with patch("src.dependencies.SessionLocal", new=MockSessionLocal()):
        response = client.get("/api/auth/users")

    assert response.status_code == 500
    data = response.json()
    assert "Failed to list users" in data["detail"]
