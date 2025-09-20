"""Pytest configuration for Strava service tests."""

import pytest
from stravalib.tests.integration.strava_api_stub import StravaAPIMock


@pytest.fixture
def mock_strava_api():
    """Provide the stravalib mock API fixture for testing."""
    return StravaAPIMock()


@pytest.fixture
def client():
    """Provide a stravalib Client instance for testing."""
    from stravalib import Client
    return Client()
