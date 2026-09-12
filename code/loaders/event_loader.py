"""
event_loader.py - Loads historical and scheduled financial events from CSV.
"""

import csv
from typing import Dict, List
from models import FinancialEvent
from utils import parse_date


def load_events(filepath: str) -> Dict[str, List[FinancialEvent]]:
    """
    Reads financial_events.csv and groups events by user_id.
    Handles blank amounts (from images) as None and falls back to event_date if settlement_date is blank.
    """
    events_by_user: Dict[str, List[FinancialEvent]] = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle optional blank amounts (filled via VLM in Step 2)
            amt_str = row["amount"].strip()
            amount = float(amt_str) if amt_str else None

            # Handle optional floor amount for reducible expenses
            min_amt_str = row.get("minimum_allowed_amount", "").strip()
            min_allowed = float(min_amt_str) if min_amt_str else None

            # Parse event and settlement dates
            event_date_val = parse_date(row["event_date"])
            settlement_date_val = parse_date(row["settlement_date"]) or event_date_val

            event = FinancialEvent(
                event_id=row["event_id"],
                user_id=row["user_id"],
                event_type=row["event_type"],
                description=row["description"],
                category=row["category"],
                direction=row["direction"],
                amount=amount,
                currency=row["currency"],
                event_date=event_date_val,
                settlement_date=settlement_date_val,
                status=row["status"],
                linked_event_id=row["linked_event_id"] if row.get("linked_event_id") else None,
                flexibility=row.get("flexibility", "fixed"),
                minimum_allowed_amount=min_allowed,
            )

            if event.user_id not in events_by_user:
                events_by_user[event.user_id] = []
            events_by_user[event.user_id].append(event)
    return events_by_user
