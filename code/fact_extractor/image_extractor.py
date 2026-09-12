"""
image_extractor.py - Serial batch processor for image VLM amount extraction using Gemini 3.6 Flash.
Processes 3 images per batch serially with a 2-second delay between batches.
"""

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple
import requests
from models import FinancialEvent
from token_tracker import tracker
from .image_cache_handler import load_image_cache, save_image_cache


def call_gemini_vlm_for_image(image_path: Path, api_key: str, cache: Dict[str, float]) -> float:
    """Calls Gemini VLM to extract monetary amount. Uses cache if previously extracted."""
    if image_path.name in cache:
        print(f"[VLM CACHE] {image_path.name} -> Reused LLM Amount: {cache[image_path.name]}")
        return cache[image_path.name]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = "Extract the exact net monetary amount payable or credited. Return JSON: {\"amount\": 1250.0}."
    payload = {"contents": [{"parts": [{"inline_data": {"mime_type": "image/png", "data": img_b64}}, {"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}

    last_error = None
    for attempt in range(1, 6):
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                res_json = resp.json()
                raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                amt = float(json.loads(raw_text)["amount"])
                u = res_json.get("usageMetadata", {})
                in_t, out_t = u.get("promptTokenCount", 1130), u.get("candidatesTokenCount", 18)

                tracker.record_call("gemini-3.6-flash", in_t, out_t, f"VLM Extraction {image_path.name}", f"Amount: {amt}", f"[Image: {image_path.name}]\n{prompt}", raw_text)
                cache[image_path.name] = amt
                save_image_cache(cache)
                print(f"[VLM LOG] {image_path.name} -> Extracted: {amt} (Tokens: {in_t} in / {out_t} out)")
                return amt

            elif resp.status_code == 429:
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", resp.text, re.IGNORECASE)
                wait_sec = float(match.group(1)) + 2.0 if match else 35.0
                print(f"[VLM RATE LIMIT] 429 on {image_path.name}. Pausing {wait_sec:.1f}s (Attempt {attempt}/5)...")
                time.sleep(wait_sec)
                last_error = f"Rate limited: {resp.text}"
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text}"
                time.sleep(3)
        except Exception as err:
            last_error = str(err)
            time.sleep(4)

    raise RuntimeError(f"VLM Extraction failed for image '{image_path.name}': {last_error}. Pipeline stopped.")


def resolve_image_amounts_in_batches(events_by_user: Dict[str, List[FinancialEvent]], images_map: Dict[str, str], media_dir: Path, batch_size: int = 3, batch_delay_sec: float = 2.0) -> int:
    """Groups missing image events into serial batches of 3 images with 2s delay between batches."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set. Pipeline stopped.")

    cache, targets = load_image_cache(), []
    for user_events in events_by_user.values():
        for ev in user_events:
            if ev.amount is None and ev.event_id in images_map:
                p = media_dir / f"{images_map[ev.event_id]}.png"
                if not p.exists():
                    raise RuntimeError(f"Required image file missing: '{p}'.")
                targets.append((ev, p))

    tot_batches = (len(targets) + batch_size - 1) // batch_size if targets else 0
    resolved = 0
    for b in range(tot_batches):
        batch = targets[b * batch_size : (b + 1) * batch_size]
        print(f"\n--- Image Batch {b + 1}/{tot_batches} ({len(batch)} images) ---")
        for ev, p in batch:
            ev.amount = call_gemini_vlm_for_image(p, api_key, cache)
            resolved += 1
        if b < tot_batches - 1:
            print(f"[BATCH DELAY] Waiting {batch_delay_sec}s before next image batch...")
            time.sleep(batch_delay_sec)

    return resolved
