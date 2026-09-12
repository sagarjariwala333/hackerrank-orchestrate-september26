"""
image_cache_handler.py - Manages persistent JSON caching of LLM-extracted image amounts.
"""

import json
from pathlib import Path
from typing import Dict

CACHE_FILE = Path(__file__).resolve().parent / "image_cache.json"


def load_image_cache() -> Dict[str, float]:
    """Loads LLM-extracted image amounts from persistent cache."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_image_cache(cache: Dict[str, float]):
    """Saves LLM-extracted image amounts to persistent cache."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
