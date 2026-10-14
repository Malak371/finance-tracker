"""Realistic sample data for demo accounts.

Generates about a year of spending ending today: rent, subscriptions (one with a price rise,
one cancelled), utilities, groceries, dining, transport, shopping, one trip, plus a few rules
and budgets. A fixed random seed keeps the data the same for every demo account; dates are
relative to `today` so the demo always looks current.
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app import models
from app.months import add_months

DEMO_SEED = 20260101
HISTORY_MONTHS = 12


@dataclass
class DemoExpense:
    date: date
    amount: Decimal
    description: str
    category: str


def _money(value: float) -> Decimal:
    return Decimal(str(round(value, 2)))


class _Month:
    """Helper to place charges on days of one month, never in the future."""

    def __init__(self, start: date, today: date, rng: random.Random):
        self.start, self.rng = start, rng
        in_progress = (start.year, start.month) == (today.year, today.month)
        self.last_day = today.day if in_progress else (add_months(start, 1) - timedelta(days=1)).day

    def on(self, day: int) -> date | None:
        return self.start.replace(day=day) if day <= self.last_day else None

    def random_day(self) -> date:
        return self.start.replace(day=self.rng.randint(1, self.last_day))


GROCERS = [("TRADER JOE'S #552", 30, 95), ("WHOLE FOODS MKT 10234", 40, 140), ("SAFEWAY 1234", 25, 80)]
DINING = [
    ("STARBUCKS #1234", 4.5, 7.5),
    ("CHIPOTLE 2231", 11, 16),
    ("SWEETGREEN UNION SQ", 13, 17),
    ("DOORDASH*THAI SPICE", 22, 38),
    ("LUIGI'S TRATTORIA", 45, 85),
]


def generate_expenses(today: date, rng: random.Random | None = None) -> list[DemoExpense]:
    rng = rng or random.Random(DEMO_SEED)
    expenses: list[DemoExpense] = []
    this_month = today.replace(day=1)

    def add(when: date | None, amount: float, description: str, category: str) -> None:
        if when is not None:
            expenses.append(DemoExpense(when, _money(amount), description, category))

    for offset in range(-HISTORY_MONTHS, 1):
        start = add_months(this_month, offset)
        month = _Month(start, today, rng)

        # Fixed monthly charges
        add(month.on(1), 1450, "MAPLE STREET APARTMENTS RENT", "Rent")
        add(month.on(3), 34.99, "PUREGYM MEMBERSHIP", "Health")
        add(month.on(7), 17.99 if offset >= -3 else 15.49, "NETFLIX.COM", "Subscriptions")
        add(month.on(12), 11.99, "SPOTIFY P1A2B3C4", "Subscriptions")
        add(month.on(18), 2.99, "APPLE.COM/BILL ICLOUD", "Subscriptions")
        add(month.on(20), 69.99, "XFINITY INTERNET", "Utilities")
        winter = start.month in (12, 1, 2)
        add(
            month.on(22),
            rng.uniform(95, 120) if winter else rng.uniform(55, 80),
            "CITY POWER & LIGHT",
            "Utilities",
        )
        if offset <= -6:
            add(month.on(15), 7.99, "HULU 877-8244858", "Subscriptions")  # cancelled six months ago

        # Day-to-day spending
        for _ in range(rng.randint(5, 7)):
            name, low, high = rng.choice(GROCERS)
            add(month.random_day(), rng.uniform(low, high), name, "Groceries")
        for _ in range(rng.randint(7, 11)):
            name, low, high = rng.choice(DINING)
            add(month.random_day(), rng.uniform(low, high), name, "Dining")
        for _ in range(rng.randint(2, 4)):
            add(month.random_day(), rng.uniform(9, 32), "UBER *TRIP HELP.UBER.COM", "Transport")
        for _ in range(2):
            add(month.random_day(), rng.uniform(38, 58), "SHELL OIL 5742", "Transport")
        for _ in range(rng.randint(1, 3)):
            add(
                month.random_day(), rng.uniform(12, 95), f"AMAZON.COM*{rng.randint(10000, 99999)}", "Shopping"
            )
        if rng.random() < 0.5:
            add(month.random_day(), rng.uniform(20, 80), "TARGET 00012", "Shopping")
        if rng.random() < 0.4:
            add(month.random_day(), rng.uniform(14, 32), "AMC THEATRES", "Entertainment")
        if rng.random() < 0.3:
            add(month.random_day(), rng.uniform(8, 40), "CVS PHARMACY #0921", "Health")

        # One-off events
        if offset == -5:
            add(month.on(9), 412.60, "DELTA AIR LINES", "Travel")
            add(month.on(9), 690.00, "AIRBNB * HM8XQ2", "Travel")
        if start.month == 12 and offset < 0:
            add(month.on(14), 64.00, "ETSY GIFT ORDER", "Gifts")
            add(month.on(16), 120.00, "BEST BUY 00321", "Gifts")

        # Make sure the month in progress has something to look at from day one.
        if offset == 0:
            add(month.on(1), 23.40, "STARBUCKS #1234", "Dining")
            add(month.on(1), 64.50, "LUIGI'S TRATTORIA", "Dining")
            add(month.on(1), 89.99, "AMAZON.COM*48213", "Shopping")

    return sorted(expenses, key=lambda e: e.date)


DEMO_RULES = {"trader joe": "Groceries", "puregym": "Health", "luigi": "Dining"}
DEMO_BUDGETS = {"Groceries": 600, "Transport": 220, "Entertainment": 60}


def seed_demo_account(db: Session, user: models.User, today: date | None = None) -> None:
    today = today or date.today()
    expenses = generate_expenses(today)
    recent = today - timedelta(days=30)
    for e in expenses:
        # Recent coffees and rides show up as auto-categorised, like freshly imported data would.
        auto = e.date >= recent and e.description.startswith(("STARBUCKS", "UBER"))
        db.add(
            models.Expense(
                user_id=user.id,
                date=e.date,
                amount=e.amount,
                description=e.description,
                category=e.category,
                category_source="default" if auto else "manual",
            )
        )

    for keyword, category in DEMO_RULES.items():
        db.add(models.CategoryRule(user_id=user.id, keyword=keyword, category=category))

    # Dining and Shopping limits are set from this month's spending so the demo always shows one
    # budget nearing its limit and one over it.
    this_month = today.replace(day=1)
    spent: dict[str, Decimal] = {}
    for e in expenses:
        if e.date >= this_month:
            spent[e.category] = spent.get(e.category, Decimal(0)) + e.amount
    budgets = {name: Decimal(amount) for name, amount in DEMO_BUDGETS.items()}
    budgets["Dining"] = max(
        Decimal(100), (spent.get("Dining", Decimal(0)) * Decimal("1.12")).quantize(Decimal(1))
    )
    budgets["Shopping"] = max(
        Decimal(10), (spent.get("Shopping", Decimal(0)) * Decimal("0.85")).quantize(Decimal(1))
    )
    for category, amount in budgets.items():
        db.add(models.Budget(user_id=user.id, category=category, amount=amount))


def sample_statement(existing: list[models.Expense], today: date) -> str:
    """A bank-style CSV for trying the importer: a few rows the user already has (to show
    duplicate detection) plus new transactions, one income row and one unknown merchant."""
    lines = [
        "Account name,Everyday Checking",
        "Account number,****4821",
        "",
        "Date,Description,Amount,Balance",
    ]
    rows = [(e.date, e.description or e.category, -e.amount) for e in existing[:4]]
    new = [
        (1, "TRADER JOE'S #552", "-48.17"),
        (1, "STARBUCKS #2087", "-5.85"),
        (2, "ACME CORP PAYROLL", "3200.00"),
        (2, "UBER *TRIP HELP.UBER.COM", "-17.30"),
        (3, "ZEN FLOW YOGA STUDIO", "-25.00"),
        (3, "BLUE BOTTLE COFFEE", "-6.50"),
    ]
    rows += [
        (today - timedelta(days=days), description, Decimal(amount)) for days, description, amount in new
    ]
    balance = Decimal("2450.00")
    for when, description, amount in sorted(rows, key=lambda r: r[0]):
        balance += amount
        lines.append(f"{when:%d/%m/%Y},{description.replace(',', ' ')},{amount:.2f},{balance:.2f}")
    return "\n".join(lines) + "\n"
