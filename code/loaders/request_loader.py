"""
request_loader.py - Loads user financial evaluation requests from CSV.
"""

import csv
from typing import List
from models import Request
from utils import parse_date


def load_requests(filepath: str) -> List[Request]:
    """
    Reads dataset/requests.csv and converts each row into a Request object.
    Parses request dates, desired completion dates, amounts, and partial payment flags.
    """
    requests = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            requests.append(
                Request(
                    request_id=row["request_id"],
                    user_id=row["user_id"],
                    request_date=parse_date(row["request_date"]),
                    request_type=row["request_type"],
                    requested_amount=float(row["requested_amount"]),
                    desired_completion_date=parse_date(row["desired_completion_date"]),
                    allows_partial_payment=row["allows_partial_payment"].strip().lower() == "true",
                    request_text=row["request_text"],
                )
            )
    return requests
