"""Tests for GPX utility functions."""

from pathlib import Path

import gpxpy
from src.utils.gpx import GPXData, extract_from_gpx_file


def test_extract_from_gpx_file_with_data_file():
    """Test extract_from_gpx_file function with the file.gpx from data folder."""
    data_dir = Path(__file__).parent / "data"
    gpx_file_path = data_dir / "file.gpx"

    with open(gpx_file_path, "r", encoding="utf-8") as gpx_file:
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
