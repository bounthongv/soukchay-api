"""Computed fields for the FA / Loan section.

The web app stores loan components in loan_department.price1..price5:
    price1 = Laboure fee
    price2 = Upfront fee
    price3 = Interest in Advance
    price4 = Total Debt
    price5 = Laboure Balance

The customer additionally asks for overdue/interest-day figures. These are NOT
stored anywhere in the DB -- they are derived from the loan terms (rate,
first_due_date, last_due_date) and payment history. Provided here as standard
flat-loan calculations.
"""
import datetime


def _parse_date(v):
    if not v:
        return None
    if isinstance(v, datetime.date):
        return v
    try:
        return datetime.date.fromisoformat(str(v)[:10])
    except (ValueError, TypeError):
        return None


def days_overdue(first_due_date, last_due_date, today=None):
    """Days the loan is overdue relative to its final due date.

    Positive = overdue; negative/zero = still within term.
    """
    end = _parse_date(last_due_date) or _parse_date(first_due_date)
    if not end:
        return 0
    today = today or datetime.date.today()
    return (today - end).days


def elapsed_term_days(first_due_date, today=None):
    """Days elapsed since the loan was released (first due date)."""
    start = _parse_date(first_due_date)
    if not start:
        return 0
    today = today or datetime.date.today()
    return max(0, (today - start).days)


def interest_payable(fin_price, rate_str, elapsed_days):
    """Simple flat interest on the finance amount over the elapsed days.

    rate_str is the annual % as the app stores it (e.g. "12" = 12%/yr).
    """
    if not fin_price:
        return 0.0
    try:
        rate = float(str(rate_str).replace("%", ""))
    except (ValueError, TypeError):
        rate = 0.0
    if rate <= 0:
        return 0.0
    return round(float(fin_price) * rate / 100.0 * (elapsed_days / 365.0), 2)


def interest_in_advance(fin_price, rate_str, months):
    """Interest charged up front for a term of `months` months."""
    if not fin_price:
        return 0.0
    try:
        rate = float(str(rate_str).replace("%", ""))
    except (ValueError, TypeError):
        rate = 0.0
    if rate <= 0:
        return 0.0
    return round(float(fin_price) * rate / 100.0 * (months / 12.0), 2)


def over_under_amount(payments_total, total_debt):
    """Amount paid over (positive) or under (negative) the total debt."""
    return round(float(payments_total or 0.0) - float(total_debt or 0.0), 2)


def to_currency(amount, exchange_rate):
    """Convert an amount to a target currency using the exchange rate."""
    try:
        return round(float(amount or 0.0) * float(exchange_rate or 0.0), 2)
    except (ValueError, TypeError):
        return round(float(amount or 0.0), 2)