"""
test_fact_extractor.py - Unit tests verifying strict LLM calling & error halting.
"""

import os
import sys
from pathlib import Path

# Ensure code directory is in sys.path
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from fact_extractor import reconcile_financial_facts
from loaders import load_events, load_images_map, load_messages


def test_strict_llm_error_halting():
    """Verify that pipeline halts immediately with RuntimeError if GEMINI_API_KEY is missing."""
    base_dir = code_dir.parent / "dataset"
    events = load_events(str(base_dir / "financial_events.csv"))
    images = load_images_map(str(base_dir / "images.csv"))
    messages = load_messages(str(base_dir / "messages.csv"))
    media = base_dir / "media" / "images"

    # Ensure API key is cleared to test strict halting
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("GOOGLE_API_KEY", None)

    try:
        reconcile_financial_facts(events, messages, images, media)
        assert False, "Pipeline should have raised RuntimeError due to missing GEMINI_API_KEY!"
    except RuntimeError as err:
        assert "GEMINI_API_KEY" in str(err), f"Expected GEMINI_API_KEY error message, got: {err}"
        print(f"Strict LLM Error Halting Test Passed: Verified pipeline stops with RuntimeError -> '{err}'")


if __name__ == "__main__":
    print("Running Strict LLM Edge Case Tests for Step 2...")
    test_strict_llm_error_halting()
    print("ALL STEP 2 STRICT LLM HALTING TESTS PASSED SUCCESSFULLY! [PASS]")
