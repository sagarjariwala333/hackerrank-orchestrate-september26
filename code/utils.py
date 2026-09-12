"""
utils.py - Helper utilities for date parsing, string sanitization, and FX conversion.
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple
from dotenv import load_dotenv

# Automatically load environment variables from local .env file
load_dotenv()


def parse_date(date_str: str) -> Optional[date]:
    """Parses a YYYY-MM-DD date string into a datetime.date object safely."""
    if not date_str or not date_str.strip():
        return None
    return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()


def parse_set(pipe_str: str) -> Set[str]:
    """Splits a pipe-delimited string (e.g. 'rent|groceries') into a set of clean strings."""
    if not pipe_str or not pipe_str.strip():
        return set()
    return {item.strip() for item in pipe_str.split("|") if item.strip()}


def parse_list(pipe_str: str) -> List[str]:
    """Splits a pipe-delimited string into an ordered list of clean strings."""
    if not pipe_str or not pipe_str.strip():
        return []
    return [item.strip() for item in pipe_str.split("|") if item.strip()]


def convert_to_home_currency(
    amount: float,
    from_curr: str,
    to_curr: str,
    event_date_str: str,
    exchange_rates: Dict[Tuple[str, str, str], float],
) -> float:
    """Converts a foreign transaction amount to user's home_currency using dated exchange rates."""
    if from_curr == to_curr or amount == 0:
        return amount

    # Direct date lookup
    key = (event_date_str, from_curr, to_curr)
    if key in exchange_rates:
        return amount * exchange_rates[key]

    # Fallback to closest preceding rate date if exact date row is absent
    available_dates = [d for (d, fc, tc) in exchange_rates.keys() if fc == from_curr and tc == to_curr]
    if available_dates:
        available_dates.sort()
        closest_date = available_dates[0]
        for d in available_dates:
            if d <= event_date_str:
                closest_date = d
        return amount * exchange_rates[(closest_date, from_curr, to_curr)]

    return amount
