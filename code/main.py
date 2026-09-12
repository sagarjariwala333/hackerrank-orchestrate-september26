"""
main.py - Main entry point runner for Buy or Wait AI Financial Agent.
Integrates Step 1 (Data Loader) and Step 2 (Fact Extractor: VLM image amounts & message rules).
Writes evaluation/usage_report.md complying with §6.5 contract.
"""

import sys
from pathlib import Path

# Ensure code directory is in sys.path
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import load_dotenv
from data_loader import (
    load_events,
    load_exchange_rates,
    load_images_map,
    load_messages,
    load_payment_options,
    load_profiles,
    load_requests,
)
from fact_extractor import reconcile_financial_facts
from token_tracker import tracker

# Load local .env environment variables automatically
load_dotenv()


def main():
    print("=== BUY OR WAIT? AI FINANCIAL AGENT PIPELINE ===")

    base_dir = code_dir.parent / "dataset"
    media_dir = base_dir / "media" / "images"

    # Step 1: Load Raw Datasets
    print("\n[Step 1] Loading financial datasets...")
    profiles = load_profiles(str(base_dir / "financial_profiles.csv"))
    requests = load_requests(str(base_dir / "requests.csv"))
    events = load_events(str(base_dir / "financial_events.csv"))
    options = load_payment_options(str(base_dir / "request_payment_options.csv"))
    rates = load_exchange_rates(str(base_dir / "exchange_rates.csv"))
    messages = load_messages(str(base_dir / "messages.csv"))
    images = load_images_map(str(base_dir / "images.csv"))

    print(f"Loaded {len(profiles)} user profiles.")
    print(f"Loaded {len(requests)} evaluation requests.")
    print(f"Loaded {sum(len(v) for v in events.values())} financial events across {len(events)} users.")

    # Step 2: Reconcile Financial Facts (Images & Messages)
    print("\n[Step 2] Reconciling financial facts (VLM image extraction & message updates)...")
    resolved_img, mod_msg = reconcile_financial_facts(events, messages, images, media_dir)
    print(f"Resolved {resolved_img} missing image amounts via VLM.")
    print(f"Updated {mod_msg} financial event entries from message rules.")

    # Write Token Usage Report
    report_path = code_dir / "evaluation" / "usage_report.md"
    tracker.write_usage_report(report_path)
    print(f"\n[Token Report] Generated usage report at '{report_path}'. Total Cost: ${tracker.get_total_cost():.6f}")

    print("\n=== STEP 1 & STEP 2 PIPELINE STAGES COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
