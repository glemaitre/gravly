import sys
from pathlib import Path

# Ensure backend src is on sys.path for imports like `from src import main`
# When running from project root, we need to add the backend/src directory
BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
