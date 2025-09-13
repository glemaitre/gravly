"""
GPX Editor Module

This module provides functionality for creating, editing, and manipulating GPX files
for cycling segments. It handles the core logic for the editor backend.
"""

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gpxpy
import gpxpy.gpx


@dataclass
class TrackPoint:
    """Represents a single track point with GPS coordinates and elevation."""

    latitude: float
    longitude: float
    elevation: float
    time: Optional[datetime] = None


@dataclass
class SegmentMetadata:
    """Metadata for a cycling segment."""

    name: str
    surface_type: str
    difficulty_level: int
    tire_dry: str
    tire_wet: str
    commentary_text: str
    video_links: List[Dict[str, str]]
    images: List[Dict[str, Any]]


class GPXEditor:
    """
    Main class for GPX file editing operations.

    This class provides methods to create, modify, and export GPX files
    with segment-specific metadata.
    """

    def __init__(self):
        """Initialize the GPX editor."""
        self.track_points: List[TrackPoint] = []
        self.metadata: Optional[SegmentMetadata] = None

    def load_track_points(self, points_data: List[Dict[str, Any]]) -> None:
        """
        Load track points from a list of dictionaries.

        Args:
            points_data: List of dictionaries containing lat, lon, ele, and optional time
        """
        # Dummy implementation - just store the data
        self.track_points = []
        for point in points_data:
            track_point = TrackPoint(
                latitude=point["lat"],
                longitude=point["lon"],
                elevation=point["ele"],
                time=datetime.fromisoformat(point["time"]) if point.get("time") else None,
            )
            self.track_points.append(track_point)

    def set_metadata(self, metadata: SegmentMetadata) -> None:
        """
        Set metadata for the segment.

        Args:
            metadata: SegmentMetadata object containing all segment information
        """
        # Dummy implementation - just store the metadata
        self.metadata = metadata

    def create_segment_gpx(self, start_index: int, end_index: int) -> str:
        """
        Create a GPX file for the selected segment.

        Args:
            start_index: Starting index of the segment
            end_index: Ending index of the segment

        Returns:
            GPX XML string
        """
        # Dummy implementation - create a simple GPX structure
        if not self.track_points:
            raise ValueError("No track points loaded")

        if start_index < 0 or end_index >= len(self.track_points):
            raise ValueError("Invalid segment indices")

        if start_index >= end_index:
            raise ValueError("Start index must be less than end index")

        segment_points = self.track_points[start_index : end_index + 1]

        # Create GPX structure
        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()
        track.name = self.metadata.name if self.metadata else "Unnamed Segment"

        segment = gpxpy.gpx.GPXTrackSegment()

        for point in segment_points:
            gpx_point = gpxpy.gpx.GPXTrackPoint(
                latitude=point.latitude,
                longitude=point.longitude,
                elevation=point.elevation,
                time=point.time,
            )
            segment.points.append(gpx_point)

        track.segments.append(segment)
        gpx.tracks.append(track)

        return gpx.to_xml()

    def calculate_segment_stats(self, start_index: int, end_index: int) -> Dict[str, float]:
        """
        Calculate statistics for the selected segment.

        Args:
            start_index: Starting index of the segment
            end_index: Ending index of the segment

        Returns:
            Dictionary containing distance, elevation gain, etc.
        """
        # Dummy implementation - return placeholder values
        segment_points = self.track_points[start_index : end_index + 1]

        if len(segment_points) < 2:
            return {"distance": 0.0, "elevation_gain": 0.0, "elevation_loss": 0.0, "duration": 0.0}

        # Calculate distance using Haversine formula
        total_distance = 0.0
        for i in range(1, len(segment_points)):
            p1 = segment_points[i - 1]
            p2 = segment_points[i]
            distance = self._haversine_distance(
                p1.latitude, p1.longitude, p2.latitude, p2.longitude
            )
            total_distance += distance

        # Calculate elevation changes
        elevation_gain = 0.0
        elevation_loss = 0.0
        for i in range(1, len(segment_points)):
            elevation_diff = segment_points[i].elevation - segment_points[i - 1].elevation
            if elevation_diff > 0:
                elevation_gain += elevation_diff
            else:
                elevation_loss += abs(elevation_diff)

        # Calculate duration if timestamps are available
        duration = 0.0
        if segment_points[0].time and segment_points[-1].time:
            duration = (segment_points[-1].time - segment_points[0].time).total_seconds()

        return {
            "distance": total_distance,
            "elevation_gain": elevation_gain,
            "elevation_loss": elevation_loss,
            "duration": duration,
        }

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Distance in kilometers
        """
        # Dummy implementation - simplified distance calculation
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def validate_segment(self, start_index: int, end_index: int) -> Tuple[bool, List[str]]:
        """
        Validate a segment for common issues.

        Args:
            start_index: Starting index of the segment
            end_index: Ending index of the segment

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        # Dummy implementation - basic validation
        issues = []

        if start_index < 0 or end_index >= len(self.track_points):
            issues.append("Invalid segment indices")

        if start_index >= end_index:
            issues.append("Start index must be less than end index")

        if end_index - start_index < 2:
            issues.append("Segment must have at least 2 points")

        # Check for duplicate points
        segment_points = self.track_points[start_index : end_index + 1]
        for i in range(1, len(segment_points)):
            p1 = segment_points[i - 1]
            p2 = segment_points[i]
            if (
                p1.latitude == p2.latitude
                and p1.longitude == p2.longitude
                and p1.elevation == p2.elevation
            ):
                issues.append(f"Duplicate points found at index {start_index + i}")

        return len(issues) == 0, issues

    def export_to_file(self, gpx_content: str, filename: str) -> bool:
        """
        Export GPX content to a file.

        Args:
            gpx_content: GPX XML string
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        # Dummy implementation - just return success
        try:
            # In a real implementation, this would write to file
            # with open(filename, 'w', encoding='utf-8') as f:
            #     f.write(gpx_content)
            return True
        except Exception:
            return False


def create_segment_from_editor_data(
    points_data: List[Dict[str, Any]], start_index: int, end_index: int, metadata: Dict[str, Any]
) -> str:
    """
    Convenience function to create a GPX segment from editor data.

    Args:
        points_data: List of track points from the editor
        start_index: Starting index of the segment
        end_index: Ending index of the segment
        metadata: Dictionary containing segment metadata

    Returns:
        GPX XML string
    """
    # Dummy implementation
    editor = GPXEditor()
    editor.load_track_points(points_data)

    # Convert metadata dict to SegmentMetadata object
    segment_metadata = SegmentMetadata(
        name=metadata.get("name", "Unnamed Segment"),
        surface_type=metadata.get("surface_type", "forest-trail"),
        difficulty_level=metadata.get("difficulty_level", 3),
        tire_dry=metadata.get("tire_dry", "slick"),
        tire_wet=metadata.get("tire_wet", "slick"),
        commentary_text=metadata.get("commentary_text", ""),
        video_links=metadata.get("video_links", []),
        images=metadata.get("images", []),
    )

    editor.set_metadata(segment_metadata)

    # Validate segment before creating
    is_valid, issues = editor.validate_segment(start_index, end_index)
    if not is_valid:
        raise ValueError(f"Invalid segment: {', '.join(issues)}")

    return editor.create_segment_gpx(start_index, end_index)
