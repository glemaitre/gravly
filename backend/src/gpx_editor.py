"""
GPX Editor Module

This module provides functionality to process GPX files, particularly for extracting
segments based on start and end indices, and saving processed GPX files.
"""

import os
from datetime import datetime
from typing import Any

import gpxpy


class GPXProcessingError(Exception):
    """Custom exception for GPX processing errors."""

    pass


def extract_gpx_segment(
    input_file_path: str,
    start_index: int,
    end_index: int,
    output_dir: str = "mock_gpx",
    custom_name: str | None = None,
) -> str:
    """
    Extract a segment from a GPX file between start and end indices and save it.

    Args:
        input_file_path: Path to the original GPX file
        start_index: Starting point index (inclusive)
        end_index: Ending point index (inclusive)
        output_dir: Directory where the processed file should be saved
        custom_name: Optional custom name for the segment

    Returns:
        Path to the processed GPX file

    Raises:
        GPXProcessingError: If processing fails
    """
    try:
        # Parse the original GPX file
        with open(input_file_path) as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        if not gpx.tracks:
            raise GPXProcessingError("No tracks found in GPX file")

        # Get the first track and segment
        original_track = gpx.tracks[0]
        if not original_track.segments:
            raise GPXProcessingError("No segments found in the first track")

        original_segment = original_track.segments[0]
        total_points = len(original_segment.points)

        # Validate indices
        if start_index < 0 or start_index >= total_points:
            raise GPXProcessingError(
                f"Start index {start_index} is out of range (0-{total_points - 1})"
            )

        if end_index < start_index or end_index >= total_points:
            raise GPXProcessingError(
                f"End index {end_index} is out of range ({start_index}-{total_points - 1})"
            )

        # Create new GPX object
        new_gpx = gpxpy.gpx.GPX()

        # Create a new track
        new_track = gpxpy.gpx.GPXTrack()

        # Set track name
        if custom_name:
            new_track.name = custom_name
        else:
            original_name = original_track.name or "Segment"
            new_track.name = f"{original_name} (points {start_index}-{end_index})"

        new_gpx.tracks.append(new_track)

        # Create a new segment
        new_segment = gpxpy.gpx.GPXTrackSegment()
        new_track.segments.append(new_segment)

        # Copy the selected points
        for i in range(start_index, end_index + 1):
            point = original_segment.points[i]
            # Create a new point to avoid reference issues
            new_point = gpxpy.gpx.GPXTrackPoint(
                latitude=point.latitude,
                longitude=point.longitude,
                elevation=point.elevation,
                time=point.time,
            )
            new_segment.points.append(new_point)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate output file path
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{base_name}_segment_{start_index}_{end_index}_{timestamp}.gpx"
        output_file_path = os.path.join(output_dir, output_filename)

        # Save the processed GPX file
        with open(output_file_path, "w") as output_file:
            output_file.write(new_gpx.to_xml())

        return output_file_path

    except Exception as e:
        raise GPXProcessingError(f"Failed to process GPX file: {str(e)}")


def get_gpx_statistics(file_path: str) -> dict[str, Any]:
    """
    Get basic statistics about a GPX file.

    Args:
        file_path: Path to the GPX file

    Returns:
        Dictionary containing statistics about the GPX file

    Raises:
        GPXProcessingError: If file cannot be processed
    """
    try:
        with open(file_path) as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        if not gpx.tracks or not gpx.tracks[0].segments:
            raise GPXProcessingError("No valid track segments found in GPX file")

        track = gpx.tracks[0]
        segment = track.segments[0]
        total_points = len(segment.points)

        # Extract coordinates and elevations
        lats = []
        lons = []
        elevations = []
        times = []

        for point in segment.points:
            if point.latitude is not None and point.longitude is not None:
                lats.append(point.latitude)
                lons.append(point.longitude)

            if point.elevation is not None:
                elevations.append(point.elevation)

            if point.time is not None:
                times.append(point.time)

        # Calculate bounds
        bounds = None
        if lats and lons:
            bounds = {"north": max(lats), "south": min(lats), "east": max(lons), "west": min(lons)}

        # Calculate elevation statistics
        elevation_stats = None
        if elevations:
            elevation_stats = {
                "min": min(elevations),
                "max": max(elevations),
                "total_points": len(elevations),
            }

        # Calculate time span
        time_span = None
        if len(times) >= 2:
            time_span = {
                "start": times[0].isoformat() if times[0] else None,
                "end": times[-1].isoformat() if times[-1] else None,
                "duration_seconds": (times[-1] - times[0]).total_seconds()
                if times[0] and times[-1]
                else None,
            }

        stats = {
            "track_name": track.name or "Unnamed Track",
            "total_points": total_points,
            "bounds": bounds,
            "elevation_stats": elevation_stats,
            "time_span": time_span,
            "has_elevation": len(elevations) > 0,
            "has_time": len(times) > 0,
        }

        return stats

    except Exception as e:
        raise GPXProcessingError(f"Failed to get GPX statistics: {str(e)}")


def validate_indices(file_path: str, start_index: int, end_index: int) -> tuple[bool, str]:
    """
    Validate that the given indices are valid for the GPX file.

    Args:
        file_path: Path to the GPX file
        start_index: Starting point index
        end_index: Ending point index

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path) as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        if not gpx.tracks or not gpx.tracks[0].segments:
            return False, "No valid track segments found in GPX file"

        total_points = len(gpx.tracks[0].segments[0].points)

        if start_index < 0:
            return False, f"Start index {start_index} cannot be negative"

        if start_index >= total_points:
            return False, f"Start index {start_index} is out of range (max: {total_points - 1})"

        if end_index < start_index:
            return False, f"End index {end_index} cannot be less than start index {start_index}"

        if end_index >= total_points:
            return False, f"End index {end_index} is out of range (max: {total_points - 1})"

        return True, ""

    except Exception as e:
        return False, f"Error validating indices: {str(e)}"


def process_gpx_for_segment_creation(
    input_file_path: str,
    start_index: int,
    end_index: int,
    segment_name: str,
    output_dir: str = "mock_gpx",
) -> dict[str, Any]:
    """
    Complete processing pipeline for creating a segment from a GPX file.

    Args:
        input_file_path: Path to the original GPX file
        start_index: Starting point index
        end_index: Ending point index
        segment_name: Name for the segment
        output_dir: Directory to save the processed file

    Returns:
        Dictionary containing processing results and metadata

    Raises:
        GPXProcessingError: If processing fails
    """
    # Validate indices first
    is_valid, error_msg = validate_indices(input_file_path, start_index, end_index)
    if not is_valid:
        raise GPXProcessingError(error_msg)

    # Get original file statistics
    original_stats = get_gpx_statistics(input_file_path)

    # Extract the segment
    processed_file_path = extract_gpx_segment(
        input_file_path, start_index, end_index, output_dir, segment_name
    )

    # Get processed file statistics
    processed_stats = get_gpx_statistics(processed_file_path)

    # Calculate segment statistics
    segment_length = end_index - start_index + 1
    original_length = original_stats["total_points"]
    percentage = (segment_length / original_length) * 100 if original_length > 0 else 0

    result = {
        "success": True,
        "original_file": input_file_path,
        "processed_file": processed_file_path,
        "segment_name": segment_name,
        "indices": {"start": start_index, "end": end_index, "length": segment_length},
        "original_stats": original_stats,
        "processed_stats": processed_stats,
        "extraction_info": {
            "percentage_of_original": round(percentage, 2),
            "points_extracted": segment_length,
            "points_original": original_length,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    return result


def split_gpx_at_index(file_path: str, split_index: int) -> tuple[str, str]:
    """
    Split a GPX file at a specific index, creating two separate files.

    Args:
        file_path: Path to the original GPX file
        split_index: Index at which to split the file

    Returns:
        Tuple of (first_part_path, second_part_path)

    Raises:
        GPXProcessingError: If processing fails
    """
    try:
        # Create first part (0 to split_index-1)
        first_part = extract_gpx_segment(
            file_path, 0, split_index - 1, custom_name=f"Part 1 (0-{split_index - 1})"
        )

        # Create second part (split_index to end)
        stats = get_gpx_statistics(file_path)
        second_part = extract_gpx_segment(
            file_path,
            split_index,
            stats["total_points"] - 1,
            custom_name=f"Part 2 ({split_index}-{stats['total_points'] - 1})",
        )

        return first_part, second_part

    except Exception as e:
        raise GPXProcessingError(f"Failed to split GPX file: {str(e)}")
