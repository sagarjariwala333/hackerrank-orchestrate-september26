"""
test_simulator.py - Unit test suite for 90-Day Cash Flow Simulator.
"""

import sys
from pathlib import Path

# Ensure code directory is in sys.path
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from loaders import load_profiles, load_events, load_exchange_rates, load_requests, load_messages, load_images_map
from fact_extractor import reconcile_financial_facts
from simulator import (
    simulate_cash_flow,
    compute_amount_safe_to_pay,
    compute_earliest_date_for_full_payment,
)


def test_simulator_basic():
    base_dir = code_dir.parent / "dataset"
    profiles = load_profiles(str(base_dir / "financial_profiles.csv"))
    events = load_events(str(base_dir / "financial_events.csv"))
    rates = load_exchange_rates(str(base_dir / "exchange_rates.csv"))
    requests = load_requests(str(base_dir / "requests.csv"))
    messages = load_messages(str(base_dir / "messages.csv"))
    images = load_images_map(str(base_dir / "images.csv"))
    media_dir = base_dir / "media" / "images"

    # Reconciles events in-place
    reconcile_financial_facts(events, messages, images, media_dir)

    # Pick request_26 from dataset/requests.csv
    req = requests[0]
    prof = profiles[req.user_id]
    user_events = events[req.user_id]

    safe_amt = compute_amount_safe_to_pay(prof, user_events, rates, req.request_date, req.requested_amount)
    earliest_d = compute_earliest_date_for_full_payment(prof, user_events, rates, req.request_date, req.requested_amount)

    print(f"[TEST] Request {req.request_id} (user {req.user_id}): Safe Amount={safe_amt}, Earliest Date={earliest_d}")
    assert safe_amt >= 0, "Safe amount must be non-negative"
    print("=== SIMULATOR UNIT TESTS PASSED SUCCESSFULLY! [PASS] ===")


if __name__ == "__main__":
    test_simulator_basic()
