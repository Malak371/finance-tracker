"""Plain-English spending insights, computed from the user's own history.

Everything here compares a month with the user's *own* past behaviour, never with other users.
For the month in progress, comparisons are made at the same day of the month (spending by the
14th vs. spending by the 14th of earlier months), so a half-finished month isn't compared with
whole ones.

Insight kinds, each with deliberately conservative thresholds so the cards stay meaningful:

- spike / drop: a category's spending is well outside its usual range (see `_category_change`)
- large_purchase: a single expense far above what the user usually spends in that category
- new_merchants: places the user has never paid before
- price_increase: a recurring charge that recently got more expensive
- forecast: projected month-end total for the month in progress
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, median, pstdev

from app.categorization import merchant_key
from app.months import add_months
from app.recurring import CADENCES, Charge, RecurringCharge

HISTORY_MONTHS = 6
MIN_HISTORY_MONTHS = 3

SPIKE_RATIO = 1.4  # at least 40% above the user's average...
SPIKE_MIN_DIFFERENCE = 25  # ...and at least this much more money...
UNUSUAL_Z = 1.5  # ...and outside their normal month-to-month variation.
DROP_RATIO = 0.6
DROP_MIN_AVERAGE = 50

LARGE_PURCHASE_MIN = Decimal(50)
LARGE_PURCHASE_RATIO = 3  # times the category's median purchase
MIN_PURCHASES_FOR_TYPICAL = 5

NEW_MERCHANT_MIN = Decimal(15)
MIN_HISTORY_DAYS_FOR_NEW_MERCHANTS = 60
PRICE_INCREASE_WINDOW = timedelta(days=60)
MAX_INSIGHTS = 6
# Comparing categories in a month in progress needs about a week of data to mean anything.
MIN_DAYS_FOR_CATEGORY_CHANGES = 7

TONE_ORDER = {"warning": 0, "info": 1, "positive": 2}


@dataclass
class Insight:
    kind: str
    tone: str  # "warning", "info" or "positive"
    title: str
    detail: str
    category: str | None = None


def _money(value: float | Decimal) -> str:
    return f"${float(value):,.2f}"


def _percent(current: float, usual: float) -> int:
    return round(abs(current - usual) / usual * 100)


class _History:
    def __init__(self, charges: list[Charge], month_start: date, today: date):
        self.month_start = month_start
        self.month_end = add_months(month_start, 1)
        self.in_progress = month_start <= today < self.month_end
        # Compare like with like: up to the same day of the month while the month is in progress.
        self.cutoff_day = today.day if self.in_progress else None
        self.today = today

        self.current = [c for c in charges if month_start <= c.date < self.month_end and c.date <= today]
        self.earlier = [c for c in charges if c.date < month_start]
        first_activity = min((c.date for c in charges), default=None)
        # Only count past months the user was already tracking, so a new user's empty
        # months don't look like zero spending.
        first_month = first_activity.replace(day=1) if first_activity else None
        self.past_months = [
            add_months(month_start, -i)
            for i in range(1, HISTORY_MONTHS + 1)
            if first_month is not None and add_months(month_start, -i) >= first_month
        ]

    def _in_window(self, charge: Charge, start: date) -> bool:
        end = add_months(start, 1)
        if self.cutoff_day is not None:
            end = min(end, start + timedelta(days=self.cutoff_day))
        return start <= charge.date < end

    def past_totals_by_category(self) -> dict[str, list[float]]:
        totals: dict[str, list[float]] = defaultdict(lambda: [0.0] * len(self.past_months))
        for i, start in enumerate(self.past_months):
            for charge in self.earlier:
                if self._in_window(charge, start):
                    totals[charge.category][i] += float(charge.amount)
        return totals

    def current_by_category(self) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)
        for charge in self.current:
            totals[charge.category] += float(charge.amount)
        return totals


def _category_change(category: str, current: float, past: list[float], in_progress: bool) -> Insight | None:
    usual = mean(past)
    spread = pstdev(past)
    when = "by this point in the month" if in_progress else "a month"
    if usual == 0:
        if current < SPIKE_MIN_DIFFERENCE:
            return None
        return Insight(
            "spike",
            "info",
            f"New spending on {category}",
            f"{_money(current)} so far; nothing in this category in recent months.",
            category,
        )
    if (
        current >= usual * SPIKE_RATIO
        and current - usual >= SPIKE_MIN_DIFFERENCE
        and (spread == 0 or (current - usual) / spread >= UNUSUAL_Z)
    ):
        return Insight(
            "spike",
            "warning",
            f"{category} is {_percent(current, usual)}% above usual",
            f"{_money(current)} so far vs. your average of {_money(usual)} {when}.",
            category,
        )
    if (
        usual >= DROP_MIN_AVERAGE
        and current <= usual * DROP_RATIO
        and (spread == 0 or (usual - current) / spread >= UNUSUAL_Z)
    ):
        return Insight(
            "drop",
            "positive",
            f"{category} is {_percent(current, usual)}% below usual",
            f"{_money(current)} vs. your average of {_money(usual)} {when}.",
            category,
        )
    return None


def _large_purchases(history: _History) -> list[Insight]:
    past_amounts: dict[str, list[Decimal]] = defaultdict(list)
    for charge in history.earlier:
        if charge.date >= add_months(history.month_start, -12):
            past_amounts[charge.category].append(charge.amount)

    found = []
    for charge in history.current:
        amounts = past_amounts.get(charge.category, [])
        if charge.amount < LARGE_PURCHASE_MIN or len(amounts) < MIN_PURCHASES_FOR_TYPICAL:
            continue
        typical = median(amounts)
        ninety_fifth = sorted(amounts)[int(len(amounts) * 0.95) - 1]
        if charge.amount >= typical * LARGE_PURCHASE_RATIO and charge.amount > ninety_fifth:
            ratio = charge.amount / typical
            found.append((ratio, charge, typical))
    found.sort(key=lambda item: -item[0])
    return [
        Insight(
            "large_purchase",
            "info",
            f"Unusually large {charge.category} purchase",
            f"{_money(charge.amount)} at {charge.description} on {charge.date:%b %-d}, "
            f"about {ratio:.0f}x your typical {_money(typical)}.",
            charge.category,
        )
        for ratio, charge, typical in found[:2]
    ]


def _new_merchants(history: _History) -> Insight | None:
    first_activity = min((c.date for c in history.earlier), default=None)
    if (
        first_activity is None
        or (history.month_start - first_activity).days < MIN_HISTORY_DAYS_FOR_NEW_MERCHANTS
    ):
        return None
    known = {merchant_key(c.description) for c in history.earlier}
    new: dict[str, Charge] = {}
    for charge in history.current:
        key = merchant_key(charge.description)
        if key and key not in known and charge.amount >= NEW_MERCHANT_MIN and key not in new:
            new[key] = charge
    if not new:
        return None
    listed = sorted(new.values(), key=lambda c: -c.amount)[:3]
    names = ", ".join(f"{c.description} ({_money(c.amount)})" for c in listed)
    count = len(new)
    return Insight(
        "new_merchants",
        "info",
        f"{count} new place{'s' if count > 1 else ''} this month",
        f"First time paying {names}{' and more' if count > 3 else ''}.",
    )


def _price_increases(recurring: list[RecurringCharge], today: date) -> list[Insight]:
    insights = []
    for r in recurring:
        if not (
            r.active
            and r.previous_amount is not None
            and r.amount > r.previous_amount
            and r.price_changed_on is not None
            and today - r.price_changed_on <= PRICE_INCREASE_WINDOW
        ):
            continue
        charges_per_year = CADENCES[r.cadence][2] * 12
        extra_per_year = (r.amount - r.previous_amount) * charges_per_year
        insights.append(
            Insight(
                "price_increase",
                "warning",
                f"{r.merchant} went up {_percent(float(r.amount), float(r.previous_amount))}%",
                f"Now {_money(r.amount)} instead of {_money(r.previous_amount)}, "
                f"about {_money(extra_per_year)} more a year.",
                r.category,
            )
        )
    return insights


def _forecast(history: _History) -> Insight | None:
    if not history.in_progress or history.cutoff_day is None or len(history.past_months) < MIN_HISTORY_MONTHS:
        return None
    days_in_month = (history.month_end - history.month_start).days
    if not 3 <= history.cutoff_day < days_in_month:
        return None

    recent = history.past_months[:3]
    rest_of_month, full_months = [], []
    for start in recent:
        end = add_months(start, 1)
        cutoff = start + timedelta(days=history.cutoff_day)
        month_charges = [c for c in history.earlier if start <= c.date < end]
        full_months.append(sum(float(c.amount) for c in month_charges))
        rest_of_month.append(sum(float(c.amount) for c in month_charges if c.date >= cutoff))

    so_far = sum(float(c.amount) for c in history.current)
    projected = so_far + mean(rest_of_month)
    usual = mean(full_months)
    if usual <= 0:
        return None
    if projected > usual * 1.1:
        tone, comparison = "warning", f"{_percent(projected, usual)}% more than"
    elif projected < usual * 0.9:
        tone, comparison = "positive", f"{_percent(projected, usual)}% less than"
    else:
        tone, comparison = "info", "in line with"
    return Insight(
        "forecast",
        tone,
        f"On track for about {_money(round(projected, -1))} this month",
        f"{_money(so_far)} so far plus your usual spending for the rest of the month; "
        f"{comparison} your recent average of {_money(usual)}.",
    )


def generate_insights(
    charges: list[Charge], recurring: list[RecurringCharge], month_start: date, today: date
) -> list[Insight]:
    history = _History(charges, month_start, today)
    insights: list[Insight] = []

    if forecast := _forecast(history):
        insights.append(forecast)

    large_purchases = _large_purchases(history)
    explained = {i.category for i in large_purchases}
    early_in_month = history.in_progress and today.day < MIN_DAYS_FOR_CATEGORY_CHANGES
    if len(history.past_months) >= MIN_HISTORY_MONTHS and not early_in_month:
        past = history.past_totals_by_category()
        current = history.current_by_category()
        for category in sorted(set(past) | set(current)):
            # A single large purchase already explains a jump in its category.
            if category in explained:
                continue
            change = _category_change(
                category, current.get(category, 0.0), past[category], history.in_progress
            )
            if change:
                insights.append(change)

    insights += large_purchases
    if new := _new_merchants(history):
        insights.append(new)
    if history.in_progress:
        insights += _price_increases(recurring, today)

    insights.sort(key=lambda i: TONE_ORDER[i.tone])
    return insights[:MAX_INSIGHTS]
