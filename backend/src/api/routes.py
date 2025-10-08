"""Routes API endpoints."""

import logging
import math
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
                    route_stats = calculate_route_statistics(
                        ordered_segments, computed_stats, actual_route_coordinates
                    )
                else:
                    # Waypoint-based route: use default values and computed stats
                    route_stats = calculate_waypoint_route_statistics(
                        computed_stats,
                        interpolated_elevation_data,
                        actual_route_coordinates,
                    )

                if not global_storage_manager:
                    raise HTTPException(
                        status_code=500, detail="Storage manager not available"
                    )

                # Create GPX file for the route
                if segments_data:
                    route_gpx_data = await create_route_gpx(ordered_segments)
                else:
                    route_gpx_data = await create_waypoint_route_gpx(
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

                # Validate bounds before creating track
                bounds_to_save = route_stats["bounds"]
                bound_fields = {
                    "north": bounds_to_save["north"],
                    "south": bounds_to_save["south"],
                    "east": bounds_to_save["east"],
                    "west": bounds_to_save["west"],
                    "barycenter_lat": bounds_to_save["barycenter_lat"],
                    "barycenter_lng": bounds_to_save["barycenter_lng"],
                }

                if not all(
                    isinstance(value, (int, float)) and math.isfinite(value)
                    for value in bound_fields.values()
                ):
                    raise HTTPException(
                        status_code=422,
                        detail="Cannot save route with invalid bounds data",
                    )

                # Create the route track
                route_track = Track(
                    file_path=route_file_path,
                    bound_north=route_stats["bounds"]["north"],
                    bound_south=route_stats["bounds"]["south"],
                    bound_east=route_stats["bounds"]["east"],
                    bound_west=route_stats["bounds"]["west"],
                    barycenter_latitude=route_stats["bounds"]["barycenter_lat"],
                    barycenter_longitude=route_stats["bounds"]["barycenter_lng"],
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


def calculate_waypoint_route_statistics(
    computed_stats, interpolated_elevation_data=None, actual_route_coordinates=None
):
    """Calculate route statistics for waypoint-based routes using actual coordinates.

    Parameters
    ----------
    computed_stats : dict
        Pre-computed statistics from frontend (distance, elevation gain)
    interpolated_elevation_data : list, optional
        List of interpolated elevation data with lat, lng, elevation, distance
    actual_route_coordinates : list, optional
        List of actual route coordinates from the RoutePlanner

    Returns
    -------
    dict
        Route statistics with bounds calculated from actual route coordinates
    """
    # Use default values for segment-specific statistics
    default_difficulty = 2  # Medium difficulty
    default_surface_types = [
        SurfaceType.BROKEN_PAVED_ROAD.value
    ]  # Default to paved road
    default_tire_dry = TireType.SEMI_SLICK  # Conservative recommendation
    default_tire_wet = TireType.KNOBS  # Safe for wet conditions

    # Calculate bounds from actual route coordinates (preferred)
    if actual_route_coordinates and len(actual_route_coordinates) >= 2:
        # Filter out non-finite coordinates to avoid NaN/inf propagating
        actual_route_coordinates = _filter_finite_coordinates(actual_route_coordinates)
        # If not enough valid points remain, skip to next fallback
        use_actual_coords = len(actual_route_coordinates) >= 2
    else:
        use_actual_coords = False

    if use_actual_coords:
        # Calculate bounds from actual route coordinates
        lats = [point["lat"] for point in actual_route_coordinates]
        lngs = [point["lng"] for point in actual_route_coordinates]

        bounds = {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs),
            "barycenter_lat": sum(lats) / len(lats),
            "barycenter_lng": sum(lngs) / len(lngs),
        }
        _ensure_finite_bounds(bounds)
    # Fallback to interpolated elevation data if available
    elif interpolated_elevation_data and len(interpolated_elevation_data) >= 2:
        # Filter out non-finite coordinates from interpolated elevation data
        interpolated_elevation_data = _filter_finite_coordinates(
            interpolated_elevation_data
        )
        if len(interpolated_elevation_data) < 2:
            # Not enough valid points, fall back to computed_stats
            bounds = computed_stats.get(
                "bounds",
                {
                    "north": 46.9,
                    "south": 46.8,
                    "east": 4.0,
                    "west": 3.9,
                    "barycenter_lat": 46.85,
                    "barycenter_lng": 3.95,
                },
            )
            _ensure_finite_bounds(bounds)
            return {
                "difficulty_level": default_difficulty,
                "surface_types": default_surface_types,
                "tire_dry": default_tire_dry,
                "tire_wet": default_tire_wet,
                "bounds": bounds,
            }
        # Calculate bounds from interpolated elevation data
        lats = [point["lat"] for point in interpolated_elevation_data]
        lngs = [point["lng"] for point in interpolated_elevation_data]

        bounds = {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs),
            "barycenter_lat": sum(lats) / len(lats),
            "barycenter_lng": sum(lngs) / len(lngs),
        }
        _ensure_finite_bounds(bounds)
    else:
        # Fallback to bounds from computed_stats or defaults
        bounds = computed_stats.get(
            "bounds",
            {
                "north": 46.9,
                "south": 46.8,
                "east": 4.0,
                "west": 3.9,
                "barycenter_lat": 46.85,
                "barycenter_lng": 3.95,
            },
        )
        _ensure_finite_bounds(bounds)

    return {
        "difficulty_level": default_difficulty,
        "surface_types": default_surface_types,
        "tire_dry": default_tire_dry,
        "tire_wet": default_tire_wet,
        "bounds": bounds,
    }


def calculate_route_statistics(segments, computed_stats, actual_route_coordinates=None):
    """Calculate route statistics from segments.

    Parameters
    ----------
    segments : list
        List of segment Track objects
    computed_stats : dict
        Pre-computed statistics from frontend
    actual_route_coordinates : list, optional
        List of actual route coordinates from the RoutePlanner

    Returns
    -------
    dict
        Calculated route statistics
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

    # Calculate bounds - prefer actual route coordinates if available
    if actual_route_coordinates and len(actual_route_coordinates) >= 2:
        # Filter out non-finite coordinates to avoid NaN/inf propagating
        actual_route_coordinates = _filter_finite_coordinates(actual_route_coordinates)
        use_actual_coords = len(actual_route_coordinates) >= 2
    else:
        use_actual_coords = False

    if use_actual_coords:
        # Calculate bounds from actual route coordinates
        lats = [point["lat"] for point in actual_route_coordinates]
        lngs = [point["lng"] for point in actual_route_coordinates]

        bounds = {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs),
            "barycenter_lat": sum(lats) / len(lats),
            "barycenter_lng": sum(lngs) / len(lngs),
        }
        _ensure_finite_bounds(bounds)
    else:
        # Fallback to bounds from segments
        min_lat = min(segment.bound_south for segment in segments)
        max_lat = max(segment.bound_north for segment in segments)
        min_lng = min(segment.bound_west for segment in segments)
        max_lng = max(segment.bound_east for segment in segments)

        # Calculate barycenter
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
        _ensure_finite_bounds(bounds)

    return {
        "difficulty_level": int(avg_difficulty),
        "surface_types": surface_types,
        "tire_dry": tire_dry_recommendation,
        "tire_wet": tire_wet_recommendation,
        "bounds": bounds,
    }


def _ensure_finite_bounds(bounds: dict) -> None:
    """Validate that all bound values are finite numbers.

    Raises a 422 error if any value is NaN or infinite, which would break JSON encoding.
    """
    required_keys = (
        "north",
        "south",
        "east",
        "west",
        "barycenter_lat",
        "barycenter_lng",
    )
    for key in required_keys:
        value = bounds.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise HTTPException(
                status_code=422, detail=f"Invalid bound value for {key}: {value}"
            )


def _filter_finite_coordinates(points: list[dict]) -> list[dict]:
    """Return only points with finite lat/lng values.

    This helper prevents NaN/±inf coordinates from propagating into bounds
    calculations, which would otherwise produce invalid JSON values.
    """
    filtered_points: list[dict] = []
    for point in points:
        lat = point.get("lat")
        lng = point.get("lng")
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            if math.isfinite(lat) and math.isfinite(lng):
                filtered_points.append({"lat": float(lat), "lng": float(lng)})
    return filtered_points


async def create_route_gpx(segments):
    """Create GPX data for the route by combining segment GPX data.

    Parameters
    ----------
    segments : list
        List of segment Track objects

    Returns
    -------
    str
        GPX XML content for the route
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

                    # Add all points to the segment
                    for point in points:
                        gpx_point = GPXTrackPoint(
                            latitude=point.latitude,
                            longitude=point.longitude,
                            elevation=point.elevation,
                            time=point.time,
                        )
                        gpx_segment.points.append(gpx_point)

                    # Add the segment to the track
                    gpx_track.segments.append(gpx_segment)

        except Exception as e:
            logger.warning(f"Error loading GPX for segment {segment.id}: {str(e)}")
            # Continue with other segments even if one fails
            continue

    # Add the track to the GPX
    gpx.tracks.append(gpx_track)

    # Convert to XML string
    return gpx.to_xml()


async def create_waypoint_route_gpx(
    computed_stats, actual_route_coordinates, interpolated_elevation_data
):
    """Create GPX data for waypoint-based routes using actual route coordinates.

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
    str
        GPX XML content for the waypoint route
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

    # Return the GPX as XML string
    return gpx.to_xml()
