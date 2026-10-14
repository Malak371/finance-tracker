"""Detecting recurring charges (subscriptions, rent, memberships) from expense history.

Expenses are grouped by merchant (the description's words, ignoring numbers, so
"NETFLIX.COM 8841" and "Netflix.com 9921" are the same). A group is recurring when:

- the gaps between charges fit one cadence (weekly ... yearly): the median and the average gap
  are in the cadence's window and at least half the gaps are too. A late charge makes one gap
  long and the next short, so this tolerates it without accepting irregular visits;
- the amounts are stable: every charge within 25% of the median, so a price rise is
  tolerated (and reported) but irregular shopping at one store is not;
- there are enough charges: 3, or 2 for yearly charges with near-identical amounts.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from itertools import pairwise
from statistics import median

from app.categorization import merchant_key

# name: (shortest gap, longest gap, charges per month)
CADENCES = {
    "weekly": (6, 8, Decimal("4.33")),
    "fortnightly": (13, 16, Decimal("2.17")),
    "monthly": (26, 35, Decimal(1)),
    "quarterly": (84, 98, Decimal(1) / 3),
    "yearly": (350, 380, Decimal(1) / 12),
}
AMOUNT_TOLERANCE = Decimal("0.25")
YEARLY_AMOUNT_TOLERANCE = Decimal("0.05")


@dataclass
class Charge:
    date: date
    amount: Decimal
    description: str
    category: str


@dataclass
class RecurringCharge:
    merchant: str
    category: str
    cadence: str
    amount: Decimal
    monthly_cost: Decimal
    occurrences: int
    first_date: date
    last_date: date
    next_date: date
    active: bool
    previous_amount: Decimal | None  # set when the latest charge differs from the one before


def _cadence_for(gaps: list[int]) -> str | None:
    typical = median(gaps)
    average = sum(gaps) / len(gaps)
    for name, (shortest, longest, _) in CADENCES.items():
        if shortest <= typical <= longest and shortest <= average <= longest:
            fitting = sum(1 for gap in gaps if shortest <= gap <= longest)
            if fitting * 2 >= len(gaps):
                return name
    return None


def _stable_amounts(amounts: list[Decimal], tolerance: Decimal) -> bool:
    typical = Decimal(median(amounts))
    return all(abs(a - typical) <= typical * tolerance for a in amounts)


def detect_recurring(charges: list[Charge], today: date) -> list[RecurringCharge]:
    groups: dict[str, list[Charge]] = {}
    for charge in charges:
        key = merchant_key(charge.description)
        if key:
            groups.setdefault(key, []).append(charge)

    found = []
    for group in groups.values():
        group.sort(key=lambda c: c.date)
        # Several charges on one day (e.g. split payments) count once for timing.
        dates = sorted({c.date for c in group})
        if len(dates) < 2:
            continue
        gaps = [(b - a).days for a, b in pairwise(dates)]
        cadence = _cadence_for(gaps)
        if cadence is None:
            continue
        amounts = [c.amount for c in group]
        if cadence == "yearly":
            if not _stable_amounts(amounts, YEARLY_AMOUNT_TOLERANCE):
                continue
        elif len(dates) < 3 or not _stable_amounts(amounts, AMOUNT_TOLERANCE):
            continue

        latest = group[-1]
        typical_gap = round(median(gaps))
        next_date = latest.date + timedelta(days=typical_gap)
        # Allow half a cycle of slack before suggesting it may have been cancelled.
        active = today <= next_date + timedelta(days=max(3, typical_gap // 2))
        previous = group[-2].amount if len(group) > 1 else None
        found.append(
            RecurringCharge(
                merchant=latest.description,
                category=latest.category,
                cadence=cadence,
                amount=latest.amount,
                monthly_cost=(latest.amount * CADENCES[cadence][2]).quantize(Decimal("0.01")),
                occurrences=len(group),
                first_date=group[0].date,
                last_date=latest.date,
                next_date=next_date,
                active=active,
                previous_amount=previous if previous is not None and previous != latest.amount else None,
            )
        )
    return sorted(found, key=lambda r: (not r.active, -r.monthly_cost))
