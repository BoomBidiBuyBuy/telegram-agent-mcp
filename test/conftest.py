import sys
import os
from pathlib import Path

# Add the src directory to the Python path for imports during testing
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Set default environment variables for testing
os.environ.setdefault("TEACHER_TELEGRAM_ID", "123456789")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("DEBUG_MODE", "0")
