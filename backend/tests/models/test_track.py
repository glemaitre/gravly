from datetime import UTC, datetime
from pathlib import Path

from src.models.track import (
    SurfaceType,
    TireType,
    Track,
    TrackCreateResponse,
    TrackType,
)


def test_track_type_enum_values():
    """Test TrackType enum has correct values."""
    assert TrackType.SEGMENT.value == "segment"
    assert TrackType.ROUTE.value == "route"


def test_surface_type_enum_values():
    """Test SurfaceType enum has correct values."""
    assert SurfaceType.BIG_STONE_ROAD.value == "big-stone-road"
    assert SurfaceType.BROKEN_PAVED_ROAD.value == "broken-paved-road"
    assert SurfaceType.DIRTY_ROAD.value == "dirty-road"
    assert SurfaceType.FIELD_TRAIL.value == "field-trail"
    assert SurfaceType.FOREST_TRAIL.value == "forest-trail"
    assert SurfaceType.SMALL_STONE_ROAD.value == "small-stone-road"


def test_tire_type_enum_values():
    """Test TireType enum has correct values."""
    assert TireType.SLICK.value == "slick"
    assert TireType.SEMI_SLICK.value == "semi-slick"
    assert TireType.KNOBS.value == "knobs"


def test_track_model_creation():
    """Test Track model can be created with valid data."""
    track = Track(
        file_path="/path/to/track.gpx",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=2.0,
        bound_west=1.0,
        name="Test Track",
        track_type=TrackType.SEGMENT,
        difficulty_level=3,
        surface_type=SurfaceType.FOREST_TRAIL,
        tire_dry=TireType.KNOBS,
        tire_wet=TireType.KNOBS,
        comments="Test track for unit testing",
    )

    assert track.file_path == "/path/to/track.gpx"
    assert track.bound_north == 45.0
    assert track.bound_south == 44.0
    assert track.bound_east == 2.0
    assert track.bound_west == 1.0
    assert track.name == "Test Track"
    assert track.track_type == TrackType.SEGMENT
    assert track.difficulty_level == 3
    assert track.surface_type == SurfaceType.FOREST_TRAIL
    assert track.tire_dry == TireType.KNOBS
    assert track.tire_wet == TireType.KNOBS
    assert track.comments == "Test track for unit testing"


def test_track_model_optional_fields():
    """Test Track model with minimal required fields."""
    track = Track(file_path="/path/to/track.gpx", name="Minimal Track")

    assert track.file_path == "/path/to/track.gpx"
    assert track.name == "Minimal Track"
    assert track.bound_north is None
    assert track.bound_south is None
    assert track.bound_east is None
    assert track.bound_west is None
    assert track.track_type is None
    assert track.difficulty_level is None
    assert track.surface_type is None
    assert track.tire_dry is None
    assert track.tire_wet is None
    assert track.comments is None


def test_track_model_created_at_field():
    """Test Track model has created_at field that can be set."""
    # Test that created_at can be set explicitly
    now = datetime.now(UTC)
    track = Track(file_path="/path/to/track.gpx", name="Test Track", created_at=now)

    assert track.created_at is not None
    assert isinstance(track.created_at, datetime)
    assert track.created_at == now


def test_track_create_response_model():
    """Test TrackCreateResponse Pydantic model."""
    response = TrackCreateResponse(
        id=1,
        file_path=Path("/path/to/track.gpx"),
        bound_north=45.0,
        bound_south=44.0,
        bound_east=2.0,
        bound_west=1.0,
        name="Test Track",
        track_type="segment",
        difficulty_level=3,
        surface_type="forest-trail",
        tire_dry="knobs",
        tire_wet="knobs",
        comments="Test track for unit testing",
    )

    assert response.id == 1
    assert response.file_path == Path("/path/to/track.gpx")
    assert response.bound_north == 45.0
    assert response.bound_south == 44.0
    assert response.bound_east == 2.0
    assert response.bound_west == 1.0
    assert response.name == "Test Track"
    assert response.track_type == "segment"
    assert response.difficulty_level == 3
    assert response.surface_type == "forest-trail"
    assert response.tire_dry == "knobs"
    assert response.tire_wet == "knobs"
    assert response.comments == "Test track for unit testing"


def test_track_create_response_with_string_path():
    """Test TrackCreateResponse accepts string path and converts to Path."""
    response = TrackCreateResponse(
        id=1,
        file_path="/path/to/track.gpx",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=2.0,
        bound_west=1.0,
        name="Test Track",
        track_type="segment",
        difficulty_level=3,
        surface_type="forest-trail",
        tire_dry="knobs",
        tire_wet="knobs",
        comments="Test track for unit testing",
    )

    assert isinstance(response.file_path, Path)
    assert str(response.file_path) == "/path/to/track.gpx"


def test_track_model_with_all_enum_values():
    """Test Track model with all possible enum values."""
    # Test all TrackType values
    for track_type in TrackType:
        track = Track(
            file_path="/path/to/track.gpx",
            name=f"Track {track_type.value}",
            track_type=track_type,
        )
        assert track.track_type == track_type

    # Test all SurfaceType values
    for surface_type in SurfaceType:
        track = Track(
            file_path="/path/to/track.gpx",
            name=f"Track {surface_type.value}",
            surface_type=surface_type,
        )
        assert track.surface_type == surface_type

    # Test all TireType values
    for tire_type in TireType:
        track = Track(
            file_path="/path/to/track.gpx",
            name=f"Track {tire_type.value}",
            tire_dry=tire_type,
            tire_wet=tire_type,
        )
        assert track.tire_dry == tire_type
        assert track.tire_wet == tire_type


def test_track_model_bounds_validation():
    """Test Track model with various bound values."""
    # Test with valid bounds
    track = Track(
        file_path="/path/to/track.gpx",
        name="Valid Bounds Track",
        bound_north=45.5,
        bound_south=44.2,
        bound_east=2.8,
        bound_west=1.1,
    )

    assert track.bound_north == 45.5
    assert track.bound_south == 44.2
    assert track.bound_east == 2.8
    assert track.bound_west == 1.1


def test_track_model_difficulty_levels():
    """Test Track model with various difficulty levels."""
    for difficulty in [1, 2, 3, 4, 5]:
        track = Track(
            file_path="/path/to/track.gpx",
            name=f"Difficulty {difficulty} Track",
            difficulty_level=difficulty,
        )
        assert track.difficulty_level == difficulty


def test_track_model_long_text_fields():
    """Test Track model with long text in file_path and comments."""
    long_path = "/" + "a" * 1000 + ".gpx"
    long_comments = "This is a very long comment. " * 100

    track = Track(file_path=long_path, name="Long Text Track", comments=long_comments)

    assert track.file_path == long_path
    assert track.comments == long_comments
