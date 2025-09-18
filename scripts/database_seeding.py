#!/usr/bin/env python3
"""
Database Seeding Script for Cycling GPX Segments

This script generates 1,000 realistic 5km cycling GPX segments across France
and uploads them to both storage and the database for testing the map exploration feature.

Usage:
    pixi run python scripts/database_seeding.py
"""

import asyncio
import logging
import math
import random

# Add the backend src directory to the Python path
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import NamedTuple

import gpxpy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).parent.parent / "backend" / "src"))

from models.base import Base
from models.track import SurfaceType, TireType, Track, TrackType
from utils.config import load_environment_config
from utils.math import haversine_distance
from utils.postgres import get_database_url
from utils.storage import cleanup_local_file, get_storage_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FrenchRegion(NamedTuple):
    """Represents a French region with its geographic bounds."""

    name: str
    north: float
    south: float
    east: float
    west: float
    elevation_min: float
    elevation_max: float


# French regions with realistic geographic bounds and elevation ranges
FRENCH_REGIONS = [
    FrenchRegion("Île-de-France", 49.2, 48.1, 3.6, 1.4, 20, 200),
    FrenchRegion("Provence-Alpes-Côte d'Azur", 45.0, 43.0, 7.7, 4.5, 0, 4000),
    FrenchRegion("Auvergne-Rhône-Alpes", 46.5, 44.0, 7.0, 2.0, 200, 4800),
    FrenchRegion("Occitanie", 45.0, 42.0, 4.0, 1.0, 0, 3000),
    FrenchRegion("Nouvelle-Aquitaine", 47.0, 42.0, 2.0, -1.0, 0, 2000),
    FrenchRegion("Bretagne", 48.9, 47.0, -1.0, -5.0, 0, 400),
    FrenchRegion("Normandie", 49.5, 48.0, 2.0, -2.0, 0, 400),
    FrenchRegion("Hauts-de-France", 51.0, 49.0, 4.0, 1.0, 0, 300),
    FrenchRegion("Grand Est", 50.0, 47.0, 8.0, 3.0, 100, 1500),
    FrenchRegion("Bourgogne-Franche-Comté", 48.0, 46.0, 7.0, 2.0, 200, 1700),
    FrenchRegion("Centre-Val de Loire", 48.5, 46.0, 3.0, 0.0, 50, 500),
    FrenchRegion("Pays de la Loire", 48.5, 46.0, 1.0, -2.0, 0, 400),
    FrenchRegion("Corse", 43.0, 41.0, 9.5, 8.0, 0, 2700),
]

# Surface types with realistic probabilities for France
SURFACE_TYPES = [
    (SurfaceType.BROKEN_PAVED_ROAD, 0.3),
    (SurfaceType.DIRTY_ROAD, 0.2),
    (SurfaceType.FIELD_TRAIL, 0.15),
    (SurfaceType.FOREST_TRAIL, 0.15),
    (SurfaceType.SMALL_STONE_ROAD, 0.1),
    (SurfaceType.BIG_STONE_ROAD, 0.1),
]

# Tire types with realistic combinations
TIRE_COMBINATIONS = [
    (TireType.SLICK, TireType.SEMI_SLICK),
    (TireType.SEMI_SLICK, TireType.KNOBS),
    (TireType.KNOBS, TireType.KNOBS),
    (TireType.SLICK, TireType.SLICK),
]

# Difficulty levels (1-5 scale)
DIFFICULTY_LEVELS = [1, 2, 3, 4, 5]


def generate_realistic_cycling_route(
    region: FrenchRegion, target_distance_km: float = 5.0, num_points: int = 50
) -> list[tuple[float, float, float, datetime]]:
    """
    Generate a realistic cycling route within a French region.

    Parameters
    ----------
    region : FrenchRegion
        The French region to generate the route in
    target_distance_km : float
        Target distance in kilometers (default: 5.0)
    num_points : int
        Number of GPS points to generate (default: 50)

    Returns
    -------
    list[tuple[float, float, float, datetime]]
        List of (latitude, longitude, elevation, timestamp) tuples
    """
    # Start from a random point within the region
    start_lat = random.uniform(region.south, region.north)
    start_lon = random.uniform(region.west, region.east)
    start_elevation = random.uniform(region.elevation_min, region.elevation_max)

    # Generate a route that roughly follows roads (not straight lines)
    points = []
    current_lat, current_lon = start_lat, start_lon
    current_elevation = start_elevation

    # Start time (recent)
    current_time = datetime.now(UTC) - timedelta(days=random.randint(0, 30))

    # Add some variation to make routes more realistic
    total_distance = 0.0
    segment_distance = target_distance_km / num_points

    for i in range(num_points):
        # Add the current point
        points.append((current_lat, current_lon, current_elevation, current_time))

        if i == num_points - 1:
            break

        # Calculate next point with some randomness to simulate road following
        # Use a combination of straight line and random deviation
        remaining_points = num_points - i - 1
        remaining_distance = target_distance_km - total_distance

        if remaining_points > 0:
            next_segment_distance = remaining_distance / remaining_points
        else:
            next_segment_distance = segment_distance

        # Convert distance to approximate lat/lon degrees
        # Rough approximation: 1 degree latitude ≈ 111 km
        lat_delta = (next_segment_distance / 111.0) * random.uniform(0.8, 1.2)
        lon_delta = (
            next_segment_distance / (111.0 * math.cos(math.radians(current_lat)))
        ) * random.uniform(0.8, 1.2)

        # Add some randomness to simulate road curves
        direction_variation = random.uniform(-0.3, 0.3)
        lat_delta += lat_delta * direction_variation
        lon_delta += lon_delta * direction_variation

        # Ensure we stay within region bounds
        next_lat = current_lat + lat_delta
        next_lon = current_lon + lon_delta

        # Clamp to region bounds
        next_lat = max(region.south, min(region.north, next_lat))
        next_lon = max(region.west, min(region.east, next_lon))

        # Add elevation variation (cycling routes have elevation changes)
        elevation_change = random.uniform(-20, 20)  # meters per segment
        next_elevation = max(
            region.elevation_min,
            min(region.elevation_max, current_elevation + elevation_change),
        )

        # Add time progression (cycling speed varies)
        time_delta = timedelta(seconds=random.randint(30, 120))  # 30s to 2min per point
        next_time = current_time + time_delta

        # Update for next iteration
        current_lat, current_lon = next_lat, next_lon
        current_elevation = next_elevation
        current_time = next_time

        # Calculate actual distance for more accurate total
        if i > 0:
            prev_lat, prev_lon = points[-2][0], points[-2][1]
            distance_km = haversine_distance(
                latitude_1=prev_lat,
                longitude_1=prev_lon,
                latitude_2=current_lat,
                longitude_2=current_lon,
            )
            total_distance += distance_km

    return points


def create_gpx_file(
    points: list[tuple[float, float, float, datetime]], track_name: str
) -> gpxpy.gpx.GPX:
    """Create a GPX file from a list of points."""
    gpx = gpxpy.gpx.GPX()

    # Create track
    track = gpxpy.gpx.GPXTrack(name=track_name)
    gpx.tracks.append(track)

    # Create segment
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    # Add points
    for lat, lon, elev, time in points:
        point = gpxpy.gpx.GPXTrackPoint(lat, lon, elev, time)
        segment.points.append(point)

    return gpx


def calculate_bounds(
    points: list[tuple[float, float, float, datetime]],
) -> tuple[float, float, float, float]:
    """Calculate bounding box for the points."""
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return max(lats), min(lats), max(lons), min(lons)


def select_random_surface_type() -> SurfaceType:
    """Select a surface type based on realistic probabilities."""
    rand = random.random()
    cumulative = 0.0
    for surface_type, probability in SURFACE_TYPES:
        cumulative += probability
        if rand <= cumulative:
            return surface_type
    return SurfaceType.BROKEN_PAVED_ROAD  # fallback


def select_random_tire_types() -> tuple[TireType, TireType]:
    """Select random tire types for dry and wet conditions."""
    return random.choice(TIRE_COMBINATIONS)


def select_random_difficulty() -> int:
    """Select a random difficulty level."""
    return random.choice(DIFFICULTY_LEVELS)


async def seed_database(
    num_segments: int = 1000, target_distance_km: float = 5.0, batch_size: int = 50
) -> None:
    """
    Generate and seed the database with cycling GPX segments.

    Parameters
    ----------
    num_segments : int
        Number of segments to generate (default: 1000)
    target_distance_km : float
        Target distance for each segment in kilometers (default: 5.0)
    batch_size : int
        Number of segments to process in each batch (default: 50)
    """
    logger.info(f"Starting database seeding with {num_segments} segments")

    # Load configuration
    try:
        db_config, storage_config = load_environment_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # Initialize database
    database_url = get_database_url(
        host=db_config.host,
        port=db_config.port,
        database=db_config.name,
        username=db_config.user,
        password=db_config.password,
    )

    engine = create_async_engine(database_url, echo=False, future=True)
    SessionLocal = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    # Initialize storage
    storage_manager = get_storage_manager(storage_config)

    # Create temporary directory for GPX files
    temp_dir = Path("/tmp/cycling_gpx_seeds")
    temp_dir.mkdir(exist_ok=True)

    try:
        # Ensure database tables exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured")

        # Process segments in batches
        total_processed = 0
        total_errors = 0

        for batch_start in range(0, num_segments, batch_size):
            batch_end = min(batch_start + batch_size, num_segments)
            batch_size_actual = batch_end - batch_start

            logger.info(
                f"Processing batch {batch_start // batch_size + 1}: segments {batch_start + 1}-{batch_end}"
            )

            # Generate segments for this batch
            segments_data = []
            for i in range(batch_size_actual):
                segment_num = batch_start + i + 1

                try:
                    # Select random region
                    region = random.choice(FRENCH_REGIONS)

                    # Generate route points
                    points = generate_realistic_cycling_route(
                        region, target_distance_km
                    )

                    # Create GPX file
                    track_name = f"Segment {segment_num:04d} - {region.name}"
                    gpx = create_gpx_file(points, track_name)

                    # Calculate bounds
                    north, south, east, west = calculate_bounds(points)

                    # Select random attributes
                    surface_type = select_random_surface_type()
                    tire_dry, tire_wet = select_random_tire_types()
                    difficulty = select_random_difficulty()

                    # Generate comments
                    comments = (
                        f"Surface: {surface_type.value}, Difficulty: {difficulty}/5"
                    )

                    segments_data.append(
                        {
                            "gpx": gpx,
                            "track_name": track_name,
                            "bounds": (north, south, east, west),
                            "surface_type": surface_type,
                            "tire_dry": tire_dry,
                            "tire_wet": tire_wet,
                            "difficulty": difficulty,
                            "comments": comments,
                            "region": region.name,
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to generate segment {segment_num}: {e}")
                    total_errors += 1
                    continue

            # Process batch: upload to storage and save to database
            async with SessionLocal() as session:
                for segment_data in segments_data:
                    try:
                        # Generate unique file ID
                        file_id = str(uuid.uuid4())

                        # Save GPX to temporary file
                        temp_file = temp_dir / f"{file_id}.gpx"
                        with open(temp_file, "w") as f:
                            f.write(segment_data["gpx"].to_xml())

                        # Upload to storage
                        storage_key = storage_manager.upload_gpx_segment(
                            local_file_path=temp_file,
                            file_id=file_id,
                            prefix="gpx-segments",
                        )

                        # Clean up temporary file
                        cleanup_local_file(temp_file)

                        # Create database record
                        north, south, east, west = segment_data["bounds"]
                        processed_file_path = (
                            f"{storage_manager.get_storage_root_prefix()}/{storage_key}"
                        )

                        # Calculate barycenter from bounds
                        barycenter_latitude = (north + south) / 2
                        barycenter_longitude = (east + west) / 2

                        track = Track(
                            file_path=processed_file_path,
                            bound_north=north,
                            bound_south=south,
                            bound_east=east,
                            bound_west=west,
                            barycenter_latitude=barycenter_latitude,
                            barycenter_longitude=barycenter_longitude,
                            name=segment_data["track_name"],
                            track_type=TrackType.SEGMENT,
                            difficulty_level=segment_data["difficulty"],
                            surface_type=segment_data["surface_type"],
                            tire_dry=segment_data["tire_dry"],
                            tire_wet=segment_data["tire_wet"],
                            comments=segment_data["comments"],
                        )

                        session.add(track)
                        total_processed += 1

                    except Exception as e:
                        logger.error(f"Failed to process segment: {e}")
                        total_errors += 1
                        continue

                # Commit batch
                await session.commit()
                logger.info(f"Batch committed: {len(segments_data)} segments processed")

        logger.info(f"Database seeding completed!")
        logger.info(f"Total segments processed: {total_processed}")
        logger.info(f"Total errors: {total_errors}")

    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise
    finally:
        # Cleanup
        await engine.dispose()
        if temp_dir.exists():
            import shutil

            shutil.rmtree(temp_dir)


async def main():
    """Main function to run the database seeding."""
    logger.info("Starting cycling GPX database seeding script")

    try:
        await seed_database(num_segments=1000, target_distance_km=5.0, batch_size=50)
        logger.info("Database seeding completed successfully!")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
