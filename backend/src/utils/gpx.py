"""
GPX Editor Module

This module provides functionality to process GPX files, particularly for extracting
segments based on start and end indices, and saving processed GPX files.
"""

import datetime
import math
import uuid
from pathlib import Path

import gpxpy
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.course_message import CourseMessage
from fit_tool.profile.messages.course_point_message import CoursePointMessage
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.profile_type import (
    CoursePoint,
    Event,
    EventType,
    FileType,
    Manufacturer,
    Sport,
)
from pydantic import BaseModel

from .math import haversine_distance


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
    min_elevation: float
    max_elevation: float


class GPXData(BaseModel):
    file_id: str
    track_name: str
    points: list[GPXPoint]
    total_stats: GPXTotalStats
    bounds: GPXBounds


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
        - bounds (GPXBounds): Geographic and elevation bounds with:
            - north (float): Northernmost latitude
            - south (float): Southernmost latitude
            - east (float): Easternmost longitude
            - west (float): Westernmost longitude
            - min_elevation (float): Minimum elevation in meters
            - max_elevation (float): Maximum elevation in meters

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
        min_elevation=min_elevation,
        max_elevation=max_elevation,
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
    )


def generate_gpx_segment(
    input_file_path: Path,
    start_index: int,
    end_index: int,
    segment_name: str,
    output_dir: Path,
) -> tuple[str, Path, GPXBounds]:
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
    tuple[str, Path, GPXBounds]
        A tuple containing:
        - file_id: The ID of the generated GPX segment.
        - output_file_path: The full path to the generated GPX file.
        - bounds: A `GPXBounds` object containing the minimum and maximum latitude
          and longitude.
    """
    file_id = str(uuid.uuid4())
    new_gpx = gpxpy.gpx.GPX()
    new_track = gpxpy.gpx.GPXTrack(name=segment_name)
    new_gpx.tracks.append(new_track)
    new_segment = gpxpy.gpx.GPXTrackSegment()
    new_track.segments.append(new_segment)

    with open(input_file_path) as gpx_file:
        original_gpx = gpxpy.parse(gpx_file)

    min_latitude, min_longitude, min_elevation = math.inf, math.inf, math.inf
    max_latitude, max_longitude, max_elevation = -math.inf, -math.inf, -math.inf
    for point_idx, point in enumerate(original_gpx.tracks[0].segments[0].points):
        if point_idx >= start_index and point_idx <= end_index:
            latitude, longitude = point.latitude, point.longitude
            new_point = gpxpy.gpx.GPXTrackPoint(
                latitude=latitude,
                longitude=longitude,
                elevation=point.elevation,
                time=point.time,
            )
            min_latitude = min(min_latitude, latitude)
            max_latitude = max(max_latitude, latitude)
            min_longitude = min(min_longitude, longitude)
            max_longitude = max(max_longitude, longitude)
            min_elevation = min(min_elevation, point.elevation)
            max_elevation = max(max_elevation, point.elevation)
            new_segment.points.append(new_point)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_path = output_dir / f"{file_id}.gpx"
    with open(output_file_path, "w") as gpx_file:
        gpx_file.write(new_gpx.to_xml())

    return (
        file_id,
        output_file_path,
        GPXBounds(
            north=max_latitude,
            south=min_latitude,
            east=max_longitude,
            west=min_longitude,
            min_elevation=min_elevation,
            max_elevation=max_elevation,
        ),
    )


def convert_gpx_to_fit(gpx: gpxpy.gpx.GPX, course_name: str = "GPX Course") -> bytes:
    """Convert a GPX object to a FIT file in bytes format.

    Parameters
    ----------
    gpx : gpxpy.gpx.GPX
        The parsed GPX object containing track data.
    course_name : str, optional
        The name for the course in the FIT file, by default "GPX Course".

    Returns
    -------
    bytes
        The FIT file as bytes that can be written to a file or used directly.

    Examples
    --------
    >>> import gpxpy
    >>> with open("track.gpx", "r") as gpx_file:
    ...     gpx = gpxpy.parse(gpx_file)
    >>> fit_bytes = convert_gpx_to_fit(gpx, "My Cycling Course")
    >>> with open("course.fit", "wb") as fit_file:
    ...     fit_file.write(fit_bytes)
    """
    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    # File ID message - required for all FIT files
    message = FileIdMessage()
    message.type = FileType.COURSE
    message.manufacturer = Manufacturer.DEVELOPMENT.value
    message.product = 0
    message.timeCreated = round(datetime.datetime.now().timestamp() * 1000)
    message.serialNumber = 0x12345678
    builder.add(message)

    # Course message - required for FIT course files
    message = CourseMessage()
    message.courseName = course_name
    message.sport = Sport.CYCLING
    builder.add(message)

    # Timer start event - required for FIT course files
    # FIT timestamps are in milliseconds from January 1st, 1970 at 00:00:00 UTC
    # We need to convert our timestamp to milliseconds
    import time

    start_timestamp = int(time.time() * 1000)  # Convert to milliseconds
    message = EventMessage()
    message.event = Event.TIMER
    message.event_type = EventType.START
    message.timestamp = start_timestamp
    builder.add(message)

    # Process track points
    distance = 0.0
    timestamp = start_timestamp
    course_records = []
    prev_coordinate = None

    # Get the first track and segment
    if not gpx.tracks or not gpx.tracks[0].segments:
        raise ValueError("GPX file must contain at least one track with segments")

    track = gpx.tracks[0]
    segment = track.segments[0]

    for track_point in segment.points:
        current_coordinate = (track_point.latitude, track_point.longitude)

        # Calculate distance from previous coordinate and accumulate distance
        if prev_coordinate:
            delta = (
                haversine_distance(
                    latitude_1=prev_coordinate[0],
                    longitude_1=prev_coordinate[1],
                    latitude_2=current_coordinate[0],
                    longitude_2=current_coordinate[1],
                )
                * 1000
            )  # convert from kilometers to meters
        else:
            delta = 0.0
        distance += delta

        # Create record message for this point
        message = RecordMessage()
        message.position_lat = track_point.latitude
        message.position_long = track_point.longitude
        message.altitude = track_point.elevation
        message.distance = distance
        message.timestamp = timestamp
        course_records.append(message)

        # Increment timestamp by 1 millisecond per point
        timestamp += 1
        prev_coordinate = current_coordinate

    if not course_records:
        raise ValueError("No track points found in GPX file")

    # Add all course records
    builder.add_all(course_records)

    # Add start course point
    message = CoursePointMessage()
    message.timestamp = course_records[0].timestamp
    message.position_lat = course_records[0].position_lat
    message.position_long = course_records[0].position_long
    message.type = CoursePoint.SEGMENT_START
    message.course_point_name = "start"
    builder.add(message)

    # Add end course point
    message = CoursePointMessage()
    message.timestamp = course_records[-1].timestamp
    message.position_lat = course_records[-1].position_lat
    message.position_long = course_records[-1].position_long
    message.type = CoursePoint.SEGMENT_END
    message.course_point_name = "end"
    builder.add(message)

    # Stop event
    message = EventMessage()
    message.event = Event.TIMER
    message.eventType = EventType.STOP_ALL
    message.timestamp = timestamp
    builder.add(message)

    # Lap message - required for FIT course files
    elapsed_time = timestamp - start_timestamp
    # Cap elapsed time to prevent overflow (max 32-bit unsigned int is 4294967295)
    if elapsed_time > 4294967295:
        elapsed_time = 4294967295
    message = LapMessage()
    message.timestamp = timestamp
    message.start_time = start_timestamp
    message.total_elapsed_time = elapsed_time
    message.total_timer_time = elapsed_time
    message.start_position_lat = course_records[0].position_lat
    message.start_position_long = course_records[0].position_long
    message.end_position_lat = course_records[-1].position_lat
    message.endPositionLong = course_records[-1].position_long
    message.total_distance = course_records[-1].distance
    builder.add(message)

    # Build the FIT file and return as bytes
    fit_file = builder.build()
    return fit_file.to_bytes()
