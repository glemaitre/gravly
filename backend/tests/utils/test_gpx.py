"""Tests for GPX utility functions."""

from pathlib import Path

import gpxpy
from src.utils.gpx import extract_from_gpx


def test_extract_from_gpx_with_data_file():
    """Test extract_from_gpx function with the file.gpx from data folder."""
    data_dir = Path(__file__).parent / "data"
    gpx_file_path = data_dir / "file.gpx"

    with open(gpx_file_path, "r", encoding="utf-8") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    result = extract_from_gpx(gpx)
    assert isinstance(result, dict)

    required_keys = {
        "name",
        "points",
        "total_distance",
        "total_elevation_gain",
        "total_elevation_loss",
        "bounds",
        "elevation_stats",
    }
    assert set(result.keys()) == required_keys

    assert isinstance(result["name"], str)
    assert isinstance(result["points"], list)
    assert isinstance(result["total_distance"], float)
    assert isinstance(result["total_elevation_gain"], float)
    assert isinstance(result["total_elevation_loss"], float)
    assert isinstance(result["bounds"], dict)
    assert isinstance(result["elevation_stats"], dict)

    bounds_keys = {"north", "south", "east", "west"}
    assert set(result["bounds"].keys()) == bounds_keys
    assert result["bounds"]["north"] >= result["bounds"]["south"]
    assert result["bounds"]["east"] >= result["bounds"]["west"]

    elevation_stats_keys = {"min", "max", "total_points"}
    assert set(result["elevation_stats"].keys()) == elevation_stats_keys
    assert result["elevation_stats"]["total_points"] >= 0

    if result["points"]:
        point = result["points"][0]
        point_keys = {"lat", "lon", "elevation", "time"}
        assert set(point.keys()) == point_keys
        for key in point_keys:
            assert key in point
            if key == "time":
                assert isinstance(point[key], str)
            else:
                assert isinstance(point[key], float)

    assert result["total_distance"] >= 0
    assert result["total_elevation_gain"] >= 0
    assert result["total_elevation_loss"] >= 0
