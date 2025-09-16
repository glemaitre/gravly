from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Index
from src.models.track import (
    SurfaceType,
    TireType,
    Track,
    TrackResponse,
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
    """Test TrackResponse Pydantic model."""
    response = TrackResponse(
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

    assert response.id == 1
    assert response.file_path == "/path/to/track.gpx"
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
    """Test TrackResponse accepts string path and keeps it as string."""
    response = TrackResponse(
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

    assert isinstance(response.file_path, str)
    assert response.file_path == "/path/to/track.gpx"


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


def test_track_model_table_args_defined():
    """Test that Track model has __table_args__ defined for database indices."""
    assert hasattr(Track, "__table_args__")
    assert Track.__table_args__ is not None
    assert isinstance(Track.__table_args__, tuple)
    assert len(Track.__table_args__) > 0


def test_track_model_bounds_intersection_index():
    """Test that Track model has the bounds intersection index defined."""
    table_args = Track.__table_args__

    bounds_index = None
    for arg in table_args:
        if isinstance(arg, Index) and arg.name == "idx_track_bounds_intersection":
            bounds_index = arg
            break

    assert bounds_index is not None, "Bounds intersection index not found"
    assert bounds_index.name == "idx_track_bounds_intersection"
    assert "bound_north" in bounds_index.columns
    assert "bound_south" in bounds_index.columns
    assert "bound_east" in bounds_index.columns
    assert "bound_west" in bounds_index.columns


def test_track_model_index_columns_order():
    """Test that the bounds intersection index has columns in the correct order for
    performance."""
    table_args = Track.__table_args__

    bounds_index = None
    for arg in table_args:
        if isinstance(arg, Index) and arg.name == "idx_track_bounds_intersection":
            bounds_index = arg
            break

    assert bounds_index is not None

    expected_columns = ["bound_north", "bound_south", "bound_east", "bound_west"]
    actual_columns = [col.name for col in bounds_index.columns]

    assert actual_columns == expected_columns, (
        f"Expected columns {expected_columns}, got {actual_columns}"
    )


def test_track_model_index_is_composite():
    """Test that the bounds intersection index is a composite index with multiple
    columns."""
    table_args = Track.__table_args__

    bounds_index = None
    for arg in table_args:
        if isinstance(arg, Index) and arg.name == "idx_track_bounds_intersection":
            bounds_index = arg
            break

    assert bounds_index is not None
    assert len(bounds_index.columns) == 4, (
        "Bounds intersection index should have 4 columns"
    )
    assert bounds_index.columns[0].name == "bound_north"
    assert bounds_index.columns[1].name == "bound_south"
    assert bounds_index.columns[2].name == "bound_east"
    assert bounds_index.columns[3].name == "bound_west"


def test_track_with_gpx_data_response_creation():
    """Test that TrackWithGPXDataResponse can be created with GPX XML data from file."""
    from pathlib import Path

    from src.models.track import TrackWithGPXDataResponse

    # Read actual GPX file content (equivalent to opening file.gpx directly)
    test_data_dir = Path(__file__).parent.parent / "data"
    gpx_file_path = test_data_dir / "file.gpx"

    with open(gpx_file_path, "r", encoding="utf-8") as f:
        gpx_xml_data = f.read()

    response = TrackWithGPXDataResponse(
        id=1,
        file_path="test/path.gpx",
        name="Test Track",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=2.0,
        bound_west=1.0,
        surface_type="forest-trail",
        difficulty_level=3,
        track_type="segment",
        tire_dry="semi-slick",
        tire_wet="knobs",
        comments="Test comment",
        gpx_xml_data=gpx_xml_data,
    )

    assert response.id == 1
    assert response.name == "Test Track"
    assert response.gpx_xml_data == gpx_xml_data
    assert isinstance(response.gpx_xml_data, str)

    # Verify the GPX XML content is valid
    assert response.gpx_xml_data.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<gpx" in response.gpx_xml_data
    assert "<trk>" in response.gpx_xml_data
    assert "<trkpt" in response.gpx_xml_data
    assert len(response.gpx_xml_data) > 1000  # Ensure we have substantial content


def test_track_with_gpx_data_response_none_gpx():
    """Test that TrackWithGPXDataResponse can be created with None gpx_xml_data."""
    from src.models.track import TrackWithGPXDataResponse

    response = TrackWithGPXDataResponse(
        id=1,
        file_path="test/path.gpx",
        name="Test Track",
        bound_north=45.0,
        bound_south=44.0,
        bound_east=2.0,
        bound_west=1.0,
        surface_type="forest-trail",
        difficulty_level=3,
        track_type="segment",
        tire_dry="semi-slick",
        tire_wet="knobs",
        comments="Test comment",
        gpx_xml_data=None,
    )

    assert response.gpx_xml_data is None


def test_uuid_extraction_from_file_path():
    """Test that UUID can be extracted from file paths correctly."""

    # Test local storage path
    local_path = "local:///gpx-segments/c45c8b1d-4dc0-435c-9238-f75a1e2a9359.gpx"
    file_id = Path(local_path).stem
    assert file_id == "c45c8b1d-4dc0-435c-9238-f75a1e2a9359"

    # Test S3 path
    s3_path = "s3://my-bucket/gpx-segments/another-uuid-1234-5678-9abc.gpx"
    file_id = Path(s3_path).stem
    assert file_id == "another-uuid-1234-5678-9abc"

    # Test simple path
    simple_path = "/path/to/file.gpx"
    file_id = Path(simple_path).stem
    assert file_id == "file"


def test_local_storage_manager_url_prefix_stripping(tmp_path):
    """Test that LocalStorageManager correctly strips storage URL prefixes."""
    from src.utils.storage import LocalStorageManager

    from backend.src.utils.config import LocalStorageConfig

    config = LocalStorageConfig(
        storage_type="local",
        storage_root=str(tmp_path / "storage"),
        base_url="http://test:8080/storage",
    )

    manager = LocalStorageManager(config)

    # Test with storage URL
    storage_url = "local:///gpx-segments/test-file.gpx"
    file_path = manager.get_file_path(storage_url)
    expected_path = tmp_path / "storage" / "gpx-segments" / "test-file.gpx"
    assert file_path == expected_path

    # Test with regular storage key
    storage_key = "gpx-segments/test-file.gpx"
    file_path = manager.get_file_path(storage_key)
    expected_path = tmp_path / "storage" / "gpx-segments" / "test-file.gpx"
    assert file_path == expected_path


def test_local_storage_manager_load_gpx_data(tmp_path):
    """Test that LocalStorageManager.load_gpx_data works correctly."""
    from src.utils.storage import LocalStorageManager

    from backend.src.utils.config import LocalStorageConfig

    config = LocalStorageConfig(
        storage_type="local",
        storage_root=str(tmp_path / "storage"),
        base_url="http://test:8080/storage",
    )

    manager = LocalStorageManager(config)

    # Create a test file
    test_file_path = tmp_path / "storage" / "gpx-segments" / "test-file.gpx"
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_content = b"<?xml version='1.0'?><gpx><trk><name>Test</name></trk></gpx>"
    test_file_path.write_bytes(test_content)

    # Test with storage URL
    storage_url = "local:///gpx-segments/test-file.gpx"
    result = manager.load_gpx_data(storage_url)
    assert result == test_content

    # Test with regular storage key
    storage_key = "gpx-segments/test-file.gpx"
    result = manager.load_gpx_data(storage_key)
    assert result == test_content

    # Test with non-existent file
    result = manager.load_gpx_data("gpx-segments/non-existent.gpx")
    assert result is None
