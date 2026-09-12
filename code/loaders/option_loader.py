"""
option_loader.py - Loads merchant and provider payment options from CSV.
"""

import csv
from typing import Dict, List
from models import PaymentOption
from utils import parse_date


def load_payment_options(filepath: str) -> Dict[str, List[PaymentOption]]:
    """
    Reads request_payment_options.csv and maps request_id -> List[PaymentOption].
    Parses installment payments, frequencies, financing fees, and total payable amounts.
    """
    options_by_request: Dict[str, List[PaymentOption]] = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            freq_str = row.get("payment_frequency_days", "").strip()
            opt = PaymentOption(
                payment_option_id=row["payment_option_id"],
                request_id=row["request_id"],
                payment_method=row["payment_method"],
                payment_amount=float(row["payment_amount"]),
                number_of_payments=int(row["number_of_payments"]),
                first_payment_date=parse_date(row["first_payment_date"]),
                payment_frequency_days=int(freq_str) if freq_str else None,
                financing_fee=float(row.get("financing_fee", 0) or 0),
                total_payable_amount=float(row["total_payable_amount"]),
            )
            if opt.request_id not in options_by_request:
                options_by_request[opt.request_id] = []
            options_by_request[opt.request_id].append(opt)
    return options_by_request
