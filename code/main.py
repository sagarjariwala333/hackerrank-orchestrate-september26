"""
main.py - Main end-to-end pipeline runner for Buy or Wait AI Financial Agent.
Executes Step 1 (Loader), Step 2 (Fact Extractor), Step 3 (Simulator), Step 4 (Ranker),
and exports final predictions to output.csv and token usage report to evaluation/usage_report.md.
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
from ranker import select_winning_plan
from simulator import compute_amount_safe_to_pay, compute_earliest_date_for_full_payment
from token_tracker import tracker

load_dotenv()


def main():
    print("=== BUY OR WAIT? AI FINANCIAL AGENT PIPELINE ===")
    base_dir = code_dir.parent / "dataset"
    media_dir = base_dir / "media" / "images"

    # Step 1: Load Datasets
    print("\n[Step 1] Loading raw datasets...")
    profiles = load_profiles(str(base_dir / "financial_profiles.csv"))
    requests = load_requests(str(base_dir / "requests.csv"))
    events = load_events(str(base_dir / "financial_events.csv"))
    options = load_payment_options(str(base_dir / "request_payment_options.csv"))
    rates = load_exchange_rates(str(base_dir / "exchange_rates.csv"))
    messages = load_messages(str(base_dir / "messages.csv"))
    images = load_images_map(str(base_dir / "images.csv"))
    print(f"Loaded {len(profiles)} profiles, {len(requests)} requests, {sum(len(v) for v in events.values())} events.")

    # Step 2: Reconcile Facts
    print("\n[Step 2] Reconciling financial facts (VLM images & LLM messages)...")
    resolved_img, mod_msg = reconcile_financial_facts(events, messages, images, media_dir)
    print(f"Resolved {resolved_img} image amounts via VLM. Applied {mod_msg} message updates.")

    # Step 3 & 4: Simulate & Rank Decisions
    print("\n[Step 3 & 4] Simulating cash flow & selecting safe payment plans across 250 requests...")
    output_rows = []

    for req in requests:
        prof = profiles[req.user_id]
        user_events = events[req.user_id]
        req_options = options.get(req.request_id, [])

        safe_amt = compute_amount_safe_to_pay(prof, user_events, rates, req.request_date, req.requested_amount)
        earliest_d = compute_earliest_date_for_full_payment(prof, user_events, rates, req.request_date, req.requested_amount)
        winning_plan = select_winning_plan(prof, user_events, rates, req, req_options)

        output_rows.append({
            "request_id": req.request_id,
            "amount_safe_to_pay": f"{safe_amt:.2f}".rstrip("0").rstrip("."),
            "affordability_status": winning_plan.status,
            "recommended_payment_method": winning_plan.method,
            "payment_plan": winning_plan.plan_str,
            "earliest_date_for_full_payment": str(earliest_d) if earliest_d else "",
            "spending_changes_needed": winning_plan.spending_changes_str,
            "decision_explanation": winning_plan.explanation,
        })

    # Step 5: Export output.csv complying with §6.2 contract
    out_csv = base_dir.parent / "output.csv"
    fieldnames = [
        "request_id", "amount_safe_to_pay", "affordability_status", "recommended_payment_method",
        "payment_plan", "earliest_date_for_full_payment", "spending_changes_needed", "decision_explanation"
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"\n[Export] Successfully wrote {len(output_rows)} predictions to '{out_csv}'.")

    # Generate evaluation/usage_report.md complying with §6.5 contract
    report_path = code_dir / "evaluation" / "usage_report.md"
    tracker.write_usage_report(report_path)
    print(f"[Token Report] Generated usage report at '{report_path}'. Total Cost: ${tracker.get_total_cost():.6f}")

    print("\n=== FULL BUY OR WAIT SOLUTION PIPELINE EXECUTED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
