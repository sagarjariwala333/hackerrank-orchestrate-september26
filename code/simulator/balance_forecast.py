"""
balance_forecast.py - 90-day cash flow simulation engine.
Simulates daily balance trajectory and enforces minimum required buffer.
"""

from datetime import date, timedelta
from typing import Dict, List, Tuple
from models import UserProfile, FinancialEvent
from utils import convert_to_home_currency


def simulate_cash_flow(
    user_profile: UserProfile,
    events: List[FinancialEvent],
    exchange_rates: Dict[Tuple[str, str, str], float],
    payment_schedule: List[Tuple[date, float]],
    stopped_event_ids: set,
    reduced_event_amounts: Dict[str, float],
    request_date: date,
    forecast_days: int = 90
) -> Tuple[bool, float, float, Dict[date, float]]:
    """
    Simulates daily balance trajectory from request_date to request_date + forecast_days.
    Returns: (is_safe, minimum_balance_seen, final_balance, daily_balance_map)
    """
    current_balance = user_profile.current_available_balance
    min_required = user_profile.minimum_balance_to_keep
    end_date = request_date + timedelta(days=forecast_days)

    # 1. Aggregate daily net cash flows from reconciled financial events
    daily_deltas: Dict[date, float] = {}

    for ev in events:
        if ev.event_id in stopped_event_ids:
            continue
        if ev.status in ("cancelled", "failed", "unrealized"):
            continue

        # Event date filtering: only future settlement dates relative to request_date
        s_date = ev.settlement_date if ev.settlement_date else ev.event_date
        if not s_date or s_date < request_date or s_date > end_date:
            continue

        # Cash state rules per §6.3: pending debits reserved, pending credits ignored
        if ev.direction == "debit":
            if ev.status not in ("pending", "scheduled", "settled"):
                continue
            raw_amt = reduced_event_amounts.get(ev.event_id, ev.amount or 0.0)
            conv_amt = convert_to_home_currency(
                raw_amt, ev.currency, user_profile.home_currency, str(s_date), exchange_rates
            )
            daily_deltas[s_date] = daily_deltas.get(s_date, 0.0) - conv_amt

        elif ev.direction == "credit":
            # Count confirmed salary on settlement date; ignore unconfirmed credits/bonuses
            if ev.status == "settled" or (ev.status == "scheduled" and ev.event_type == "salary"):
                raw_amt = ev.amount or 0.0
                conv_amt = convert_to_home_currency(
                    raw_amt, ev.currency, user_profile.home_currency, str(s_date), exchange_rates
                )
                daily_deltas[s_date] = daily_deltas.get(s_date, 0.0) + conv_amt

    # 2. Subtract candidate payment schedule
    for p_date, p_amt in payment_schedule:
        if request_date <= p_date <= end_date:
            daily_deltas[p_date] = daily_deltas.get(p_date, 0.0) - p_amt

    # 3. Simulate day-by-day balance trajectory
    daily_balances: Dict[date, float] = {}
    min_balance_seen = current_balance
    bal = current_balance

    for day_offset in range(forecast_days + 1):
        cur_d = request_date + timedelta(days=day_offset)
        if cur_d in daily_deltas:
            bal += daily_deltas[cur_d]
        daily_balances[cur_d] = bal
        if bal < min_balance_seen:
            min_balance_seen = bal

    is_safe = min_balance_seen >= min_required
    return is_safe, min_balance_seen, bal, daily_balances
