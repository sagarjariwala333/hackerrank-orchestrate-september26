"""
data_loader.py - Top-level facade exporting models, utils, and loader functions.
Includes an entry point execution test to verify all dataset files load cleanly.
"""

import sys
from pathlib import Path

# Ensure code directory is in sys.path for clean absolute/relative imports
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from models import UserProfile, FinancialEvent, PaymentOption, Request, Message
from utils import parse_date, parse_set, parse_list, convert_to_home_currency
from loaders import (
    load_profiles,
    load_events,
    load_payment_options,
    load_requests,
    load_messages,
    load_images_map,
    load_exchange_rates,
)

if __name__ == "__main__":
    # Sanity verification runner
    base_dir = code_dir.parent / "dataset"
    profiles = load_profiles(str(base_dir / "financial_profiles.csv"))
    requests = load_requests(str(base_dir / "requests.csv"))
    events = load_events(str(base_dir / "financial_events.csv"))
    options = load_payment_options(str(base_dir / "request_payment_options.csv"))
    rates = load_exchange_rates(str(base_dir / "exchange_rates.csv"))

    print(f"Loaded {len(profiles)} user profiles.")
    print(f"Loaded {len(requests)} requests.")
    print(f"Loaded events for {len(events)} users (total {sum(len(v) for v in events.values())} events).")
    print(f"Loaded payment options for {len(options)} requests.")
    print(f"Loaded {len(rates)} exchange rate entries.")
