"""
capacity_calculator.py - Calculates safe payment amounts and earliest full payment dates.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from models import UserProfile, FinancialEvent
from .balance_forecast import simulate_cash_flow


def compute_amount_safe_to_pay(
    user_profile: UserProfile,
    events: List[FinancialEvent],
    exchange_rates: Dict[Tuple[str, str, str], float],
    request_date: date,
    requested_amount: float
) -> float:
    """
    Computes maximum amount safe to pay on request_date without spending changes.
    Uses binary search over [0, requested_amount].
    """
    low = 0.0
    high = requested_amount
    best_safe = 0.0

    for _ in range(20):
        mid = round((low + high) / 2.0, 2)
        is_safe, _, _, _ = simulate_cash_flow(
            user_profile, events, exchange_rates, [(request_date, mid)], set(), {}, request_date
        )
        if is_safe:
            best_safe = mid
            low = mid + 0.01
        else:
            high = mid - 0.01

    return min(best_safe, requested_amount)


def compute_earliest_date_for_full_payment(
    user_profile: UserProfile,
    events: List[FinancialEvent],
    exchange_rates: Dict[Tuple[str, str, str], float],
    request_date: date,
    requested_amount: float,
    max_forecast_days: int = 90
) -> Optional[date]:
    """
    Finds the earliest date in [request_date, request_date + 90] where single full payment is safe.
    Returns None if no date within forecast window is safe.
    """
    for day_offset in range(max_forecast_days + 1):
        candidate_date = request_date + timedelta(days=day_offset)
        is_safe, _, _, _ = simulate_cash_flow(
            user_profile, events, exchange_rates, [(candidate_date, requested_amount)], set(), {}, request_date
        )
        if is_safe:
            return candidate_date
    return None
