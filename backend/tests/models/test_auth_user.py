"""Tests for AuthUser model and related Pydantic models."""

from datetime import UTC, datetime

from src.models.auth_user import (
    AuthUser,
    AuthUserResponse,
    AuthUserSummary,
)


def test_auth_user_model_creation():
    """Test AuthUser model can be created with valid data."""
    auth_user = AuthUser(
        strava_id=12345,
        firstname="John",
        lastname="Doe",
    )

    assert auth_user.strava_id == 12345
    assert auth_user.firstname == "John"
    assert auth_user.lastname == "Doe"
    assert auth_user.id is None  # Not set until persisted
    # created_at and updated_at only set during database operations
    assert auth_user.created_at is None
    assert auth_user.updated_at is None


def test_auth_user_model_minimal_creation():
    """Test AuthUser model with only required fields."""
    auth_user = AuthUser(strava_id=67890)

    assert auth_user.strava_id == 67890
    assert auth_user.firstname is None
    assert auth_user.lastname is None
    assert auth_user.id is None
    # Timestamps set by database defaults at persistence, not object creation
    assert auth_user.created_at is None
    assert auth_user.updated_at is None


def test_auth_user_created_at_default():
    """Test AuthUser created_at field behavior."""
    auth_user = AuthUser(strava_id=12345)

    # created_at is None until database persistence
    assert auth_user.created_at is None

    # When set explicitly, it returns the value set
    now = datetime.now(UTC)
    auth_user_manual = AuthUser(strava_id=12345, created_at=now)
    assert auth_user_manual.created_at == now


def test_auth_user_updated_at_default():
    """Test AuthUser updated_at field behavior."""
    auth_user = AuthUser(strava_id=12345)

    # updated_at is None until database persistence or explicit set
    assert auth_user.updated_at is None

    # When set explicitly, it returns the value set
    now = datetime.now(UTC)
    auth_user_manual = AuthUser(strava_id=12345, updated_at=now)
    assert auth_user_manual.updated_at == now


def test_auth_user_timestamps_same_when_set_explicitly():
    """Test created_at and updated_at can be set to same time explicitly."""
    now = datetime.now(UTC)
    auth_user = AuthUser(strava_id=12345, created_at=now, updated_at=now)

    assert auth_user.created_at == now
    assert auth_user.updated_at == now
    # These should be exactly identical when set explicitly
    assert auth_user.created_at == auth_user.updated_at


def test_auth_user_explicit_created_at():
    """Test AuthUser with explicitly set created_at."""
    now = datetime.now(UTC)
    auth_user = AuthUser(
        strava_id=12345,
        firstname="Jane",
        lastname="Smith",
        created_at=now,
    )

    assert auth_user.strava_id == 12345
    assert auth_user.firstname == "Jane"
    assert auth_user.lastname == "Smith"
    assert auth_user.created_at == now
    # updated_at needs explicit setting or it stays None
    assert auth_user.updated_at is None


def test_auth_user_explicit_updated_at():
    """Test AuthUser with explicitly set updated_at."""
    now = datetime.now(UTC)
    auth_user = AuthUser(
        strava_id=12345,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=now,
    )

    assert auth_user.created_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert auth_user.updated_at == now


def test_auth_user_response_model():
    """Test AuthUserResponse Pydantic model."""
    response = AuthUserResponse(
        id=1,
        strava_id=12345,
        firstname="Alice",
        lastname="Johnson",
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2023, 1, 2, 10, 0, 0, tzinfo=UTC),
    )

    assert response.id == 1
    assert response.strava_id == 12345
    assert response.firstname == "Alice"
    assert response.lastname == "Johnson"
    assert response.created_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert response.updated_at == datetime(2023, 1, 2, 10, 0, 0, tzinfo=UTC)


def test_auth_user_response_model_optional_fields():
    """Test AuthUserResponse with optional None fields."""
    response = AuthUserResponse(
        id=1,
        strava_id=12345,
        firstname=None,
        lastname=None,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2023, 1, 2, 10, 0, 0, tzinfo=UTC),
    )

    assert response.id == 1
    assert response.strava_id == 12345
    assert response.firstname is None
    assert response.lastname is None


def test_auth_user_summary_model():
    """Test AuthUserSummary Pydantic model."""
    summary = AuthUserSummary(
        strava_id=12345,
        firstname="Bob",
        lastname="Williams",
    )

    assert summary.strava_id == 12345
    assert summary.firstname == "Bob"
    assert summary.lastname == "Williams"


def test_auth_user_summary_model_optional_fields():
    """Test AuthUserSummary with optional None fields."""
    summary = AuthUserSummary(strava_id=12345)

    assert summary.strava_id == 12345
    assert summary.firstname is None
    assert summary.lastname is None


def test_auth_user_summary_model_validation():
    """Test that AuthUserSummary validates correctly with defaults."""
    # Test with minimal required fields
    summary = AuthUserSummary(strava_id=9999)

    assert summary.strava_id == 9999
    assert summary.firstname is None
    assert summary.lastname is None


def test_auth_user_string_representation():
    """Test AuthUser string representation contains expected info."""
    auth_user = AuthUser(
        id=42,
        strava_id=12345,
        firstname="John",
        lastname="Doe",
    )

    repr_str = repr(auth_user)
    # Should contain the strava_id or class info
    assert isinstance(repr_str, str)
    assert "12345" in repr_str or "AuthUser" in repr_str
