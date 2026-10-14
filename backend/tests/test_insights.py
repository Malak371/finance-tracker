from datetime import date, timedelta
from decimal import Decimal

from app.insights import generate_insights
from app.months import add_months
from app.recurring import Charge, RecurringCharge

MARCH = date(2026, 3, 1)
END_OF_MARCH = date(2026, 4, 1)  # "today" after March is over: March is a complete month


def steady_history(months=6, start=MARCH, per_month=(("Groceries", 300), ("Dining", 150), ("Rent", 1000))):
    """Identical spending in each of the `months` months before `start`, spread over the month."""
    charges = []
    for i in range(1, months + 1):
        month = add_months(start, -i)
        for category, amount in per_month:
            for day, share in ((2, 0.25), (10, 0.25), (18, 0.25), (26, 0.25)):
                charges.append(
                    Charge(month.replace(day=day), Decimal(str(amount * share)), f"{category} shop", category)
                )
    return charges


def kinds(insights):
    return [(i.kind, i.category) for i in insights]


def test_flags_a_category_spike_but_not_normal_months():
    march = [Charge(MARCH.replace(day=d), Decimal(100), "Restaurant", "Dining") for d in (3, 9, 15, 21)]
    march += [Charge(MARCH.replace(day=5), Decimal(300), "Groceries shop", "Groceries")]
    march += [Charge(MARCH.replace(day=1), Decimal(1000), "Rent shop", "Rent")]
    insights = generate_insights(steady_history() + march, [], MARCH, END_OF_MARCH)

    spike = next(i for i in insights if i.kind == "spike")
    assert spike.category == "Dining"
    assert spike.title == "Dining is 167% above usual"
    assert ("spike", "Groceries") not in kinds(insights)


def test_flags_a_drop_as_good_news():
    march = [
        Charge(MARCH.replace(day=1), Decimal(1000), "Rent shop", "Rent"),
        Charge(MARCH.replace(day=4), Decimal(300), "Groceries shop", "Groceries"),
        Charge(MARCH.replace(day=7), Decimal(20), "Dining shop", "Dining"),
    ]
    insights = generate_insights(steady_history() + march, [], MARCH, END_OF_MARCH)
    drop = next(i for i in insights if i.kind == "drop")
    assert (drop.category, drop.tone) == ("Dining", "positive")


def test_month_in_progress_is_compared_at_the_same_day():
    # By the 5th of each past month only the day-2 quarter had been spent (75 on Groceries).
    today = MARCH.replace(day=5)
    march = [Charge(MARCH.replace(day=2), Decimal(75), "Groceries shop", "Groceries")]
    insights = generate_insights(steady_history() + march, [], MARCH, today)
    assert not [i for i in insights if i.kind in ("spike", "drop")]


def test_needs_enough_history():
    history = steady_history(months=2)
    march = [Charge(MARCH.replace(day=3), Decimal(900), "Restaurant", "Dining")]
    assert not [i for i in generate_insights(history + march, [], MARCH, END_OF_MARCH) if i.kind == "spike"]


def test_unusually_large_purchase():
    march = [Charge(MARCH.replace(day=12), Decimal(480), "FANCY DINNER", "Dining")]
    insights = generate_insights(steady_history() + march, [], MARCH, END_OF_MARCH)
    large = next(i for i in insights if i.kind == "large_purchase")
    assert "$480.00 at FANCY DINNER on Mar 12" in large.detail
    assert "13x your typical $37.50" in large.detail
    # The purchase already explains the jump, so Dining isn't reported as a spike as well.
    assert ("spike", "Dining") not in kinds(insights)


def test_no_category_comparisons_in_the_first_days_of_a_month():
    march = [Charge(MARCH.replace(day=2), Decimal(400), "Restaurant", "Dining")]
    insights = generate_insights(steady_history() + march, [], MARCH, MARCH.replace(day=3))
    assert not [i for i in insights if i.kind in ("spike", "drop")]


def test_new_merchants():
    march = [
        Charge(MARCH.replace(day=3), Decimal(25), "ZEN YOGA STUDIO", "Health"),
        Charge(MARCH.replace(day=4), Decimal(5), "TINY KIOSK", "Dining"),  # below the minimum amount
        Charge(MARCH.replace(day=5), Decimal(60), "Groceries shop", "Groceries"),  # already known
    ]
    insights = generate_insights(steady_history() + march, [], MARCH, END_OF_MARCH)
    assert ("spike", "Health") in kinds(insights)  # reported as new spending, not a percentage
    new = next(i for i in insights if i.kind == "new_merchants")
    assert new.title == "1 new place this month"
    assert "ZEN YOGA STUDIO ($25.00)" in new.detail


def test_recent_price_increase():
    today = MARCH.replace(day=20)
    netflix = RecurringCharge(
        merchant="NETFLIX.COM",
        category="Subscriptions",
        cadence="monthly",
        amount=Decimal("17.99"),
        monthly_cost=Decimal("17.99"),
        occurrences=12,
        first_date=date(2025, 3, 7),
        last_date=date(2026, 3, 7),
        next_date=date(2026, 4, 7),
        active=True,
        previous_amount=Decimal("15.49"),
        price_changed_on=date(2026, 3, 7),
    )
    insights = generate_insights(steady_history(), [netflix], MARCH, today)
    increase = next(i for i in insights if i.kind == "price_increase")
    assert increase.title == "NETFLIX.COM went up 16%"
    assert "about $30.00 more a year" in increase.detail

    old_change = RecurringCharge(**{**netflix.__dict__, "price_changed_on": today - timedelta(days=90)})
    assert not [
        i
        for i in generate_insights(steady_history(), [old_change], MARCH, today)
        if i.kind == "price_increase"
    ]


def test_forecast_for_the_month_in_progress():
    # Past months: 1450 in total; half (days 2 and 10) is spent by the 10th, half after it.
    today = MARCH.replace(day=10)
    march = [Charge(MARCH.replace(day=2), Decimal("725"), "Rent shop", "Rent")]
    forecast = next(
        i for i in generate_insights(steady_history() + march, [], MARCH, today) if i.kind == "forecast"
    )
    assert forecast.tone == "info"
    assert forecast.title == "On track for about $1,450.00 this month"

    big_month = [*march, Charge(MARCH.replace(day=9), Decimal(500), "Laptop", "Shopping")]
    forecast = next(
        i for i in generate_insights(steady_history() + big_month, [], MARCH, today) if i.kind == "forecast"
    )
    assert forecast.tone == "warning"


def test_new_user_gets_no_insights():
    charges = [Charge(MARCH.replace(day=2), Decimal(50), "Shop", "Food")]
    assert generate_insights(charges, [], MARCH, MARCH.replace(day=15)) == []
