import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from stravalib.tests.integration.strava_api_stub import StravaAPIMock

# Ensure backend src is on sys.path for imports like `from src import main`
# When running from project root, we need to add the backend/src directory
BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture(autouse=True)
def mock_aws_environment():
    """Mock AWS environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "AWS_S3_BUCKET": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        },
    ):
        yield


@pytest.fixture
def mock_strava_api():
    """Provide the stravalib mock API fixture for testing."""
    return StravaAPIMock()


@pytest.fixture
def client():
    """Provide a stravalib Client instance for testing."""
    from stravalib import Client
    return Client()
