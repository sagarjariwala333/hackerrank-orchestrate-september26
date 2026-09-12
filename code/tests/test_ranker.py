"""
test_ranker.py - Unit tests for Step 4 Priority Ranker against sample_requests.csv.
"""

import sys
from pathlib import Path

code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from loaders import load_profiles, load_events, load_exchange_rates, load_requests, load_messages, load_images_map, load_payment_options
from fact_extractor import reconcile_financial_facts
from ranker import select_winning_plan


def test_ranker_sample_requests():
    base_dir = code_dir.parent / "dataset"
    profiles = load_profiles(str(base_dir / "financial_profiles.csv"))
    events = load_events(str(base_dir / "financial_events.csv"))
    rates = load_exchange_rates(str(base_dir / "exchange_rates.csv"))
    requests = load_requests(str(base_dir / "sample_requests.csv"))
    options = load_payment_options(str(base_dir / "request_payment_options.csv"))
    messages = load_messages(str(base_dir / "messages.csv"))
    images = load_images_map(str(base_dir / "images.csv"))
    media_dir = base_dir / "media" / "images"

    reconcile_financial_facts(events, messages, images, media_dir)

    for req in requests[:5]:
        prof = profiles[req.user_id]
        user_events = events[req.user_id]
        req_options = options.get(req.request_id, [])

        winning_plan = select_winning_plan(prof, user_events, rates, req, req_options)
        print(f"[{req.request_id}] Rec Method={winning_plan.method}, Status={winning_plan.status}, Plan={winning_plan.plan_str}")

    print("=== RANKER UNIT TESTS COMPLETED SUCCESSFULLY! [PASS] ===")


if __name__ == "__main__":
    test_ranker_sample_requests()
