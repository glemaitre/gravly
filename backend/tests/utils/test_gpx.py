"""Tests for GPX utility functions."""

from pathlib import Path

import gpxpy
import pytest
from src.utils.gpx import (
    GPXBounds,
    GPXData,
    convert_gpx_to_fit,
    extract_from_gpx_file,
    generate_gpx_segment,
)


def test_extract_from_gpx_file_with_data_file():
    """Test extract_from_gpx_file function with the file.gpx from data folder."""
    data_dir = Path(__file__).parent.parent / "data"
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
    assert isinstance(result.bounds.min_elevation, float)
    assert isinstance(result.bounds.max_elevation, float)

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


def test_generate_gpx_segment(tmp_path):
    """Test generate_gpx_segment function with the file.gpx from data folder."""
    data_dir = Path(__file__).parent.parent / "data"
    input_file_path = data_dir / "file.gpx"

    start_index = 10
    end_index = 50
    segment_name = "Test Segment"

    file_id, output_file_path, bounds = generate_gpx_segment(
        input_file_path=input_file_path,
        start_index=start_index,
        end_index=end_index,
        segment_name=segment_name,
        output_dir=tmp_path,
    )

    assert isinstance(file_id, str)
    assert len(file_id) > 0  # UUID should not be empty

    assert isinstance(output_file_path, Path)
    assert output_file_path.exists()

    # Test bounds return value
    assert isinstance(bounds, GPXBounds)
    assert isinstance(bounds.north, float)
    assert isinstance(bounds.south, float)
    assert isinstance(bounds.east, float)
    assert isinstance(bounds.west, float)
    assert isinstance(bounds.min_elevation, float)
    assert isinstance(bounds.max_elevation, float)
    assert bounds.south <= bounds.north
    assert bounds.west <= bounds.east

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

    # Test that bounds match the actual min/max values from the segment points
    actual_min_lat = min(point.latitude for point in segment.points)
    actual_max_lat = max(point.latitude for point in segment.points)
    actual_min_lon = min(point.longitude for point in segment.points)
    actual_max_lon = max(point.longitude for point in segment.points)

    assert bounds.south == actual_min_lat  # min_latitude
    assert bounds.west == actual_min_lon  # min_longitude
    assert bounds.north == actual_max_lat  # max_latitude
    assert bounds.east == actual_max_lon  # max_longitude


class TestConvertGpxToFit:
    """Test cases for convert_gpx_to_fit function."""

    def test_convert_gpx_to_fit_success(self):
        """Test successful conversion of GPX to FIT format."""
        # Load test GPX file
        gpx_file_path = Path(__file__).parent.parent / "data" / "file.gpx"
        with open(gpx_file_path) as f:
            gpx = gpxpy.parse(f)

        # Convert to FIT
        fit_bytes = convert_gpx_to_fit(gpx, "Test Course")

        # Verify we get bytes back
        assert isinstance(fit_bytes, bytes)
        assert len(fit_bytes) > 0

        # Verify FIT file starts with correct header (FIT files start with 0x0C)
        assert fit_bytes[0] == 0x0C

    def test_convert_gpx_to_fit_with_custom_name(self):
        """Test conversion with custom course name."""
        gpx_file_path = Path(__file__).parent.parent / "data" / "file.gpx"
        with open(gpx_file_path) as f:
            gpx = gpxpy.parse(f)

        custom_name = "My Custom Cycling Route"
        fit_bytes = convert_gpx_to_fit(gpx, custom_name)

        assert isinstance(fit_bytes, bytes)
        assert len(fit_bytes) > 0

    def test_convert_gpx_to_fit_empty_tracks(self):
        """Test conversion with GPX file that has no tracks."""
        gpx = gpxpy.gpx.GPX()

        with pytest.raises(
            ValueError, match="GPX file must contain at least one track with segments"
        ):
            convert_gpx_to_fit(gpx)

    def test_convert_gpx_to_fit_empty_segments(self):
        """Test conversion with GPX file that has tracks but no segments."""
        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(track)

        with pytest.raises(
            ValueError, match="GPX file must contain at least one track with segments"
        ):
            convert_gpx_to_fit(gpx)

    def test_convert_gpx_to_fit_empty_points(self):
        """Test conversion with GPX file that has tracks and segments but no points."""
        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()
        segment = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(segment)
        gpx.tracks.append(track)

        with pytest.raises(ValueError, match="No track points found in GPX file"):
            convert_gpx_to_fit(gpx)

    def test_convert_gpx_to_fit_single_point(self):
        """Test conversion with GPX file containing only one point."""
        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()
        segment = gpxpy.gpx.GPXTrackSegment()

        # Add a single point
        point = gpxpy.gpx.GPXTrackPoint(
            latitude=46.9192890, longitude=3.9921170, elevation=576.0
        )
        segment.points.append(point)
        track.segments.append(segment)
        gpx.tracks.append(track)

        fit_bytes = convert_gpx_to_fit(gpx, "Single Point Course")

        assert isinstance(fit_bytes, bytes)
        assert len(fit_bytes) > 0

    def test_convert_gpx_to_fit_multiple_segments(self):
        """Test conversion with GPX file containing multiple segments."""
        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()

        # Add first segment with points
        segment1 = gpxpy.gpx.GPXTrackSegment()
        for i in range(3):
            point = gpxpy.gpx.GPXTrackPoint(
                latitude=46.9192890 + i * 0.001,
                longitude=3.9921170 + i * 0.001,
                elevation=576.0 + i * 10,
            )
            segment1.points.append(point)
        track.segments.append(segment1)

        # Add second segment (should be ignored)
        segment2 = gpxpy.gpx.GPXTrackSegment()
        for i in range(2):
            point = gpxpy.gpx.GPXTrackPoint(
                latitude=46.9292890 + i * 0.001,
                longitude=3.9921170 + i * 0.001,
                elevation=600.0 + i * 10,
            )
            segment2.points.append(point)
        track.segments.append(segment2)

        gpx.tracks.append(track)

        fit_bytes = convert_gpx_to_fit(gpx, "Multi-Segment Course")

        assert isinstance(fit_bytes, bytes)
        assert len(fit_bytes) > 0

    def test_convert_gpx_to_fit_default_course_name(self):
        """Test conversion with default course name."""
        gpx_file_path = Path(__file__).parent.parent / "data" / "file.gpx"
        with open(gpx_file_path) as f:
            gpx = gpxpy.parse(f)

        fit_bytes = convert_gpx_to_fit(gpx)  # No course name provided

        assert isinstance(fit_bytes, bytes)
        assert len(fit_bytes) > 0

    def test_convert_gpx_to_fit_fit_file_structure(self):
        """Test that the generated FIT file has proper structure."""
        gpx_file_path = Path(__file__).parent.parent / "data" / "file.gpx"
        with open(gpx_file_path) as f:
            gpx = gpxpy.parse(f)

        fit_bytes = convert_gpx_to_fit(gpx, "Structure Test")

        # FIT files should have at least a header and some data
        assert len(fit_bytes) >= 14  # Minimum FIT file size

        # Check FIT file header (first 12 bytes)
        # Byte 0: Header size (should be 12 for FIT files)
        assert fit_bytes[0] == 0x0C

        # Byte 1: Protocol version
        assert fit_bytes[1] >= 0x10  # Protocol version 1.0 or higher

        # Bytes 2-3: Profile version (little endian)
        profile_version = int.from_bytes(fit_bytes[2:4], byteorder="little")
        assert profile_version > 0

        # Bytes 4-7: Data size (little endian)
        data_size = int.from_bytes(fit_bytes[4:8], byteorder="little")
        assert data_size > 0

        # Byte 8: Data type (should be '.FIT')
        assert fit_bytes[8:12] == b".FIT"
