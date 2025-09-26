"""Tests for TrackImage model and related Pydantic models."""

from datetime import UTC, datetime

from src.models.image import (
    TrackImage,
    TrackImageCreateRequest,
    TrackImageResponse,
)


def test_track_image_model_creation():
    """Test TrackImage model can be created with valid data."""
    track_image = TrackImage(
        track_id=1,
        image_id="test-image-123",
        image_url="https://example.com/image.jpg",
        storage_key="storage/test-image-123.jpg",
        filename="test-image.jpg",
        original_filename="original-test-image.jpg",
    )

    assert track_image.track_id == 1
    assert track_image.image_id == "test-image-123"
    assert track_image.image_url == "https://example.com/image.jpg"
    assert track_image.storage_key == "storage/test-image-123.jpg"
    assert track_image.filename == "test-image.jpg"
    assert track_image.original_filename == "original-test-image.jpg"
    assert track_image.id is None  # Not set until persisted
    assert track_image.created_at is None  # Set by database on persistence


def test_track_image_model_minimal_creation():
    """Test TrackImage model with only required fields."""
    track_image = TrackImage(
        track_id=2,
        image_id="minimal-image-456",
        image_url="https://cdn.example.com/minimal.jpg",
        storage_key="storage/minimal-image-456.jpg",
    )

    assert track_image.track_id == 2
    assert track_image.image_id == "minimal-image-456"
    assert track_image.image_url == "https://cdn.example.com/minimal.jpg"
    assert track_image.storage_key == "storage/minimal-image-456.jpg"
    assert track_image.filename is None
    assert track_image.original_filename is None
    assert track_image.id is None
    assert track_image.created_at is None  # Set by database on persistence


def test_track_image_created_at_behavior():
    """Test TrackImage created_at field behavior."""
    track_image = TrackImage(
        track_id=1,
        image_id="current-time-test",
        image_url="https://example.com/time.jpg",
        storage_key="storage/time.jpg",
    )

    # created_at is None until database persistence
    assert track_image.created_at is None

    # When set explicitly, it returns the value set
    now = datetime.now(UTC)
    track_image_manual = TrackImage(
        track_id=1,
        image_id="manual-time-test",
        image_url="https://example.com/time.jpg",
        storage_key="storage/time.jpg",
        created_at=now,
    )
    assert track_image_manual.created_at == now


def test_track_image_explicit_created_at():
    """Test TrackImage with explicitly set created_at."""
    created_time = datetime(2023, 6, 15, 10, 30, 0, tzinfo=UTC)
    track_image = TrackImage(
        track_id=1,
        image_id="explicit-time-test",
        image_url="https://example.com/explicit.jpg",
        storage_key="storage/explicit.jpg",
        created_at=created_time,
    )

    assert track_image.created_at == created_time


def test_track_image_response_model():
    """Test TrackImageResponse Pydantic model."""
    created_time = datetime(2023, 6, 15, 10, 30, 0, tzinfo=UTC)
    response = TrackImageResponse(
        id=100,
        track_id=5,
        image_id="response-test-789",
        image_url="https://example.com/response.jpg",
        storage_key="storage/response.jpg",
        filename="response.jpg",
        original_filename="original-response.jpg",
        created_at=created_time,
    )

    assert response.id == 100
    assert response.track_id == 5
    assert response.image_id == "response-test-789"
    assert response.image_url == "https://example.com/response.jpg"
    assert response.storage_key == "storage/response.jpg"
    assert response.filename == "response.jpg"
    assert response.original_filename == "original-response.jpg"
    assert response.created_at == created_time


def test_track_image_response_model_optional_fields():
    """Test TrackImageResponse with optional None fields."""
    response = TrackImageResponse(
        id=101,
        track_id=6,
        image_id="multiple-files-test",
        image_url="https://example.com/files.jpg",
        storage_key="storage/files.jpg",
        created_at=datetime.now(UTC),
    )

    assert response.id == 101
    assert response.track_id == 6
    assert response.image_id == "multiple-files-test"
    assert response.image_url == "https://example.com/files.jpg"
    assert response.storage_key == "storage/files.jpg"
    assert response.filename is None
    assert response.original_filename is None


def test_track_image_create_request_model():
    """Test TrackImageCreateRequest Pydantic model."""
    request = TrackImageCreateRequest(
        track_id=7,
        image_url="https://example.com/create.jpg",
        storage_key="storage/create.jpg",
        filename="create.jpg",
        original_filename="original-create.jpg",
    )

    assert request.track_id == 7
    assert request.image_url == "https://example.com/create.jpg"
    assert request.storage_key == "storage/create.jpg"
    assert request.filename == "create.jpg"
    assert request.original_filename == "original-create.jpg"


def test_track_image_create_request_minimal():
    """Test TrackImageCreateRequest with only required fields."""
    request = TrackImageCreateRequest(
        track_id=8,
        image_url="https://example.com/required.jpg",
        storage_key="storage/required.jpg",
    )

    assert request.track_id == 8
    assert request.image_url == "https://example.com/required.jpg"
    assert request.storage_key == "storage/required.jpg"
    assert request.filename is None
    assert request.original_filename is None


def test_track_image_string_representation():
    """Test TrackImage string representation."""
    track_image = TrackImage(
        id=999,
        track_id=1,
        image_id="string-test",
        image_url="https://example.com/string.jpg",
        storage_key="storage/string.jpg",
    )

    repr_str = repr(track_image)
    assert isinstance(repr_str, str)
    # Should contain class name or relevant identifiers
    assert "TrackImage" in repr_str or "string-test" in repr_str


def test_track_image_foreign_key_relationship():
    """Test TrackImage foreign key fields are properly defined."""
    track_image = TrackImage(
        track_id=999,
        image_id="foreign-key-test",
        image_url="https://example.com/foreign.jpg",
        storage_key="storage/foreign.jpg",
    )

    # Test that track_id is set correctly
    assert track_image.track_id == 999
    assert isinstance(track_image.track_id, int)


def test_track_image_unique_constraints():
    """Test TrackImage unique fields."""
    # Test image_id uniqueness (should be enforced at database level)
    track_image1 = TrackImage(
        track_id=1,
        image_id="unique-test-001",
        image_url="https://example.com/1.jpg",
        storage_key="storage/1.jpg",
    )

    track_image2 = TrackImage(
        track_id=2,  # Different track
        image_id="unique-test-001",  # Same image_id - violates unique in DB
        image_url="https://example.com/2.jpg",
        storage_key="storage/2.jpg",
    )

    # Both should be createable at model level (constraint enforced at DB level)
    assert track_image1.image_id == "unique-test-001"
    assert track_image2.image_id == "unique-test-001"
    assert track_image1.track_id != track_image2.track_id


def test_track_image_long_url_values():
    """Test TrackImage handles long URL values correctly."""
    long_url = (
        "https://very-long-domain-name-for-testing.com/very-long-path/with/"
        "many/segments/and/a-very-long-filename-that-exceeds-typical.txt"
    )
    long_storage_key = (
        "storage-base-path/very-long-storage-path/that-might-be/"
        "very-long-and-contained-within/databases/storage-systems"
    )

    track_image = TrackImage(
        track_id=1,
        image_id="long-url-test",
        image_url=long_url,
        storage_key=long_storage_key,
        filename="long-name-file.jpg",
        original_filename="this-is-a-very-long-original-file-name.jpg",
    )

    assert track_image.image_url == long_url
    assert track_image.storage_key == long_storage_key
    assert len(track_image.image_url) > 100  # Verify it's actually long
    assert len(track_image.storage_key) > 100
