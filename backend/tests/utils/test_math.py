from dataclasses import dataclass

import pytest

from backend.src.utils.math import haversine_distance


@dataclass
class Coordinates:
    """Represents a geographic coordinate with latitude and longitude."""

    latitude: float
    longitude: float


def test_paris_to_london_distance():
    """Test distance from Paris to London (approximately 344 km)."""
    paris = Coordinates(latitude=48.8566, longitude=2.3522)
    london = Coordinates(latitude=51.5074, longitude=-0.1278)

    distance = haversine_distance(
        latitude_1=paris.latitude,
        longitude_1=paris.longitude,
        latitude_2=london.latitude,
        longitude_2=london.longitude,
    )
    assert distance == pytest.approx(343.556, rel=1e-3)
