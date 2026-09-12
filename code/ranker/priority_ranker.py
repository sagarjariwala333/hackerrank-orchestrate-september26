"""
priority_ranker.py - Implements the strict 6-rule priority tie-breaker for ranking safe plans.
"""

from typing import Dict, List, Tuple
from models import UserProfile, FinancialEvent, PaymentOption, Request
from .option_evaluator import CandidatePlan, evaluate_candidate_plans
from .spending_adjuster import find_plans_with_spending_changes


def rank_key(plan: CandidatePlan, desired_date) -> Tuple[bool, bool, float, float, int, str]:
    """
    Ranks safe candidate plans according to strict hackathon §6.3 rules:
    1. Completes by desired_completion_date (True before False)
    2. Requires NO spending changes (True before False)
    3. Minimizes total amount paid (lowest total_cost)
    4. Starts payment earlier (earliest first_payment_date)
    5. Uses fewer payments (lowest num_payments)
    6. Lowest payment_option_id string (tie-breaker)
    """
    completes_on_time = plan.completion_date <= desired_date
    no_spending_changes = plan.spending_changes_str == "none"
    first_payment_days = (plan.first_payment_date - desired_date).days

    return (
        not completes_on_time,      # False (0) is preferred over True (1)
        not no_spending_changes,    # False (0) is preferred over True (1)
        plan.total_cost,            # Lower cost preferred
        first_payment_days,         # Earlier date preferred
        plan.num_payments,          # Fewer payments preferred
        plan.option_id              # Lowest option ID string
    )


def select_winning_plan(
    user_profile: UserProfile,
    events: List[FinancialEvent],
    rates: Dict[Tuple[str, str, str], float],
    req: Request,
    options: List[PaymentOption]
) -> CandidatePlan:
    """Evaluates all candidate plans and selects the top-ranked safe recommendation."""
    # 1. Evaluate clean candidate plans without spending changes
    plans = evaluate_candidate_plans(user_profile, events, rates, req, options)

    # 2. Filter to safe plans completing on or before desired_completion_date
    valid_on_time = [p for p in plans if p.completion_date <= req.desired_completion_date and p.status != "not_affordable"]

    if not valid_on_time:
        # Evaluate candidate plans with permitted flexible spending changes
        adj_plans = find_plans_with_spending_changes(user_profile, events, rates, req, options)
        plans.extend(adj_plans)
        valid_on_time = [p for p in plans if p.completion_date <= req.desired_completion_date and p.status != "not_affordable"]

    if valid_on_time:
        valid_on_time.sort(key=lambda p: rank_key(p, req.desired_completion_date))
        return valid_on_time[0]

    # If no plan completes on time, evaluate affordable_later or not_affordable
    if plans:
        plans.sort(key=lambda p: rank_key(p, req.desired_completion_date))
        best = plans[0]
        if best.completion_date > req.desired_completion_date:
            best.status = "affordable_later" if best.first_payment_date <= req.request_date + timedelta(days=90) else "not_affordable"
            best.method = "wait" if best.status == "affordable_later" else "not_recommended"
        return best

    # Fallback default when no plan is viable
    return CandidatePlan(
        method="not_recommended", status="not_affordable", plan_str="none",
        completion_date=req.request_date, total_cost=req.requested_amount,
        first_payment_date=req.request_date, num_payments=0, option_id="",
        spending_changes_str="none",
        explanation=f"Do not make this payment by {req.desired_completion_date}. No safe payment plan is available within minimum balance limits."
    )
