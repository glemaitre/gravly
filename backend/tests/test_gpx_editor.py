"""
Tests for the GPX Editor module.

This module contains unit tests for the GPX editing functionality.
"""

from datetime import datetime

import pytest
from src.gpx_editor import GPXEditor, SegmentMetadata, TrackPoint, create_segment_from_editor_data


class TestTrackPoint:
    """Test cases for TrackPoint dataclass."""

    def test_track_point_creation(self):
        """Test creating a TrackPoint with basic data."""
        point = TrackPoint(latitude=45.0, longitude=-73.0, elevation=100.0)

        assert point.latitude == 45.0
        assert point.longitude == -73.0
        assert point.elevation == 100.0
        assert point.time is None

    def test_track_point_with_time(self):
        """Test creating a TrackPoint with timestamp."""
        time = datetime(2024, 1, 1, 12, 0, 0)
        point = TrackPoint(latitude=45.0, longitude=-73.0, elevation=100.0, time=time)

        assert point.time == time


class TestSegmentMetadata:
    """Test cases for SegmentMetadata dataclass."""

    def test_segment_metadata_creation(self):
        """Test creating SegmentMetadata with all fields."""
        metadata = SegmentMetadata(
            name="Test Segment",
            surface_type="forest-trail",
            difficulty_level=3,
            tire_dry="slick",
            tire_wet="semi-slick",
            commentary_text="A great trail",
            video_links=[{"url": "https://youtube.com/watch?v=123", "title": "Trail Video"}],
            images=[{"filename": "trail.jpg", "caption": "Trail view"}],
        )

        assert metadata.name == "Test Segment"
        assert metadata.surface_type == "forest-trail"
        assert metadata.difficulty_level == 3
        assert metadata.tire_dry == "slick"
        assert metadata.tire_wet == "semi-slick"
        assert metadata.commentary_text == "A great trail"
        assert len(metadata.video_links) == 1
        assert len(metadata.images) == 1


class TestGPXEditor:
    """Test cases for GPXEditor class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.editor = GPXEditor()

        # Sample track points data
        self.sample_points = [
            {"lat": 45.0, "lon": -73.0, "ele": 100.0, "time": "2024-01-01T12:00:00"},
            {"lat": 45.001, "lon": -73.001, "ele": 105.0, "time": "2024-01-01T12:01:00"},
            {"lat": 45.002, "lon": -73.002, "ele": 110.0, "time": "2024-01-01T12:02:00"},
            {"lat": 45.003, "lon": -73.003, "ele": 108.0, "time": "2024-01-01T12:03:00"},
        ]

        self.sample_metadata = SegmentMetadata(
            name="Test Trail",
            surface_type="forest-trail",
            difficulty_level=3,
            tire_dry="slick",
            tire_wet="semi-slick",
            commentary_text="A beautiful forest trail",
            video_links=[],
            images=[],
        )

    def test_load_track_points(self):
        """Test loading track points from data."""
        self.editor.load_track_points(self.sample_points)

        assert len(self.editor.track_points) == 4
        assert self.editor.track_points[0].latitude == 45.0
        assert self.editor.track_points[0].longitude == -73.0
        assert self.editor.track_points[0].elevation == 100.0
        assert self.editor.track_points[0].time is not None

    def test_set_metadata(self):
        """Test setting segment metadata."""
        self.editor.set_metadata(self.sample_metadata)

        assert self.editor.metadata is not None
        assert self.editor.metadata.name == "Test Trail"
        assert self.editor.metadata.surface_type == "forest-trail"

    def test_create_segment_gpx(self):
        """Test creating a GPX segment."""
        self.editor.load_track_points(self.sample_points)
        self.editor.set_metadata(self.sample_metadata)

        gpx_content = self.editor.create_segment_gpx(0, 2)

        assert isinstance(gpx_content, str)
        assert "<?xml" in gpx_content
        assert "Test Trail" in gpx_content
        assert "trkpt" in gpx_content

    def test_create_segment_gpx_invalid_indices(self):
        """Test creating GPX with invalid indices."""
        self.editor.load_track_points(self.sample_points)

        with pytest.raises(ValueError, match="Start index must be less than end index"):
            self.editor.create_segment_gpx(2, 1)

        with pytest.raises(ValueError, match="Invalid segment indices"):
            self.editor.create_segment_gpx(0, 10)

    def test_calculate_segment_stats(self):
        """Test calculating segment statistics."""
        self.editor.load_track_points(self.sample_points)

        stats = self.editor.calculate_segment_stats(0, 2)

        assert isinstance(stats, dict)
        assert "distance" in stats
        assert "elevation_gain" in stats
        assert "elevation_loss" in stats
        assert "duration" in stats

        # Distance should be positive
        assert stats["distance"] > 0
        # Elevation gain should be positive (100 -> 105 -> 110)
        assert stats["elevation_gain"] > 0

    def test_calculate_segment_stats_single_point(self):
        """Test calculating stats for a single point segment."""
        self.editor.load_track_points(self.sample_points)

        stats = self.editor.calculate_segment_stats(0, 0)

        assert stats["distance"] == 0.0
        assert stats["elevation_gain"] == 0.0
        assert stats["elevation_loss"] == 0.0
        assert stats["duration"] == 0.0

    def test_validate_segment_valid(self):
        """Test validating a valid segment."""
        self.editor.load_track_points(self.sample_points)

        is_valid, issues = self.editor.validate_segment(0, 2)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_segment_invalid_indices(self):
        """Test validating segment with invalid indices."""
        self.editor.load_track_points(self.sample_points)

        is_valid, issues = self.editor.validate_segment(2, 1)
        assert is_valid is False
        assert "Start index must be less than end index" in issues

        is_valid, issues = self.editor.validate_segment(0, 10)
        assert is_valid is False
        assert "Invalid segment indices" in issues

    def test_validate_segment_too_short(self):
        """Test validating a segment that's too short."""
        self.editor.load_track_points(self.sample_points)

        is_valid, issues = self.editor.validate_segment(0, 0)
        assert is_valid is False
        assert "Segment must have at least 2 points" in issues

    def test_validate_segment_duplicate_points(self):
        """Test validating segment with duplicate points."""
        duplicate_points = [
            {"lat": 45.0, "lon": -73.0, "ele": 100.0},
            {"lat": 45.0, "lon": -73.0, "ele": 100.0},  # Duplicate
            {"lat": 45.001, "lon": -73.001, "ele": 105.0},
        ]
        self.editor.load_track_points(duplicate_points)

        is_valid, issues = self.editor.validate_segment(0, 2)
        assert is_valid is False
        assert any("Duplicate points found" in issue for issue in issues)

    def test_haversine_distance(self):
        """Test Haversine distance calculation."""
        # Test distance between two known points
        distance = self.editor._haversine_distance(45.0, -73.0, 45.001, -73.001)

        assert isinstance(distance, float)
        assert distance > 0
        # Should be approximately 0.157 km (rough estimate)
        assert 0.1 < distance < 0.2

    def test_export_to_file(self):
        """Test exporting GPX to file."""
        gpx_content = "<?xml version='1.0'?><gpx></gpx>"

        result = self.editor.export_to_file(gpx_content, "test.gpx")

        # Dummy implementation should return True
        assert result is True


class TestCreateSegmentFromEditorData:
    """Test cases for the convenience function."""

    def test_create_segment_from_editor_data(self):
        """Test creating segment using the convenience function."""
        points_data = [
            {"lat": 45.0, "lon": -73.0, "ele": 100.0, "time": "2024-01-01T12:00:00"},
            {"lat": 45.001, "lon": -73.001, "ele": 105.0, "time": "2024-01-01T12:01:00"},
            {"lat": 45.002, "lon": -73.002, "ele": 110.0, "time": "2024-01-01T12:02:00"},
        ]

        metadata = {
            "name": "Test Segment",
            "surface_type": "forest-trail",
            "difficulty_level": 3,
            "tire_dry": "slick",
            "tire_wet": "semi-slick",
            "commentary_text": "Great trail",
            "video_links": [],
            "images": [],
        }

        gpx_content = create_segment_from_editor_data(points_data, 0, 2, metadata)

        assert isinstance(gpx_content, str)
        assert "<?xml" in gpx_content
        assert "Test Segment" in gpx_content

    def test_create_segment_invalid_data(self):
        """Test creating segment with invalid data."""
        points_data = [{"lat": 45.0, "lon": -73.0, "ele": 100.0}]
        metadata = {"name": "Test"}

        with pytest.raises(ValueError, match="Invalid segment"):
            create_segment_from_editor_data(points_data, 0, 0, metadata)


# Integration tests
class TestGPXEditorIntegration:
    """Integration tests for the GPX Editor."""

    def test_full_workflow(self):
        """Test the complete workflow from loading data to creating GPX."""
        editor = GPXEditor()

        # Load track points
        points_data = [
            {"lat": 45.0, "lon": -73.0, "ele": 100.0, "time": "2024-01-01T12:00:00"},
            {"lat": 45.001, "lon": -73.001, "ele": 105.0, "time": "2024-01-01T12:01:00"},
            {"lat": 45.002, "lon": -73.002, "ele": 110.0, "time": "2024-01-01T12:02:00"},
            {"lat": 45.003, "lon": -73.003, "ele": 108.0, "time": "2024-01-01T12:03:00"},
        ]
        editor.load_track_points(points_data)

        # Set metadata
        metadata = SegmentMetadata(
            name="Integration Test Trail",
            surface_type="forest-trail",
            difficulty_level=4,
            tire_dry="knobs",
            tire_wet="semi-slick",
            commentary_text="A challenging forest trail",
            video_links=[{"url": "https://youtube.com/watch?v=123", "title": "Trail Video"}],
            images=[{"filename": "trail.jpg", "caption": "Beautiful view"}],
        )
        editor.set_metadata(metadata)

        # Validate segment
        is_valid, issues = editor.validate_segment(0, 3)
        assert is_valid is True
        assert len(issues) == 0

        # Calculate stats
        stats = editor.calculate_segment_stats(0, 3)
        assert stats["distance"] > 0
        assert stats["elevation_gain"] > 0

        # Create GPX
        gpx_content = editor.create_segment_gpx(0, 3)
        assert "Integration Test Trail" in gpx_content
        # Note: surface_type is not included in the GPX output, only the track name

        # Export to file
        result = editor.export_to_file(gpx_content, "integration_test.gpx")
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])
