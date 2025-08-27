import json
import os
from typing import Dict, Any


def load_constants() -> Dict[str, Any]:
    """Load constants from JSON file"""
    constants_path = os.path.join(os.path.dirname(__file__), "constants.json")
    with open(constants_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load constants
CONSTANTS = load_constants()

# Extract commonly used constants
STATES = CONSTANTS["states"]
LANGUAGES = CONSTANTS["languages"]
MESSAGES = CONSTANTS["messages"]
LANGUAGE_BUTTONS = CONSTANTS["language_buttons"]

# State constants for easier access
CHOOSING_LANGUAGE = STATES["CHOOSING_LANGUAGE"]
ENTERING_NAME = STATES["ENTERING_NAME"]
ENTERING_SURNAME = STATES["ENTERING_SURNAME"]
