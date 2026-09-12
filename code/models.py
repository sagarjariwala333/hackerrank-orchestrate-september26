"""
models.py - Core domain entities and dataclasses for the Buy or Wait financial agent.
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Set


@dataclass
class UserProfile:
    """User preferences, currency, balance, emergency buffer, and spending flexibility rules."""
    user_id: str
    home_currency: str  # Base currency (USD, EUR, INR, ZAR, IDR)
    current_available_balance: float  # Liquid balance on request_date
    minimum_balance_to_keep: float  # Safety buffer invariant
    financial_priorities: List[str]  # Priority goals (e.g. education, savings)
    expense_categories_to_protect: Set[str]  # Non-negotiable categories
    expense_categories_user_is_willing_to_reduce: Set[str]  # Reducible categories
    expense_categories_user_is_willing_to_stop: Set[str]  # Stoppable subscriptions
    payment_methods_user_will_consider: Set[str]  # Allowed methods (full, partial, installments)
    max_installment_months: Optional[int]  # Max allowed loan term in months


@dataclass
class FinancialEvent:
    """Historical or scheduled cash flow transaction (income, expense, subscription, debt)."""
    event_id: str
    user_id: str
    event_type: str  # income, salary, expense, debt_payment, subscription, investment
    description: str
    category: str  # rent, groceries, utilities, dining, education, etc.
    direction: str  # 'credit' (cash in) or 'debit' (cash out)
    amount: Optional[float]  # Blank for 16 images requiring VLM extraction
    currency: str
    event_date: date
    settlement_date: date  # Date cash actually posts to balance
    status: str  # settled, pending, scheduled, unrealized, cancelled, failed
    linked_event_id: Optional[str]
    flexibility: str  # fixed, stoppable, reducible
    minimum_allowed_amount: Optional[float]  # Lower bound for reducible events


@dataclass
class PaymentOption:
    """Seller or provider payment plan offer (full or installment structure)."""
    payment_option_id: str
    request_id: str
    payment_method: str  # full_payment or installments
    payment_amount: float  # Per installment payment amount
    number_of_payments: int
    first_payment_date: date
    payment_frequency_days: Optional[int]  # Days between payments (~30 days)
    financing_fee: float
    total_payable_amount: float


@dataclass
class Request:
    """Evaluation request submitted by a user asking for affordability recommendation."""
    request_id: str
    user_id: str
    request_date: date
    request_type: str  # purchase, travel, education, debt_repayment, etc.
    requested_amount: float
    desired_completion_date: date
    allows_partial_payment: bool  # Whether request permits partial split
    request_text: str  # User prompt text


@dataclass
class Message:
    """Notification message (SMS, bank alert, employer note) updating financial facts."""
    message_id: str
    user_id: str
    request_id: Optional[str]
    related_event_id: Optional[str]
    sent_at: str
    source_type: str  # employer, service_provider, bank, merchant
    message_text: str
