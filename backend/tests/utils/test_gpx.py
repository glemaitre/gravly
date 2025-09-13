"""Tests for GPX utility functions."""

from pathlib import Path

import gpxpy
from src.utils.gpx import GPXData, extract_from_gpx_file, generate_gpx_segment


def test_extract_from_gpx_file_with_data_file():
    """Test extract_from_gpx_file function with the file.gpx from data folder."""
    data_dir = Path(__file__).parent / "data"
    gpx_file_path = data_dir / "file.gpx"

    with open(gpx_file_path, encoding="utf-8") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    result = extract_from_gpx_file(gpx, file_id="test_file")

    assert isinstance(result, GPXData)

    assert hasattr(result, "file_id")
    assert hasattr(result, "track_name")
    assert hasattr(result, "points")
    assert hasattr(result, "total_stats")
    assert hasattr(result, "bounds")
    assert hasattr(result, "elevation_stats")

    assert isinstance(result.file_id, str)
    assert result.file_id == "test_file"
    assert isinstance(result.track_name, str)
    assert isinstance(result.points, list)
    assert isinstance(result.total_stats.total_distance, float)
    assert isinstance(result.total_stats.total_elevation_gain, float)
    assert isinstance(result.total_stats.total_elevation_loss, float)
    assert isinstance(result.bounds.north, float)
    assert isinstance(result.bounds.south, float)
    assert isinstance(result.bounds.east, float)
    assert isinstance(result.bounds.west, float)
    assert isinstance(result.elevation_stats.min, float)
    assert isinstance(result.elevation_stats.max, float)

    assert result.bounds.north >= result.bounds.south
    assert result.bounds.east >= result.bounds.west

    assert result.total_stats.total_distance >= 0
    assert result.total_stats.total_elevation_gain >= 0
    assert result.total_stats.total_elevation_loss >= 0
    assert result.total_stats.total_points >= 0

    point = result.points[0]
    assert hasattr(point, "latitude")
    assert hasattr(point, "longitude")
    assert hasattr(point, "elevation")
    assert hasattr(point, "time")
    assert isinstance(point.latitude, float)
    assert isinstance(point.longitude, float)
    assert isinstance(point.elevation, float)
    assert isinstance(point.time, str)


def test_generate_gpx_segment(tmp_dir):
    """Test generate_gpx_segment function with the file.gpx from data folder."""
    data_dir = Path(__file__).parent / "data"
    input_file_path = data_dir / "file.gpx"

    start_index = 10
    end_index = 50
    segment_name = "Test Segment"

    file_id = generate_gpx_segment(
        input_file_path=input_file_path,
        start_index=start_index,
        end_index=end_index,
        segment_name=segment_name,
        output_dir=tmp_dir,
    )

    assert isinstance(file_id, str)
    assert len(file_id) > 0  # UUID should not be empty

    output_file_path = tmp_dir / f"{file_id}.gpx"
    assert output_file_path.exists()

    with open(output_file_path, encoding="utf-8") as gpx_file:
        generated_gpx = gpxpy.parse(gpx_file)

    assert len(generated_gpx.tracks) == 1
    track = generated_gpx.tracks[0]
    assert track.name == segment_name
    assert len(track.segments) == 1
    segment = track.segments[0]

    expected_points = end_index - start_index + 1
    assert len(segment.points) == expected_points

    with open(input_file_path, encoding="utf-8") as original_file:
        original_gpx = gpxpy.parse(original_file)

    original_points = original_gpx.tracks[0].segments[0].points

    generated_first_point = segment.points[0]
    original_first_point = original_points[start_index]
    assert generated_first_point.latitude == original_first_point.latitude
    assert generated_first_point.longitude == original_first_point.longitude
    assert generated_first_point.elevation == original_first_point.elevation
    assert generated_first_point.time == original_first_point.time

    generated_last_point = segment.points[-1]
    original_last_point = original_points[end_index]
    assert generated_last_point.latitude == original_last_point.latitude
    assert generated_last_point.longitude == original_last_point.longitude
    assert generated_last_point.elevation == original_last_point.elevation
    assert generated_last_point.time == original_last_point.time

    for i, generated_point in enumerate(segment.points):
        original_point = original_points[start_index + i]
        assert generated_point.latitude == original_point.latitude
        assert generated_point.longitude == original_point.longitude
        assert generated_point.elevation == original_point.elevation
        assert generated_point.time == original_point.time
