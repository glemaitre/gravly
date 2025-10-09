"""Routes API endpoints."""

import logging
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import gpxpy
from fastapi import APIRouter, HTTPException, Request
from gpxpy.gpx import GPXTrack, GPXTrackPoint, GPXTrackSegment
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .. import dependencies
from ..models.track import (
    SurfaceType,
    TireType,
    Track,
    TrackResponse,
    TrackType,
)

logger = logging.getLogger(__name__)


def get_tire_recommendation(tire_types: set[TireType]) -> TireType:
    """Get the tire recommendation for the given tire types.

    Parameters
    ----------
    tire_types : list[TireType]
        List of tire types

    Returns
    -------
    TireType
        The tire recommendation
    """

    # Order: knobs > semi-slick > slick (from best to worst)
    if TireType.KNOBS in tire_types:
        return TireType.KNOBS
    elif TireType.SEMI_SLICK in tire_types:
        return TireType.SEMI_SLICK
    else:
        return TireType.SLICK


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
        from ..dependencies import storage_manager as global_storage_manager

        if not dependencies.SessionLocal:
            raise HTTPException(status_code=500, detail="Database not configured")

        try:
            body = await request.json()

            name = body.get("name")
            segments_data = body.get("segments", [])
            computed_stats = body.get("computed_stats", {})
            route_track_points = body.get("route_track_points", [])
            comments = body.get("comments", "").strip()

            async with dependencies.SessionLocal() as session:
                if segments_data:
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

                    segment_map = {seg.id: seg for seg in segments}
                    ordered_segments = []
                    for seg_data in segments_data:
                        segment_id = seg_data["id"]
                        if segment_id in segment_map:
                            segment = segment_map[segment_id]
                            segment.isReversed = seg_data.get("isReversed", False)
                            ordered_segments.append(segment)

                    route_stats = compute_route_features_from_segments(ordered_segments)
                else:
                    route_stats = compute_route_features_route()

                if not global_storage_manager:
                    raise HTTPException(
                        status_code=500, detail="Storage manager not available"
                    )

                route_gpx_data, bounds = await create_route_gpx(
                    computed_stats, route_track_points
                )

                route_file_id = str(uuid.uuid4())
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".gpx", delete=False
                ) as temp_file:
                    temp_file.write(route_gpx_data)
                    temp_file_path = Path(temp_file.name)

                try:
                    storage_key = global_storage_manager.upload_gpx_segment(
                        temp_file_path, route_file_id, prefix="routes"
                    )

                    route_file_path = (
                        f"{global_storage_manager.get_storage_root_prefix()}/"
                        f"{storage_key}"
                    )

                    temp_file_path.unlink()

                except Exception as e:
                    if temp_file_path.exists():
                        temp_file_path.unlink()
                    raise HTTPException(
                        status_code=500, detail=f"Failed to save route GPX: {str(e)}"
                    )

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


def compute_route_features_route():
    """Compute route features for waypoint-based routes.

    For waypoint-based routes, we use default values since there are no segments
    to derive terrain characteristics from.

    Returns
    -------
    dict
        Route statistics with default values for difficulty, surface types,
        and tire recommendations
    """
    return {
        "difficulty_level": 2,
        "surface_types": [SurfaceType.BROKEN_PAVED_ROAD.value],
        "tire_dry": TireType.SEMI_SLICK,
        "tire_wet": TireType.KNOBS,
    }


def compute_route_features_from_segments(segments):
    """Compute route features from segments.

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

    total_difficulty = 0
    surface_types, dry_tire_types, wet_tire_types = [], [], []

    for segment in segments:
        total_difficulty += segment.difficulty_level
        surface_types.extend(segment.surface_type)
        dry_tire_types.append(segment.tire_dry)
        wet_tire_types.append(segment.tire_wet)

    avg_difficulty = round(total_difficulty / len(segments), 1)
    surface_types = list(set(surface_types))
    tire_dry_recommendation = get_tire_recommendation(set(dry_tire_types))
    tire_wet_recommendation = get_tire_recommendation(set(wet_tire_types))

    return {
        "difficulty_level": int(avg_difficulty),
        "surface_types": surface_types,
        "tire_dry": tire_dry_recommendation,
        "tire_wet": tire_wet_recommendation,
    }


async def create_route_gpx(computed_stats, route_track_points):
    """Create GPX data using interpolated route track points.

    This function is used for both guided mode (with segments) and free mode
    (waypoints). It uses the interpolated route track points from OSRM routing
    which includes elevation data and represents the actual path that will be
    followed. This function also calculates bounding box by processing the GPX
    points.

    Parameters
    ----------
    computed_stats : dict
        Pre-computed statistics from frontend
    route_track_points : list
        List of route track points with lat, lng, elevation, and distance data

    Returns
    -------
    tuple
        A tuple containing:
        - str: GPX XML content for the route
        - dict: Bounding box with north, south, east, west,
                barycenter_lat, barycenter_lng
    """

    distance = computed_stats.get("distance", 0)
    elevation_gain = computed_stats.get("elevationGain", 0)

    gpx = gpxpy.gpx.GPX()
    gpx.creator = "Gravly Route Planner"

    gpx_track = GPXTrack()
    gpx_track.name = "Route"
    gpx_track.description = (
        f"Route with interpolated track points - Distance: {distance:.2f}km, "
        f"Elevation: {elevation_gain:.0f}m"
    )

    gpx_segment = GPXTrackSegment()

    min_lat, max_lat = None, None
    min_lng, max_lng = None, None
    all_lats, all_lngs = [], []

    if route_track_points and len(route_track_points) >= 2:
        # Use the smoothed route track points from the RoutePlanner
        # This data includes elevation and matches the chart display
        start_time = datetime.now(UTC)
        for i, point_data in enumerate(route_track_points):
            point_time = start_time + timedelta(seconds=i * 10)
            point = GPXTrackPoint(
                point_data["lat"],
                point_data["lng"],
                elevation=point_data["elevation"],
                time=point_time,
            )
            gpx_segment.points.append(point)

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
        raise HTTPException(
            status_code=422,
            detail="Route track points are required to create route GPX",
        )

    gpx_track.segments.append(gpx_segment)
    gpx.tracks.append(gpx_track)

    if min_lat is None or max_lat is None or min_lng is None or max_lng is None:
        raise HTTPException(
            status_code=422, detail="Unable to calculate bounds from route data"
        )

    barycenter_lat = sum(all_lats) / len(all_lats)
    barycenter_lng = sum(all_lngs) / len(all_lngs)

    bounds = {
        "north": max_lat,
        "south": min_lat,
        "east": max_lng,
        "west": min_lng,
        "barycenter_lat": barycenter_lat,
        "barycenter_lng": barycenter_lng,
    }

    return gpx.to_xml(), bounds
