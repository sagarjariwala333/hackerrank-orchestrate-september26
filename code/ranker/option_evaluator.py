"""
option_evaluator.py - Evaluates full payment, seller installment options, partial payments, and wait options.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Tuple
from models import UserProfile, FinancialEvent, PaymentOption, Request
from simulator import simulate_cash_flow, compute_amount_safe_to_pay, compute_earliest_date_for_full_payment


def fmt_num(val: float) -> str:
    """Formats float into a clean decimal string without scientific notation."""
    return f"{val:.2f}".rstrip("0").rstrip(".")


@dataclass
class CandidatePlan:
    method: str
    status: str
    plan_str: str
    completion_date: date
    total_cost: float
    first_payment_date: date
    num_payments: int
    option_id: str
    spending_changes_str: str
    explanation: str


def build_installment_schedule(opt: PaymentOption) -> List[Tuple[date, float]]:
    """Builds list of (date, amount) tuples for an installment option offer."""
    freq = opt.payment_frequency_days or 30
    return [(opt.first_payment_date + timedelta(days=i * freq), opt.payment_amount) for i in range(opt.number_of_payments)]


def evaluate_candidate_plans(
    user_profile: UserProfile, events: List[FinancialEvent], rates: Dict[Tuple[str, str, str], float],
    req: Request, options: List[PaymentOption], stopped_ids: set = None, reduced_amts: dict = None
) -> List[CandidatePlan]:
    """Generates and tests all valid payment options (Full, Installments, Partial, Wait)."""
    stopped_ids, reduced_amts = stopped_ids or set(), reduced_amts or {}
    plans: List[CandidatePlan] = []
    allowed = user_profile.payment_methods_user_will_consider or {"full_payment", "partial_payment", "installments", "wait"}
    curr = user_profile.home_currency

    # 1. Full Payment
    if "full_payment" in allowed:
        is_safe, _, _, _ = simulate_cash_flow(user_profile, events, rates, [(req.request_date, req.requested_amount)], stopped_ids, reduced_amts, req.request_date)
        if is_safe:
            plans.append(CandidatePlan(
                "full_payment", "affordable_now" if not stopped_ids else "affordable_with_plan", f"{req.request_date}:{fmt_num(req.requested_amount)}",
                req.request_date, req.requested_amount, req.request_date, 1, "", "none" if not stopped_ids else "spending_change",
                f"Pay {curr} {fmt_num(req.requested_amount)} in full on {req.request_date}."
            ))

    # 2. Installments
    if "installments" in allowed and options:
        max_months = user_profile.max_installment_months or 999
        for opt in options:
            if opt.number_of_payments <= max_months:
                schedule = build_installment_schedule(opt)
                is_safe, _, _, _ = simulate_cash_flow(user_profile, events, rates, schedule, stopped_ids, reduced_amts, req.request_date)
                if is_safe:
                    plans.append(CandidatePlan(
                        "installments", "affordable_with_plan", "|".join(f"{d}:{fmt_num(amt)}" for d, amt in schedule), schedule[-1][0],
                        opt.total_payable_amount, opt.first_payment_date, opt.number_of_payments, opt.payment_option_id,
                        "none" if not stopped_ids else "spending_change", f"Use {opt.number_of_payments} installments of {curr} {fmt_num(opt.payment_amount)}."
                    ))

    # 3. Partial Payment
    if "partial_payment" in allowed and req.allows_partial_payment:
        safe_today = compute_amount_safe_to_pay(user_profile, events, rates, req.request_date, req.requested_amount)
        if 0 < safe_today < req.requested_amount:
            earliest_d = compute_earliest_date_for_full_payment(user_profile, events, rates, req.request_date, req.requested_amount - safe_today)
            if earliest_d and earliest_d <= req.desired_completion_date:
                remainder = round(req.requested_amount - safe_today, 2)
                plans.append(CandidatePlan(
                    "partial_payment", "affordable_with_plan", f"{req.request_date}:{fmt_num(safe_today)}|{earliest_d}:{fmt_num(remainder)}", earliest_d,
                    req.requested_amount, req.request_date, 2, "", "none" if not stopped_ids else "spending_change",
                    f"Pay {curr} {fmt_num(safe_today)} today and remainder on {earliest_d}."
                ))

    # 4. Wait Option
    earliest_full = compute_earliest_date_for_full_payment(user_profile, events, rates, req.request_date, req.requested_amount)
    if earliest_full and earliest_full > req.request_date:
        on_time = earliest_full <= req.desired_completion_date
        plans.append(CandidatePlan(
            "wait", "affordable_later" if on_time else "not_affordable", f"{earliest_full}:{fmt_num(req.requested_amount)}", earliest_full,
            req.requested_amount, earliest_full, 1, "", "none", f"Wait until {earliest_full}, then pay {curr} {fmt_num(req.requested_amount)} in full."
        ))

    return plans
