"""Tests for the routes API endpoints."""

import pytest
from fastapi import HTTPException
from src.api.routes import calculate_route_statistics
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

    result = calculate_route_statistics(segments, {})

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

    result = calculate_route_statistics(segments, {})

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

    result = calculate_route_statistics(segments, {})

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

    result = calculate_route_statistics(segments, {})

    # Dry: slick, semi-slick, knobs -> worst case is knobs
    assert result["tire_dry"] == TireType.KNOBS

    # Wet: slick, knobs, semi-slick -> worst case is knobs
    assert result["tire_wet"] == TireType.KNOBS


def test_calculate_route_statistics_empty_segments():
    """Test that empty segments list raises HTTPException."""
    with pytest.raises(HTTPException):  # HTTPException from FastAPI
        calculate_route_statistics([], {})


def test_calculate_route_statistics_with_route_coordinates():
    """Test calculation with actual route coordinates."""
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

    actual_route_coordinates = [
        {"lat": 44.5, "lng": 1.5},
        {"lat": 44.6, "lng": 1.6},
        {"lat": 44.7, "lng": 1.7},
    ]

    result = calculate_route_statistics(segments, {}, actual_route_coordinates)

    # Should use actual route coordinates for bounds calculation
    assert result["bounds"]["north"] == 44.7
    assert result["bounds"]["south"] == 44.5
    assert result["bounds"]["east"] == 1.7
    assert result["bounds"]["west"] == 1.5
    assert result["bounds"]["barycenter_lat"] == 44.6
    assert abs(result["bounds"]["barycenter_lng"] - 1.6) < 1e-10


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

    result = calculate_route_statistics(segments, {})

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

    result = calculate_route_statistics(segments, {})

    # Average should be (2 + 4 + 6) / 3 = 4.0, rounded to 4
    assert result["difficulty_level"] == 4


def test_calculate_route_statistics_with_non_finite_coordinates():
    """Test that non-finite coordinates are filtered out."""
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

    # Test with non-finite coordinates
    actual_route_coordinates = [
        {"lat": 44.5, "lng": 1.5},
        {"lat": float("inf"), "lng": 1.6},  # Should be filtered out
        {"lat": 44.7, "lng": float("-inf")},  # Should be filtered out
        {"lat": 44.8, "lng": 1.8},
    ]

    result = calculate_route_statistics(segments, {}, actual_route_coordinates)

    # Should use only the finite coordinates (44.5, 1.5) and (44.8, 1.8)
    # But since we only have 2 valid points, it should still work
    assert result["bounds"]["north"] == 44.8
    assert result["bounds"]["south"] == 44.5
    assert result["bounds"]["east"] == 1.8
    assert result["bounds"]["west"] == 1.5


def test_calculate_route_statistics_with_all_non_finite_coordinates():
    """Test that fallback to segment bounds when all coordinates are non-finite."""
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

    # Test with all non-finite coordinates
    actual_route_coordinates = [
        {"lat": float("inf"), "lng": 1.6},
        {"lat": 44.7, "lng": float("-inf")},
        {"lat": float("nan"), "lng": 1.8},
    ]

    result = calculate_route_statistics(segments, {}, actual_route_coordinates)

    # Should fallback to segment bounds
    assert result["bounds"]["north"] == 45.0
    assert result["bounds"]["south"] == 44.0
    assert result["bounds"]["east"] == 2.0
    assert result["bounds"]["west"] == 1.0
