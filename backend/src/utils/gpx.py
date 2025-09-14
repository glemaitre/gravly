"""
GPX Editor Module

This module provides functionality to process GPX files, particularly for extracting
segments based on start and end indices, and saving processed GPX files.
"""

import math
import uuid
from pathlib import Path

import gpxpy
from pydantic import BaseModel

from .math import haversine_distance


class GPXProcessingError(Exception):
    """Custom exception for GPX processing errors."""

    pass


class GPXPoint(BaseModel):
    latitude: float
    longitude: float
    elevation: float
    time: str


class GPXTotalStats(BaseModel):
    total_points: int
    total_distance: float
    total_elevation_gain: float
    total_elevation_loss: float


class GPXBounds(BaseModel):
    north: float
    south: float
    east: float
    west: float


class GPXElevationStats(BaseModel):
    min: float
    max: float


class GPXData(BaseModel):
    file_id: str
    track_name: str
    points: list[GPXPoint]
    total_stats: GPXTotalStats
    bounds: GPXBounds
    elevation_stats: GPXElevationStats


def extract_from_gpx_file(gpx: gpxpy.gpx.GPX, file_id: str) -> GPXData:
    """Extract comprehensive track information from a parsed GPX object.

    Parameters
    ----------
    gpx : gpxpy.gpx.GPX
        The parsed GPX object.
    file_id: str
        The ID of the file.

    Returns
    -------
    GPXData
        GPXData object containing parsed GPX data with the following attributes:

        - file_id (str): The ID of the file
        - track_name (str): Track name or "Unnamed Track" if not specified
        - points (list[GPXPoint]): List of track points, each containing:
            - latitude (float): Latitude in decimal degrees
            - longitude (float): Longitude in decimal degrees
            - elevation (float): Elevation in meters
            - time (str): ISO format timestamp
        - total_stats (GPXTotalStats): Statistics including:
            - total_distance (float): Total distance in kilometers
            - total_elevation_gain (float): Total elevation gain in meters
            - total_elevation_loss (float): Total elevation loss in meters
            - total_points (int): Number of points
        - bounds (GPXBounds): Geographic bounds with:
            - north (float): Northernmost latitude
            - south (float): Southernmost latitude
            - east (float): Easternmost longitude
            - west (float): Westernmost longitude
        - elevation_stats (GPXElevationStats): Elevation statistics with:
            - min (float): Minimum elevation in meters
            - max (float): Maximum elevation in meters

    Examples
    --------
    >>> import gpxpy
    >>> with open("track.gpx", "r") as gpx_file:
    ...     gpx = gpxpy.parse(gpx_file)
    >>> result = extract_from_gpx_file(gpx, "track_001")
    >>> print(f"Track: {result.track_name}")
    >>> print(f"Distance: {result.total_stats.total_distance:.2f} km")
    >>> print(f"Points: {result.total_stats.total_points}")
    """
    track = gpx.tracks[0]

    points: list[GPXPoint] = []
    total_distance, total_elevation_gain, total_elevation_loss = 0.0, 0.0, 0.0
    min_latitude, min_longitude, min_elevation = math.inf, math.inf, math.inf
    max_latitude, max_longitude, max_elevation = -math.inf, -math.inf, -math.inf

    for segment in track.segments:
        for point_index, point in enumerate(segment.points):
            elevation = point.elevation

            min_latitude = min(min_latitude, point.latitude)
            max_latitude = max(max_latitude, point.latitude)
            min_longitude = min(min_longitude, point.longitude)
            max_longitude = max(max_longitude, point.longitude)
            min_elevation = min(min_elevation, elevation)
            max_elevation = max(max_elevation, elevation)

            if point_index > 0:
                previous_point = points[-1]
                distance = haversine_distance(
                    latitude_1=previous_point.latitude,
                    longitude_1=previous_point.longitude,
                    latitude_2=point.latitude,
                    longitude_2=point.longitude,
                )
                total_distance += distance

                elevation_diff = elevation - previous_point.elevation
                if elevation_diff > 0:
                    total_elevation_gain += elevation_diff
                else:
                    total_elevation_loss += abs(elevation_diff)

            points.append(
                GPXPoint(
                    latitude=point.latitude,
                    longitude=point.longitude,
                    elevation=elevation,
                    time=point.time.isoformat(),
                )
            )

    bounds = GPXBounds(
        north=max_latitude,
        south=min_latitude,
        east=max_longitude,
        west=min_longitude,
    )

    elevation_stats = GPXElevationStats(
        min=min_elevation,
        max=max_elevation,
    )

    total_stats = GPXTotalStats(
        total_points=len(points),
        total_distance=total_distance,
        total_elevation_gain=total_elevation_gain,
        total_elevation_loss=total_elevation_loss,
    )

    return GPXData(
        file_id=file_id,
        track_name=track.name or "Unnamed Track",
        points=points,
        total_stats=total_stats,
        bounds=bounds,
        elevation_stats=elevation_stats,
    )


def generate_gpx_segment(
    input_file_path: Path,
    start_index: int,
    end_index: int,
    segment_name: str,
    output_dir: Path,
) -> str:
    """Generate a GPX segment from a given GPX file.

    Parameters
    ----------
    input_file_path: Path
        The path to the input GPX file.
    start_index: int
        The start index of the segment.
    end_index: int
        The end index of the segment.
    segment_name: str
        The name of the segment.
    output_dir: Path
        The path to the output directory.

    Returns
    -------
    file_id: str
        The ID of the generated GPX segment.
    """
    file_id = str(uuid.uuid4())
    new_gpx = gpxpy.gpx.GPX()
    new_track = gpxpy.gpx.GPXTrack(name=segment_name)
    new_gpx.tracks.append(new_track)
    new_segment = gpxpy.gpx.GPXTrackSegment()
    new_track.segments.append(new_segment)

    with open(input_file_path) as gpx_file:
        original_gpx = gpxpy.parse(gpx_file)

    for point_idx, point in enumerate(original_gpx.tracks[0].segments[0].points):
        if point_idx >= start_index and point_idx <= end_index:
            new_point = gpxpy.gpx.GPXTrackPoint(
                latitude=point.latitude,
                longitude=point.longitude,
                elevation=point.elevation,
                time=point.time,
            )
            new_segment.points.append(new_point)

    with open(output_dir / f"{file_id}.gpx", "w") as gpx_file:
        gpx_file.write(new_gpx.to_xml())

    return file_id
