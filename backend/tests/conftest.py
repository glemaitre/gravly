import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Suppress RuntimeWarning about unawaited coroutines from AsyncMock
# during copy operations. This happens when AsyncMock objects are copied
# (e.g., during deepcopy in gpxpy or other libraries)
pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    """Configure pytest to filter out known warnings."""
    # Filter out RuntimeWarning about unawaited AsyncMock coroutines
    # during copy operations. This is a known issue when AsyncMock objects
    # are copied by libraries like gpxpy. The warning occurs when Python's
    # copy module tries to copy an AsyncMock object.
    import warnings

    warnings.filterwarnings(
        "ignore",
        message=r"coroutine 'AsyncMockMixin\._execute_mock_call' was never awaited",
        category=RuntimeWarning,
        module="copy",
    )


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
def client():
    """Provide a stravalib Client instance for testing."""
    from stravalib import Client

    return Client()
