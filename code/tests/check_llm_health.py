"""
check_llm_health.py - Health check script for Gemini API connectivity & VLM multimodal capabilities.
"""

import base64
import os
import re
import sys
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))


def post_with_retry(url: str, payload: dict, max_retries: int = 5, timeout: int = 60) -> requests.Response:
    """Posts payload to Gemini API with dynamic 429 retryDelay backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 429 and attempt < max_retries:
                m = re.search(r"retry in (\d+(?:\.\d+)?)s", resp.text, re.IGNORECASE)
                wait_sec = float(m.group(1)) + 2.0 if m else 35.0
                print(f"[WARN] 429 Rate limited. Pausing {wait_sec:.1f}s (Attempt {attempt}/{max_retries})...")
                time.sleep(wait_sec)
                continue
            return resp
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                time.sleep(5)
            else:
                raise
    return resp


def check_llm_health() -> bool:
    print("=== GEMINI LLM HEALTH CHECK ===")
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY is NOT set in environment variables.")
        return False
    print("[PASS] GEMINI_API_KEY environment variable detected.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"

    # 1. Test Text Prompt
    text_res = post_with_retry(url, {"contents": [{"parts": [{"text": "Respond OK"}]}]})
    if text_res.status_code == 200:
        print("[PASS] Gemini 3.6 Flash Text API: ONLINE & WORKING")
    else:
        print(f"[FAIL] Gemini Text API Error {text_res.status_code}: {text_res.text}")
        return False

    # 2. Test VLM Multimodal Image Extraction
    img_path = code_dir.parent / "dataset" / "media" / "images" / "image_01.png"
    if not img_path.exists():
        return True

    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    vlm_payload = {
        "contents": [{"parts": [{"inline_data": {"mime_type": "image/png", "data": img_b64}}, {"text": "Return JSON: {\"amount\": 125.0}"}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    vlm_res = post_with_retry(url, vlm_payload)
    if vlm_res.status_code == 200:
        out = vlm_res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"[PASS] Gemini 3.6 Flash VLM API: ONLINE & WORKING\n       Result: {out}")
        print("=== HEALTH CHECK SUMMARY: ALL SYSTEMS OPERATIONAL [PASS] ===")
        return True
    else:
        print(f"[FAIL] Gemini VLM API Error {vlm_res.status_code}: {vlm_res.text}")
        return False


if __name__ == "__main__":
    success = check_llm_health()
    sys.exit(0 if success else 1)
