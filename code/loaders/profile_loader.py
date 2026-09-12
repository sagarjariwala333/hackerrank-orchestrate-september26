"""
profile_loader.py - Loads and parses user financial profiles from CSV.
"""

import csv
from typing import Dict
from models import UserProfile
from utils import parse_list, parse_set


def load_profiles(filepath: str) -> Dict[str, UserProfile]:
    """
    Reads financial_profiles.csv and constructs a map of user_id -> UserProfile.
    Converts pipe-separated categories into Python sets for fast membership testing.
    """
    profiles = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            max_inst = row["max_installment_months"].strip()
            profiles[row["user_id"]] = UserProfile(
                user_id=row["user_id"],
                home_currency=row["home_currency"],
                current_available_balance=float(row["current_available_balance"]),
                minimum_balance_to_keep=float(row["minimum_balance_to_keep"]),
                financial_priorities=parse_list(row.get("financial_priorities", "")),
                expense_categories_to_protect=parse_set(row.get("expense_categories_to_protect", "")),
                expense_categories_user_is_willing_to_reduce=parse_set(row.get("expense_categories_user_is_willing_to_reduce", "")),
                expense_categories_user_is_willing_to_stop=parse_set(row.get("expense_categories_user_is_willing_to_stop", "")),
                payment_methods_user_will_consider=parse_set(row.get("payment_methods_user_will_consider", "")),
                max_installment_months=int(max_inst) if max_inst else None,
            )
    return profiles
