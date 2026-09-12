"""
main.py - Main entry point runner for Buy or Wait AI Financial Agent.
Integrates Step 1 (Data Loader), Step 2 (Fact Extractor), and Step 3 (90-Day Simulator).
Exports code/evaluation/simulation_summary.csv for Step 3 inspection.
"""

import csv
import sys
from pathlib import Path

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
from simulator import compute_amount_safe_to_pay, compute_earliest_date_for_full_payment
from token_tracker import tracker

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
    print(f"Loaded {len(profiles)} profiles, {len(requests)} requests, {sum(len(v) for v in events.values())} events.")

    # Step 2: Reconcile Financial Facts
    print("\n[Step 2] Reconciling financial facts (VLM images & LLM messages)...")
    resolved_img, mod_msg = reconcile_financial_facts(events, messages, images, media_dir)
    print(f"Resolved {resolved_img} image amounts via VLM. Applied {mod_msg} message updates.")

    # Step 3: Run 90-Day Cash Flow Simulator across requests
    print("\n[Step 3] Running 90-day cash flow simulation across evaluation requests...")
    sim_rows = []
    for req in requests:
        prof = profiles[req.user_id]
        user_events = events[req.user_id]
        safe_amt = compute_amount_safe_to_pay(prof, user_events, rates, req.request_date, req.requested_amount)
        earliest_d = compute_earliest_date_for_full_payment(prof, user_events, rates, req.request_date, req.requested_amount)
        sim_rows.append({
            "request_id": req.request_id,
            "user_id": req.user_id,
            "request_date": str(req.request_date),
            "requested_amount": req.requested_amount,
            "amount_safe_to_pay": safe_amt,
            "earliest_date_for_full_payment": str(earliest_d) if earliest_d else "none"
        })

    # Export simulation_summary.csv for inspection
    out_csv = code_dir / "evaluation" / "simulation_summary.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(sim_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sim_rows)

    print(f"Simulated 90-day cash flow for {len(sim_rows)} evaluation requests.")
    print(f"[Export] Saved intermediate simulation summary to '{out_csv}'.")

    # Write Token Usage Report
    report_path = code_dir / "evaluation" / "usage_report.md"
    tracker.write_usage_report(report_path)
    print(f"\n[Token Report] Saved usage report to '{report_path}'. Total Cost: ${tracker.get_total_cost():.6f}")

    print("\n=== STEP 1, STEP 2 & STEP 3 PIPELINE STAGES COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
