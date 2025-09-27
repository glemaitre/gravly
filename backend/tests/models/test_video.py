"""Tests for the TrackVideo model."""

from datetime import UTC, datetime

from src.models.video import TrackVideo, TrackVideoCreateRequest, TrackVideoResponse


def test_track_video_model_creation():
    """Test TrackVideo model can be created with valid data."""
    video = TrackVideo(
        track_id=1,
        video_id="test-video-123",
        video_url="https://youtube.com/watch?v=test123",
        video_title="Test Video",
        platform="youtube",
    )

    assert video.track_id == 1
    assert video.video_id == "test-video-123"
    assert video.video_url == "https://youtube.com/watch?v=test123"
    assert video.video_title == "Test Video"
    assert video.platform == "youtube"
    # created_at is set by SQLAlchemy when inserted into database
    assert video.created_at is None


def test_track_video_model_with_minimal_data():
    """Test TrackVideo model can be created with minimal required data."""
    video = TrackVideo(
        track_id=1,
        video_id="minimal-video",
        video_url="https://vimeo.com/123456",
        platform="vimeo",
    )

    assert video.track_id == 1
    assert video.video_id == "minimal-video"
    assert video.video_url == "https://vimeo.com/123456"
    assert video.platform == "vimeo"
    assert video.video_title is None
    # created_at is set by SQLAlchemy when inserted into database
    assert video.created_at is None


def test_track_video_response_model():
    """Test TrackVideoResponse Pydantic model."""
    now = datetime.now(UTC)
    response = TrackVideoResponse(
        id=1,
        track_id=123,
        video_id="test-video-789",
        video_url="https://youtube.com/watch?v=test789",
        video_title="Test Response Video",
        platform="youtube",
        created_at=now,
    )

    assert response.id == 1
    assert response.track_id == 123
    assert response.video_id == "test-video-789"
    assert response.video_url == "https://youtube.com/watch?v=test789"
    assert response.video_title == "Test Response Video"
    assert response.platform == "youtube"
    assert response.created_at == now


def test_track_video_response_model_with_null_title():
    """Test TrackVideoResponse Pydantic model with null title."""
    now = datetime.now(UTC)
    response = TrackVideoResponse(
        id=2,
        track_id=456,
        video_id="test-video-null-title",
        video_url="https://vimeo.com/456789",
        video_title=None,
        platform="vimeo",
        created_at=now,
    )

    assert response.id == 2
    assert response.track_id == 456
    assert response.video_id == "test-video-null-title"
    assert response.video_url == "https://vimeo.com/456789"
    assert response.video_title is None
    assert response.platform == "vimeo"
    assert response.created_at == now


def test_track_video_create_request_model():
    """Test TrackVideoCreateRequest Pydantic model."""
    request = TrackVideoCreateRequest(
        track_id=456,
        video_url="https://vimeo.com/789012",
        video_title="Create Request Video",
        platform="vimeo",
    )

    assert request.track_id == 456
    assert request.video_url == "https://vimeo.com/789012"
    assert request.video_title == "Create Request Video"
    assert request.platform == "vimeo"


def test_track_video_create_request_model_with_null_title():
    """Test TrackVideoCreateRequest Pydantic model with null title."""
    request = TrackVideoCreateRequest(
        track_id=789, video_url="https://youtube.com/watch?v=test", platform="youtube"
    )

    assert request.track_id == 789
    assert request.video_url == "https://youtube.com/watch?v=test"
    assert request.video_title is None
    assert request.platform == "youtube"


def test_video_platforms():
    """Test different video platforms."""
    platforms = ["youtube", "vimeo", "other"]

    for i, platform in enumerate(platforms):
        video = TrackVideo(
            track_id=1,
            video_id=f"test-video-{i}",
            video_url=f"https://example.com/video{i}",
            platform=platform,
        )
        assert video.platform == platform
        assert video.video_url == f"https://example.com/video{i}"


def test_track_video_table_name():
    """Test that TrackVideo has correct table name."""
    assert TrackVideo.__tablename__ == "track_videos"
