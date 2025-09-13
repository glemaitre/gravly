import sys
import tempfile
from pathlib import Path

import pytest

# Ensure backend src is on sys.path for imports like `from src import main`
# When running from project root, we need to add the backend/src directory
BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)
