"""
message_processor.py - Full LLM batch processor with persistent message_cache.json caching using Gemini 3.6 Flash.
Processes uncached messages in serial batches of 25 with 2s delay and Gemini 3.6 Flash structured output.
"""

import json
import os
import re
import time
from typing import Dict, List
import requests
from models import FinancialEvent, Message
from token_tracker import tracker
from .message_cache_handler import load_message_cache, save_message_cache


def call_llm_for_message_batch(batch: List[Message], api_key: str, cache: Dict[str, List[dict]]) -> List[dict]:
    """Calls Gemini 3.6 Flash for uncached messages and saves updates to cache."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    summaries = [{"id": m.message_id, "user_id": m.user_id, "rel_event": m.related_event_id, "text": m.message_text} for m in batch]
    prompt = 'Extract updates: [{"message_id": str, "user_id": str, "action": "rent_increase_pct"|"cancel_event"|"unrealize_bonus"|"update_salary", "event_id": str|null, "category": str|null, "value": float|null}].'
    raw_in = f"Prompt: {prompt}\nMessages: {json.dumps(summaries)}"
    payload = {"contents": [{"parts": [{"text": raw_in}]}], "generationConfig": {"response_mime_type": "application/json"}}

    for attempt in range(1, 6):
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                u = resp.json().get("usageMetadata", {})
                tracker.record_call("gemini-3.6-flash", u.get("promptTokenCount", 1500), u.get("candidatesTokenCount", 200), f"Msg LLM ({len(batch)} msgs)", "Parsed", raw_in, raw_text)
                results = json.loads(raw_text)
                for m in batch:
                    cache[m.message_id] = [r for r in results if r.get("message_id") == m.message_id]
                save_message_cache(cache)
                return results

            elif resp.status_code == 429:
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", resp.text, re.IGNORECASE)
                time.sleep(float(match.group(1)) + 2.0 if match else 35.0)
            else:
                time.sleep(3)
        except Exception:
            time.sleep(4)
    raise RuntimeError("LLM Message extraction failed after retries. Pipeline stopped.")


def apply_llm_updates_to_events(events_by_user: Dict[str, List[FinancialEvent]], updates: List[dict]) -> int:
    """Applies extracted LLM updates to user financial events."""
    modified = 0
    for item in updates:
        uid = item.get("user_id")
        if not uid or uid not in events_by_user:
            continue
        act, rel_id, cat, val = item.get("action"), item.get("event_id"), item.get("category"), item.get("value")
        for ev in events_by_user[uid]:
            if act == "rent_increase_pct" and ev.category == "rent" and val:
                ev.amount = round((ev.amount or 0.0) * (1.0 + (val / 100.0 if val > 1 else val)), 2)
                modified += 1
            elif act == "cancel_event" and ((rel_id and ev.event_id == rel_id) or (cat and ev.category == cat)):
                ev.status = "cancelled"
                modified += 1
            elif act == "unrealize_bonus" and ev.event_type in ("income", "bonus") and ev.status != "settled":
                ev.status = "unrealized"
                modified += 1
            elif act == "update_salary" and ev.category == "salary" and val:
                ev.amount = float(val)
                modified += 1
    return modified


def apply_message_updates_in_batches(events_by_user: Dict[str, List[FinancialEvent]], messages: List[Message], batch_size: int = 25, batch_delay_sec: float = 2.0) -> int:
    """Processes messages in serial LLM batches with persistent message_cache.json caching."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set. Pipeline stopped.")

    cache = load_message_cache()
    cached_updates = [r for m in messages if m.message_id in cache for r in cache[m.message_id]]
    uncached_msgs = [m for m in messages if m.message_id not in cache]

    modified_count = apply_llm_updates_to_events(events_by_user, cached_updates)
    if cached_updates:
        print(f"[MSG CACHE] Reused {len(cached_updates)} cached LLM message updates.")

    tot_batches = (len(uncached_msgs) + batch_size - 1) // batch_size if uncached_msgs else 0
    if tot_batches > 0:
        print(f"\n--- Processing {len(uncached_msgs)} Uncached Messages in {tot_batches} Serial Batches ({batch_size} msg/batch) ---")

    for b in range(tot_batches):
        batch = uncached_msgs[b * batch_size : (b + 1) * batch_size]
        print(f"[MSG LLM BATCH] Running Batch {b + 1}/{tot_batches} ({len(batch)} messages)...")
        updates = call_llm_for_message_batch(batch, api_key, cache)
        modified_count += apply_llm_updates_to_events(events_by_user, updates)
        if b < tot_batches - 1:
            time.sleep(batch_delay_sec)

    return modified_count
