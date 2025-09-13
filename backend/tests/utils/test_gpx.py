"""
Unit tests for GPX Editor module.

This module contains comprehensive tests for the GPX processing functions,
particularly the parse_gpx_file function.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from backend.src.utils.gpx import (
    GPXProcessingError,
    parse_gpx_file,
)


class TestParseGpxFile:
    """Test cases for the parse_gpx_file function."""

    def create_test_gpx_file(self, content: str) -> str:
        """Create a temporary GPX file with the given content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            f.write(content)
            return f.name

    def test_parse_gpx_file_valid_with_elevation(self):
        """Test parsing a valid GPX file with elevation data."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
      <trkpt lat="46.1" lon="4.1">
        <ele>200.0</ele>
        <time>2023-01-01T12:01:00Z</time>
      </trkpt>
      <trkpt lat="46.2" lon="4.2">
        <ele>150.0</ele>
        <time>2023-01-01T12:02:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            result = parse_gpx_file(file_path)

            # Check basic structure
            assert result["name"] == "Test Track"
            assert len(result["points"]) == 3

            # Check points
            assert result["points"][0]["lat"] == 46.0
            assert result["points"][0]["lon"] == 4.0
            assert result["points"][0]["elevation"] == 100.0
            assert result["points"][0]["time"] == "2023-01-01T12:00:00+00:00"

            # Check distance calculation (should be > 0)
            assert result["total_distance"] > 0

            # Check elevation calculations
            assert result["total_elevation_gain"] == 100.0  # 200 - 100
            assert result["total_elevation_loss"] == 50.0  # 200 - 150

            # Check bounds
            assert result["bounds"]["north"] == 46.2
            assert result["bounds"]["south"] == 46.0
            assert result["bounds"]["east"] == 4.2
            assert result["bounds"]["west"] == 4.0

            # Check elevation stats
            assert result["elevation_stats"]["min"] == 100.0
            assert result["elevation_stats"]["max"] == 200.0
            assert result["elevation_stats"]["total_points"] == 3

        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_no_elevation_data(self):
        """Test parsing a GPX file without elevation data."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
      <trkpt lat="46.1" lon="4.1">
        <time>2023-01-01T12:01:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            with pytest.raises(HTTPException) as exc_info:
                parse_gpx_file(file_path)

            assert exc_info.value.status_code == 400
            assert "GPX file must contain elevation data" in str(exc_info.value.detail)
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_partial_elevation_data(self):
        """Test parsing a GPX file with some points missing elevation data."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
      <trkpt lat="46.1" lon="4.1">
        <time>2023-01-01T12:01:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            with pytest.raises(HTTPException) as exc_info:
                parse_gpx_file(file_path)

            assert exc_info.value.status_code == 400
            assert "All track points must have elevation data" in str(
                exc_info.value.detail
            )
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_no_tracks(self):
        """Test parsing a GPX file without tracks."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            with pytest.raises(ValueError) as exc_info:
                parse_gpx_file(file_path)

            assert "No tracks found in GPX file" in str(exc_info.value)
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_unnamed_track(self):
        """Test parsing a GPX file with an unnamed track."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            result = parse_gpx_file(file_path)
            assert result["name"] == "Unnamed Track"
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_single_point(self):
        """Test parsing a GPX file with a single point."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Single Point Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            result = parse_gpx_file(file_path)

            assert result["name"] == "Single Point Track"
            assert len(result["points"]) == 1
            assert result["total_distance"] == 0.0  # No distance for single point
            assert result["total_elevation_gain"] == 0.0
            assert result["total_elevation_loss"] == 0.0
            assert result["bounds"]["north"] == 46.0
            assert result["bounds"]["south"] == 46.0
            assert result["elevation_stats"]["min"] == 100.0
            assert result["elevation_stats"]["max"] == 100.0
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_no_time_data(self):
        """Test parsing a GPX file without time data."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>No Time Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
      </trkpt>
      <trkpt lat="46.1" lon="4.1">
        <ele>200.0</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            result = parse_gpx_file(file_path)

            assert result["name"] == "No Time Track"
            assert len(result["points"]) == 2
            assert result["points"][0]["time"] is None
            assert result["points"][1]["time"] is None
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_file_not_found(self):
        """Test parsing a non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_gpx_file("non_existent_file.gpx")

    def test_parse_gpx_file_invalid_xml(self):
        """Test parsing an invalid XML file."""
        gpx_content = "This is not valid XML"

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            with pytest.raises(Exception):  # gpxpy will raise an exception
                parse_gpx_file(file_path)
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_elevation_gain_loss_calculation(self):
        """Test elevation gain and loss calculations."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Elevation Test Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
      <trkpt lat="46.1" lon="4.1">
        <ele>150.0</ele>
        <time>2023-01-01T12:01:00Z</time>
      </trkpt>
      <trkpt lat="46.2" lon="4.2">
        <ele>120.0</ele>
        <time>2023-01-01T12:02:00Z</time>
      </trkpt>
      <trkpt lat="46.3" lon="4.3">
        <ele>180.0</ele>
        <time>2023-01-01T12:03:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            result = parse_gpx_file(file_path)

            # Elevation changes: 100->150 (+50), 150->120 (-30), 120->180 (+60)
            assert result["total_elevation_gain"] == 110.0  # 50 + 60
            assert result["total_elevation_loss"] == 30.0  # 30
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_bounds_calculation(self):
        """Test bounds calculation."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Bounds Test Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
      <trkpt lat="48.0" lon="2.0">
        <ele>200.0</ele>
        <time>2023-01-01T12:01:00Z</time>
      </trkpt>
      <trkpt lat="47.0" lon="6.0">
        <ele>150.0</ele>
        <time>2023-01-01T12:02:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            result = parse_gpx_file(file_path)

            assert result["bounds"]["north"] == 48.0
            assert result["bounds"]["south"] == 46.0
            assert result["bounds"]["east"] == 6.0
            assert result["bounds"]["west"] == 2.0
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_multiple_segments(self):
        """Test parsing a GPX file with multiple segments."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Multi Segment Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
      <trkpt lat="46.1" lon="4.1">
        <ele>200.0</ele>
        <time>2023-01-01T12:01:00Z</time>
      </trkpt>
    </trkseg>
    <trkseg>
      <trkpt lat="46.2" lon="4.2">
        <ele>150.0</ele>
        <time>2023-01-01T12:02:00Z</time>
      </trkpt>
      <trkpt lat="46.3" lon="4.3">
        <ele>250.0</ele>
        <time>2023-01-01T12:03:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            result = parse_gpx_file(file_path)

            assert result["name"] == "Multi Segment Track"
            assert len(result["points"]) == 4
            # Should calculate distance between all consecutive points across segments
            assert result["total_distance"] > 0
        finally:
            Path(file_path).unlink()

    def test_parse_gpx_file_coordinate_filtering(self):
        """Test that points with missing coordinates are filtered out."""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Coordinate Filtering Track</name>
    <trkseg>
      <trkpt lat="46.0" lon="4.0">
        <ele>100.0</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
      <trkpt lat="46.1" lon="4.1">
        <ele>200.0</ele>
        <time>2023-01-01T12:01:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

        file_path = self.create_test_gpx_file(gpx_content)
        try:
            result = parse_gpx_file(file_path)

            # Should include both valid points
            assert len(result["points"]) == 2
            assert result["points"][0]["lat"] == 46.0
            assert result["points"][1]["lat"] == 46.1
        finally:
            Path(file_path).unlink()
