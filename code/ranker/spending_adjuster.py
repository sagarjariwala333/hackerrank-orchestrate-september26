"""
spending_adjuster.py - Evaluates stoppable and reducible flexible expense cutbacks.
"""

from typing import Dict, List, Tuple
from models import UserProfile, FinancialEvent, PaymentOption, Request
from .option_evaluator import CandidatePlan, evaluate_candidate_plans


def find_plans_with_spending_changes(
    user_profile: UserProfile,
    events: List[FinancialEvent],
    rates: Dict[Tuple[str, str, str], float],
    req: Request,
    options: List[PaymentOption]
) -> List[CandidatePlan]:
    """
    Evaluates up to 3 permitted flexible expense cutbacks (stoppable / reducible).
    Only non-protected categories in user's stoppable / reducible lists are considered.
    """
    plans: List[CandidatePlan] = []
    stoppable_cats = user_profile.expense_categories_user_is_willing_to_stop or set()
    reducible_cats = user_profile.expense_categories_user_is_willing_to_reduce or set()
    protected_cats = user_profile.expense_categories_to_protect or set()

    # Find flexible events that can be stopped or reduced
    candidate_events = []
    for ev in events:
        if ev.direction == "debit" and ev.status in ("pending", "scheduled", "settled"):
            s_date = ev.settlement_date if ev.settlement_date else ev.event_date
            if s_date and s_date >= req.request_date:
                if ev.flexibility == "stoppable" and ev.category in stoppable_cats and ev.category not in protected_cats:
                    candidate_events.append((ev.event_id, "stop", 0.0))
                elif ev.flexibility == "reducible" and ev.category in reducible_cats and ev.category not in protected_cats:
                    min_allowed = ev.minimum_allowed_amount or 0.0
                    candidate_events.append((ev.event_id, "reduce_to", min_allowed))

    # Evaluate single spending change combinations
    for event_id, action_type, new_val in candidate_events[:3]:
        stopped_ids = {event_id} if action_type == "stop" else set()
        reduced_amts = {event_id: new_val} if action_type == "reduce_to" else {}
        change_str = f"stop:{event_id}" if action_type == "stop" else f"reduce_to:{event_id}:{new_val:g}"

        sub_plans = evaluate_candidate_plans(user_profile, events, rates, req, options, stopped_ids, reduced_amts)
        for p in sub_plans:
            if p.method in ("full_payment", "installments", "partial_payment"):
                p.spending_changes_str = change_str
                p.status = "affordable_with_plan"
                plans.append(p)

    return plans
