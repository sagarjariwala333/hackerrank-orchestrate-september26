"""
meta_loader.py - Loads supporting metadata: messages, image mappings, and exchange rates.
"""

import csv
from typing import Dict, List, Tuple
from models import Message


def load_messages(filepath: str) -> List[Message]:
    """Reads messages.csv containing notifications that modify financial facts."""
    messages = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            messages.append(
                Message(
                    message_id=row["message_id"],
                    user_id=row["user_id"],
                    request_id=row["request_id"] if row.get("request_id") else None,
                    related_event_id=row["related_event_id"] if row.get("related_event_id") else None,
                    sent_at=row["sent_at"],
                    source_type=row["source_type"],
                    message_text=row["message_text"],
                )
            )
    return messages


def load_images_map(filepath: str) -> Dict[str, str]:
    """Reads images.csv and returns a lookup dictionary: event_id -> image_id."""
    event_to_image = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("related_event_id") and row.get("image_id"):
                event_to_image[row["related_event_id"]] = row["image_id"]
    return event_to_image


def load_exchange_rates(filepath: str) -> Dict[Tuple[str, str, str], float]:
    """Reads exchange_rates.csv and returns a lookup dictionary: (rate_date_str, from_curr, to_curr) -> rate."""
    rates = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rates[(row["rate_date"].strip(), row["from_currency"].strip(), row["to_currency"].strip())] = float(row["rate"])
    return rates
