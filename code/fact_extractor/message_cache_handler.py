"""
message_cache_handler.py - Handles persistent caching of message LLM extraction results in message_cache.json.
"""

import json
from pathlib import Path
from typing import Dict, List

CACHE_FILE = Path(__file__).resolve().parent / "message_cache.json"


def load_message_cache() -> Dict[str, List[dict]]:
    """Loads cached message LLM extraction updates from message_cache.json."""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_message_cache(cache: Dict[str, List[dict]]):
    """Saves updated message LLM extraction results to message_cache.json."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
