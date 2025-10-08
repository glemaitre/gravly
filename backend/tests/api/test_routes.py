"""Tests for the routes API endpoints."""

import asyncio

import pytest
from fastapi import HTTPException
from src.api.routes import (
    calculate_route_statistics,
    create_waypoint_route_gpx,
)
from src.models.track import TireType


class MockSegment:
    """Mock segment class for testing."""

    def __init__(
        self,
        difficulty_level,
        surface_type,
        tire_dry,
        tire_wet,
        bound_north,
        bound_south,
        bound_east,
        bound_west,
    ):
        self.difficulty_level = difficulty_level
        self.surface_type = surface_type
        self.tire_dry = tire_dry
        self.tire_wet = tire_wet
        self.bound_north = bound_north
        self.bound_south = bound_south
        self.bound_east = bound_east
        self.bound_west = bound_west


def test_calculate_route_statistics_dry_wet_tire_separation():
    """Test that tire recommendations are calculated separately for dry and wet conditions."""  # noqa: E501
    # Create segments with different dry and wet tire recommendations
    segments = [
        MockSegment(
            difficulty_level=3,
            surface_type=["asphalt"],
            tire_dry=TireType.SLICK,
            tire_wet=TireType.SEMI_SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        ),
        MockSegment(
            difficulty_level=4,
            surface_type=["forest-trail"],
            tire_dry=TireType.SEMI_SLICK,
            tire_wet=TireType.KNOBS,
            bound_north=45.1,
            bound_south=44.1,
            bound_east=2.1,
            bound_west=1.1,
        ),
    ]

    result = calculate_route_statistics(segments)

    # Dry tire should be semi-slick (worst case from dry tires)
    assert result["tire_dry"] == TireType.SEMI_SLICK

    # Wet tire should be knobs (worst case from wet tires)
    assert result["tire_wet"] == TireType.KNOBS


def test_calculate_route_statistics_same_dry_wet_tires():
    """Test when dry and wet tire recommendations are the same."""
    segments = [
        MockSegment(
            difficulty_level=2,
            surface_type=["asphalt"],
            tire_dry=TireType.SLICK,
            tire_wet=TireType.SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        )
    ]

    result = calculate_route_statistics(segments)

    # Both should be slick
    assert result["tire_dry"] == TireType.SLICK
    assert result["tire_wet"] == TireType.SLICK


def test_calculate_route_statistics_knobs_dry_slick_wet():
    """Test when dry requires knobs but wet only needs slick."""
    segments = [
        MockSegment(
            difficulty_level=5,
            surface_type=["field-trail"],
            tire_dry=TireType.KNOBS,
            tire_wet=TireType.SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        )
    ]

    result = calculate_route_statistics(segments)

    # Dry should be knobs, wet should be slick
    assert result["tire_dry"] == TireType.KNOBS
    assert result["tire_wet"] == TireType.SLICK


def test_calculate_route_statistics_mixed_conditions():
    """Test with multiple segments having mixed tire recommendations."""
    segments = [
        MockSegment(
            difficulty_level=2,
            surface_type=["asphalt"],
            tire_dry=TireType.SLICK,
            tire_wet=TireType.SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        ),
        MockSegment(
            difficulty_level=3,
            surface_type=["forest-trail"],
            tire_dry=TireType.SEMI_SLICK,
            tire_wet=TireType.KNOBS,
            bound_north=45.1,
            bound_south=44.1,
            bound_east=2.1,
            bound_west=1.1,
        ),
        MockSegment(
            difficulty_level=4,
            surface_type=["field-trail"],
            tire_dry=TireType.KNOBS,
            tire_wet=TireType.SEMI_SLICK,
            bound_north=45.2,
            bound_south=44.2,
            bound_east=2.2,
            bound_west=1.2,
        ),
    ]

    result = calculate_route_statistics(segments)

    # Dry: slick, semi-slick, knobs -> worst case is knobs
    assert result["tire_dry"] == TireType.KNOBS

    # Wet: slick, knobs, semi-slick -> worst case is knobs
    assert result["tire_wet"] == TireType.KNOBS


def test_calculate_route_statistics_empty_segments():
    """Test that empty segments list raises HTTPException."""
    with pytest.raises(HTTPException):  # HTTPException from FastAPI
        calculate_route_statistics([])


def test_calculate_route_statistics_basic_stats():
    """Test that basic statistics are calculated correctly."""
    segments = [
        MockSegment(
            difficulty_level=3,
            surface_type=["asphalt"],
            tire_dry=TireType.SLICK,
            tire_wet=TireType.SEMI_SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        )
    ]

    result = calculate_route_statistics(segments)

    # Should calculate difficulty, surface types, and tire recommendations
    assert result["difficulty_level"] == 3
    assert "asphalt" in result["surface_types"]
    assert result["tire_dry"] == TireType.SLICK
    assert result["tire_wet"] == TireType.SEMI_SLICK
    # Bounds are no longer calculated in this function
    assert "bounds" not in result


def test_calculate_route_statistics_surface_types_union():
    """Test that surface types are properly unionized."""
    segments = [
        MockSegment(
            difficulty_level=2,
            surface_type=["asphalt", "concrete"],
            tire_dry=TireType.SLICK,
            tire_wet=TireType.SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        ),
        MockSegment(
            difficulty_level=3,
            surface_type=["forest-trail", "asphalt"],
            tire_dry=TireType.SEMI_SLICK,
            tire_wet=TireType.SEMI_SLICK,
            bound_north=45.1,
            bound_south=44.1,
            bound_east=2.1,
            bound_west=1.1,
        ),
    ]

    result = calculate_route_statistics(segments)

    # Should contain all unique surface types
    surface_types = set(result["surface_types"])
    expected_surface_types = {"asphalt", "concrete", "forest-trail"}
    assert surface_types == expected_surface_types


def test_calculate_route_statistics_difficulty_average():
    """Test that difficulty level is properly averaged."""
    segments = [
        MockSegment(
            difficulty_level=2,
            surface_type=["asphalt"],
            tire_dry=TireType.SLICK,
            tire_wet=TireType.SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        ),
        MockSegment(
            difficulty_level=4,
            surface_type=["forest-trail"],
            tire_dry=TireType.SEMI_SLICK,
            tire_wet=TireType.SEMI_SLICK,
            bound_north=45.1,
            bound_south=44.1,
            bound_east=2.1,
            bound_west=1.1,
        ),
        MockSegment(
            difficulty_level=6,
            surface_type=["field-trail"],
            tire_dry=TireType.KNOBS,
            tire_wet=TireType.KNOBS,
            bound_north=45.2,
            bound_south=44.2,
            bound_east=2.2,
            bound_west=1.2,
        ),
    ]

    result = calculate_route_statistics(segments)

    # Average should be (2 + 4 + 6) / 3 = 4.0, rounded to 4
    assert result["difficulty_level"] == 4


def test_calculate_route_statistics_multiple_surface_types():
    """Test route with multiple different surface types."""
    segments = [
        MockSegment(
            difficulty_level=3,
            surface_type=["asphalt", "concrete"],
            tire_dry=TireType.SLICK,
            tire_wet=TireType.SEMI_SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        ),
        MockSegment(
            difficulty_level=4,
            surface_type=["forest-trail"],
            tire_dry=TireType.KNOBS,
            tire_wet=TireType.KNOBS,
            bound_north=45.1,
            bound_south=44.1,
            bound_east=2.1,
            bound_west=1.1,
        ),
    ]

    result = calculate_route_statistics(segments)

    # Should contain all unique surface types
    surface_types = set(result["surface_types"])
    assert "asphalt" in surface_types
    assert "concrete" in surface_types
    assert "forest-trail" in surface_types
    assert len(surface_types) == 3


def test_calculate_route_statistics_tire_priority():
    """Test tire recommendations priority: knobs > semi-slick > slick."""
    segments = [
        MockSegment(
            difficulty_level=2,
            surface_type=["asphalt"],
            tire_dry=TireType.SLICK,
            tire_wet=TireType.SLICK,
            bound_north=45.0,
            bound_south=44.0,
            bound_east=2.0,
            bound_west=1.0,
        ),
        MockSegment(
            difficulty_level=3,
            surface_type=["forest-trail"],
            tire_dry=TireType.KNOBS,
            tire_wet=TireType.SEMI_SLICK,
            bound_north=45.1,
            bound_south=44.1,
            bound_east=2.1,
            bound_west=1.1,
        ),
    ]

    result = calculate_route_statistics(segments)

    # Worst case: knobs for dry, semi-slick for wet
    assert result["tire_dry"] == TireType.KNOBS
    assert result["tire_wet"] == TireType.SEMI_SLICK


def test_create_waypoint_route_gpx_with_valid_points():
    """Test GPX creation with valid route track points."""
    computed_stats = {
        "distance": 10.5,
        "elevationGain": 250,
    }
    route_track_points = [
        {"lat": 45.0, "lng": 5.0, "elevation": 100, "distance": 0},
        {"lat": 45.01, "lng": 5.01, "elevation": 120, "distance": 1000},
        {"lat": 45.02, "lng": 5.02, "elevation": 150, "distance": 2000},
    ]

    gpx_xml, bounds = asyncio.run(
        create_waypoint_route_gpx(computed_stats, route_track_points)
    )

    # Verify GPX content
    assert "<?xml version=" in gpx_xml
    assert "gpx" in gpx_xml.lower()
    assert "Route with interpolated track points" in gpx_xml

    # Verify bounds
    assert bounds["north"] == 45.02
    assert bounds["south"] == 45.0
    assert bounds["east"] == 5.02
    assert bounds["west"] == 5.0
    assert 45.0 <= bounds["barycenter_lat"] <= 45.02
    assert 5.0 <= bounds["barycenter_lng"] <= 5.02


def test_create_waypoint_route_gpx_empty_points():
    """Test that empty route track points raises HTTPException."""
    computed_stats = {
        "distance": 10.5,
        "elevationGain": 250,
    }
    route_track_points = []

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(create_waypoint_route_gpx(computed_stats, route_track_points))

    assert exc_info.value.status_code == 422
    assert "required" in exc_info.value.detail.lower()


def test_create_waypoint_route_gpx_single_point():
    """Test that single point raises HTTPException (need at least 2 points)."""
    computed_stats = {
        "distance": 0,
        "elevationGain": 0,
    }
    route_track_points = [
        {"lat": 45.0, "lng": 5.0, "elevation": 100, "distance": 0},
    ]

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(create_waypoint_route_gpx(computed_stats, route_track_points))

    assert exc_info.value.status_code == 422
    assert "required" in exc_info.value.detail.lower()
