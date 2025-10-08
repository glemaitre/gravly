"""Routes API endpoints."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import gpxpy
from fastapi import APIRouter, HTTPException, Request
from gpxpy.gpx import GPXTrack, GPXTrackPoint, GPXTrackSegment
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .. import dependencies
from ..dependencies import storage_manager as global_storage_manager
from ..models.track import (
    SurfaceType,
    TireType,
    Track,
    TrackResponse,
    TrackType,
)

logger = logging.getLogger(__name__)


def create_routes_router(
    session_local: async_sessionmaker[AsyncSession] | None,
) -> APIRouter:
    """Create the routes router with all endpoints.

    Parameters
    ----------
    session_local : Optional[async_sessionmaker[AsyncSession]]
        Database session factory, can be None for testing

    Returns
    -------
    APIRouter
        Configured FastAPI router with route endpoints
    """
    router = APIRouter(prefix="/api/routes", tags=["routes"])

    @router.post("/", response_model=TrackResponse)
    async def create_route(request: Request):
        """Create a new route from selected segments.

        This endpoint takes a list of segment IDs and creates a route
        with computed statistics based on the segments.
        """
        if not dependencies.SessionLocal:
            raise HTTPException(status_code=500, detail="Database not configured")

        try:
            # Parse request body
            body = await request.json()

            # Validate required fields
            name = body.get("name")
            if not name or not name.strip():
                raise HTTPException(status_code=422, detail="Route name is required")

            segments_data = body.get("segments", [])
            computed_stats = body.get("computed_stats", {})
            actual_route_coordinates = body.get("actual_route_coordinates", [])
            interpolated_elevation_data = body.get("interpolated_elevation_data", [])
            comments = body.get("comments", "").strip()

            # Create database session
            async with dependencies.SessionLocal() as session:
                # Handle two types of routes: segment-based and waypoint-based
                if segments_data:
                    # Segment-based route: fetch segments and calculate statistics
                    segment_ids = [seg["id"] for seg in segments_data]
                    segments_query = select(Track).where(
                        and_(
                            Track.id.in_(segment_ids),
                            Track.track_type == TrackType.SEGMENT,
                        )
                    )
                    segments_result = await session.execute(segments_query)
                    segments = segments_result.scalars().all()

                    if len(segments) != len(segment_ids):
                        raise HTTPException(
                            status_code=422, detail="One or more segments not found"
                        )

                    # Create a mapping of segment data for order preservation
                    segment_map = {seg.id: seg for seg in segments}
                    ordered_segments = []
                    for seg_data in segments_data:
                        segment_id = seg_data["id"]
                        if segment_id in segment_map:
                            segment = segment_map[segment_id]
                            segment.isReversed = seg_data.get("isReversed", False)
                            ordered_segments.append(segment)

                    # Calculate route statistics from segments
                    # (difficulty, surface types, tires)
                    route_stats = calculate_route_statistics(ordered_segments)
                else:
                    # Waypoint-based route: use default values
                    route_stats = calculate_waypoint_route_statistics()

                if not global_storage_manager:
                    raise HTTPException(
                        status_code=500, detail="Storage manager not available"
                    )

                # Create GPX file for the route and calculate bounds
                if segments_data:
                    route_gpx_data, bounds = await create_route_gpx(ordered_segments)
                else:
                    route_gpx_data, bounds = await create_waypoint_route_gpx(
                        computed_stats,
                        actual_route_coordinates,
                        interpolated_elevation_data,
                    )

                # Generate a unique file path for the route
                route_file_id = str(uuid.uuid4())

                # Create temporary file for GPX data
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".gpx", delete=False
                ) as temp_file:
                    temp_file.write(route_gpx_data)
                    temp_file_path = Path(temp_file.name)

                try:
                    # Upload GPX file to storage
                    storage_key = global_storage_manager.upload_gpx_segment(
                        temp_file_path, route_file_id, prefix="routes"
                    )

                    # Create proper storage URL
                    route_file_path = (
                        f"{global_storage_manager.get_storage_root_prefix()}/"
                        f"{storage_key}"
                    )

                    # Clean up temporary file
                    temp_file_path.unlink()

                except Exception as e:
                    # Clean up temporary file on error
                    if temp_file_path.exists():
                        temp_file_path.unlink()
                    raise HTTPException(
                        status_code=500, detail=f"Failed to save route GPX: {str(e)}"
                    )

                # Create the route track
                route_track = Track(
                    file_path=route_file_path,
                    bound_north=bounds["north"],
                    bound_south=bounds["south"],
                    bound_east=bounds["east"],
                    bound_west=bounds["west"],
                    barycenter_latitude=bounds["barycenter_lat"],
                    barycenter_longitude=bounds["barycenter_lng"],
                    name=name.strip(),
                    track_type=TrackType.ROUTE,
                    difficulty_level=route_stats["difficulty_level"],
                    surface_type=route_stats["surface_types"],
                    tire_dry=route_stats["tire_dry"],
                    tire_wet=route_stats["tire_wet"],
                    comments=comments,
                )

                session.add(route_track)
                await session.commit()
                await session.refresh(route_track)

                logger.info(f"Created route '{name}' with ID {route_track.id}")

                # Return the created route
                return TrackResponse(
                    id=route_track.id,
                    file_path=route_track.file_path,
                    bound_north=route_track.bound_north,
                    bound_south=route_track.bound_south,
                    bound_east=route_track.bound_east,
                    bound_west=route_track.bound_west,
                    barycenter_latitude=route_track.barycenter_latitude,
                    barycenter_longitude=route_track.barycenter_longitude,
                    name=route_track.name,
                    track_type=route_track.track_type.value,
                    difficulty_level=route_track.difficulty_level,
                    surface_type=route_track.surface_type,
                    tire_dry=route_track.tire_dry.value,
                    tire_wet=route_track.tire_wet.value,
                    comments=route_track.comments,
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create route: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create route: {str(e)}"
            )

    return router


def calculate_waypoint_route_statistics():
    """Calculate route statistics for waypoint-based routes.

    For waypoint-based routes, we use default values since there are no segments
    to derive terrain characteristics from.

    Returns
    -------
    dict
        Route statistics with default values for difficulty, surface types,
        and tire recommendations
    """
    # Use default values for segment-specific statistics
    default_difficulty = 2  # Medium difficulty
    default_surface_types = [
        SurfaceType.BROKEN_PAVED_ROAD.value
    ]  # Default to paved road
    default_tire_dry = TireType.SEMI_SLICK  # Conservative recommendation
    default_tire_wet = TireType.KNOBS  # Safe for wet conditions

    return {
        "difficulty_level": default_difficulty,
        "surface_types": default_surface_types,
        "tire_dry": default_tire_dry,
        "tire_wet": default_tire_wet,
    }


def calculate_route_statistics(segments):
    """Calculate route statistics from segments.

    This function computes difficulty level, surface types, and tire recommendations
    based on the segments in the route.

    Parameters
    ----------
    segments : list
        List of segment Track objects

    Returns
    -------
    dict
        Calculated route statistics with difficulty, surface types,
        and tire recommendations
    """
    if not segments:
        raise HTTPException(status_code=422, detail="No segments provided")

    # Calculate average difficulty
    total_difficulty = sum(segment.difficulty_level for segment in segments)
    avg_difficulty = round(total_difficulty / len(segments), 1)

    # Union of all surface types
    all_surface_types = set()
    for segment in segments:
        all_surface_types.update(segment.surface_type)
    surface_types = list(all_surface_types)

    # Tire recommendation logic: separate dry and wet conditions
    # Order: slick < semi-slick < knobs (from best to worst)
    dry_tire_types = set()
    wet_tire_types = set()

    for segment in segments:
        dry_tire_types.add(segment.tire_dry.value)
        wet_tire_types.add(segment.tire_wet.value)

    # Calculate dry tire recommendation (worst case scenario)
    if "knobs" in dry_tire_types:
        tire_dry_recommendation = TireType.KNOBS
    elif "semi-slick" in dry_tire_types:
        tire_dry_recommendation = TireType.SEMI_SLICK
    else:
        tire_dry_recommendation = TireType.SLICK

    # Calculate wet tire recommendation (worst case scenario)
    if "knobs" in wet_tire_types:
        tire_wet_recommendation = TireType.KNOBS
    elif "semi-slick" in wet_tire_types:
        tire_wet_recommendation = TireType.SEMI_SLICK
    else:
        tire_wet_recommendation = TireType.SLICK

    return {
        "difficulty_level": int(avg_difficulty),
        "surface_types": surface_types,
        "tire_dry": tire_dry_recommendation,
        "tire_wet": tire_wet_recommendation,
    }


async def create_route_gpx(segments):
    """Create GPX data for the route by combining segment GPX data.

    This function also calculates bounding box and total statistics efficiently
    by processing the GPX points.

    Parameters
    ----------
    segments : list
        List of segment Track objects

    Returns
    -------
    tuple
        A tuple containing:
        - str: GPX XML content for the route
        - dict: Bounding box with north, south, east, west,
                barycenter_lat, barycenter_lng
    """

    if not global_storage_manager:
        raise HTTPException(status_code=500, detail="Storage manager not available")

    # Create a new GPX object
    gpx = gpxpy.gpx.GPX()
    gpx.creator = "Gravly Route Planner"

    # Create a track
    gpx_track = GPXTrack()
    gpx_track.name = f"Route with {len(segments)} segments"
    gpx_track.description = "Route created from segments in guided mode"

    # Initialize bounds tracking
    min_lat, max_lat = None, None
    min_lng, max_lng = None, None
    all_lats, all_lngs = [], []

    # For each segment, load its GPX data and add the track points
    for segment in segments:
        try:
            # Load the segment's GPX file from storage
            gpx_file_path = global_storage_manager.get_file_path(segment.file_path)

            # Parse the GPX file
            with open(gpx_file_path) as gpx_file:
                segment_gpx = gpxpy.parse(gpx_file)

            # Extract track points from the segment
            # Check if we need to reverse the segment
            is_reversed = getattr(segment, "isReversed", False)

            for track in segment_gpx.tracks:
                for track_segment in track.segments:
                    # Create a new track segment for this part of the route
                    gpx_segment = GPXTrackSegment()

                    # Get the points, potentially reversed
                    points = list(track_segment.points)
                    if is_reversed:
                        points = list(reversed(points))

                    # Add all points to the segment and track bounds
                    for point in points:
                        gpx_point = GPXTrackPoint(
                            latitude=point.latitude,
                            longitude=point.longitude,
                            elevation=point.elevation,
                            time=point.time,
                        )
                        gpx_segment.points.append(gpx_point)

                        # Track bounds
                        all_lats.append(point.latitude)
                        all_lngs.append(point.longitude)

                        if min_lat is None or point.latitude < min_lat:
                            min_lat = point.latitude
                        if max_lat is None or point.latitude > max_lat:
                            max_lat = point.latitude
                        if min_lng is None or point.longitude < min_lng:
                            min_lng = point.longitude
                        if max_lng is None or point.longitude > max_lng:
                            max_lng = point.longitude

                    # Add the segment to the track
                    gpx_track.segments.append(gpx_segment)

        except Exception as e:
            logger.warning(f"Error loading GPX for segment {segment.id}: {str(e)}")
            # Continue with other segments even if one fails
            continue

    # Add the track to the GPX
    gpx.tracks.append(gpx_track)

    # Calculate bounds
    if min_lat is None or max_lat is None or min_lng is None or max_lng is None:
        raise HTTPException(
            status_code=422, detail="Unable to calculate bounds from route data"
        )

    if all_lats:
        barycenter_lat = sum(all_lats) / len(all_lats)
        barycenter_lng = sum(all_lngs) / len(all_lngs)
    else:
        barycenter_lat = (min_lat + max_lat) / 2
        barycenter_lng = (min_lng + max_lng) / 2

    bounds = {
        "north": max_lat,
        "south": min_lat,
        "east": max_lng,
        "west": min_lng,
        "barycenter_lat": barycenter_lat,
        "barycenter_lng": barycenter_lng,
    }

    # Convert to XML string and return with bounds
    return gpx.to_xml(), bounds


async def create_waypoint_route_gpx(
    computed_stats, actual_route_coordinates, interpolated_elevation_data
):
    """Create GPX data for waypoint-based routes using actual route coordinates.

    This function also calculates bounding box by processing the GPX points.

    Parameters
    ----------
    computed_stats : dict
        Pre-computed statistics from frontend
    actual_route_coordinates : list
        List of actual route coordinates from the RoutePlanner
    interpolated_elevation_data : list
        List of interpolated elevation data with lat, lng, elevation, distance

    Returns
    -------
    tuple
        A tuple containing:
        - str: GPX XML content for the waypoint route
        - dict: Bounding box with north, south, east, west,
                barycenter_lat, barycenter_lng
    """

    # Extract route information from computed stats
    distance = computed_stats.get("distance", 0)
    elevation_gain = computed_stats.get("elevationGain", 0)

    # Create a new GPX object
    gpx = gpxpy.gpx.GPX()
    gpx.creator = "Gravly Route Planner"

    # Create a track
    gpx_track = GPXTrack()
    gpx_track.name = "Waypoint Route"
    gpx_track.description = (
        f"Route created from waypoints - Distance: {distance:.2f}km, "
        f"Elevation: {elevation_gain:.0f}m"
    )

    # Create a track segment
    gpx_segment = GPXTrackSegment()

    # Initialize bounds tracking
    min_lat, max_lat = None, None
    min_lng, max_lng = None, None
    all_lats, all_lngs = [], []

    # Use interpolated elevation data - this is required for waypoint routes
    if interpolated_elevation_data and len(interpolated_elevation_data) >= 2:
        # Use the smoothed interpolated elevation data from the RoutePlanner
        # This data is already smoothed in the frontend to match the chart display
        start_time = datetime.now(UTC)
        for i, point_data in enumerate(interpolated_elevation_data):
            # Create progressive timestamps for better GPX compatibility
            point_time = start_time + timedelta(
                seconds=i * 10
            )  # 10 seconds between points
            point = GPXTrackPoint(
                point_data["lat"],
                point_data["lng"],
                elevation=point_data["elevation"],
                time=point_time,
            )
            gpx_segment.points.append(point)

            # Track bounds
            all_lats.append(point_data["lat"])
            all_lngs.append(point_data["lng"])

            if min_lat is None or point_data["lat"] < min_lat:
                min_lat = point_data["lat"]
            if max_lat is None or point_data["lat"] > max_lat:
                max_lat = point_data["lat"]
            if min_lng is None or point_data["lng"] < min_lng:
                min_lng = point_data["lng"]
            if max_lng is None or point_data["lng"] > max_lng:
                max_lng = point_data["lng"]
    else:
        # No valid elevation data available
        raise HTTPException(
            status_code=422,
            detail="Interpolated elevation data is required for waypoint-based routes",
        )

    # Add the segment to the track
    gpx_track.segments.append(gpx_segment)

    # Add the track to the GPX
    gpx.tracks.append(gpx_track)

    # Calculate bounds
    if min_lat is None or max_lat is None or min_lng is None or max_lng is None:
        raise HTTPException(
            status_code=422, detail="Unable to calculate bounds from route data"
        )

    if all_lats:
        barycenter_lat = sum(all_lats) / len(all_lats)
        barycenter_lng = sum(all_lngs) / len(all_lngs)
    else:
        barycenter_lat = (min_lat + max_lat) / 2
        barycenter_lng = (min_lng + max_lng) / 2

    bounds = {
        "north": max_lat,
        "south": min_lat,
        "east": max_lng,
        "west": min_lng,
        "barycenter_lat": barycenter_lat,
        "barycenter_lng": barycenter_lng,
    }

    # Return the GPX as XML string and bounds
    return gpx.to_xml(), bounds
