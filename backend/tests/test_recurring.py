from datetime import date, timedelta
from decimal import Decimal

from app.recurring import Charge, detect_recurring

TODAY = date(2026, 6, 15)


def monthly(description, amounts, start=date(2026, 1, 3), category="Subscriptions", step=31):
    return [
        Charge(start + timedelta(days=step * i), Decimal(str(amount)), description, category)
        for i, amount in enumerate(amounts)
    ]


def test_detects_a_monthly_subscription_with_varying_reference_numbers():
    charges = monthly("NETFLIX.COM 8841", [15.49] * 5)
    charges[2].description = "Netflix.com 1234"
    [found] = detect_recurring(charges, TODAY)
    assert (found.cadence, found.amount, found.monthly_cost, found.occurrences) == (
        "monthly",
        Decimal("15.49"),
        Decimal("15.49"),
        5,
    )
    assert found.next_date == found.last_date + timedelta(days=31)
    assert found.active


def test_reports_a_price_change():
    [found] = detect_recurring(monthly("SPOTIFY", [9.99, 9.99, 11.99, 11.99, 11.99]), TODAY)
    assert (found.amount, found.previous_amount) == (Decimal("11.99"), Decimal("9.99"))
    assert found.price_changed_on == date(2026, 1, 3) + timedelta(days=62)

    [unchanged] = detect_recurring(monthly("RENT", [900] * 4), TODAY)
    assert (unchanged.previous_amount, unchanged.price_changed_on) == (None, None)


def test_weekly_and_yearly_cadences():
    weekly = [
        Charge(date(2026, 5, 1) + timedelta(days=7 * i), Decimal(30), "Cleaner", "Home") for i in range(5)
    ]
    yearly = [
        Charge(date(2025, 3, 1), Decimal(99), "Domain renewal", "Tech"),
        Charge(date(2026, 3, 2), Decimal(99), "Domain renewal", "Tech"),
    ]
    found = {r.merchant: r for r in detect_recurring(weekly + yearly, TODAY)}
    assert found["Cleaner"].cadence == "weekly"
    assert found["Cleaner"].monthly_cost == Decimal("129.90")
    assert found["Domain renewal"].cadence == "yearly"
    assert found["Domain renewal"].monthly_cost == Decimal("8.25")


def test_tolerates_one_late_charge():
    dates = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 14), date(2026, 4, 1), date(2026, 5, 1)]
    charges = [Charge(d, Decimal(50), "Gym", "Health") for d in dates]
    assert [r.cadence for r in detect_recurring(charges, TODAY)] == ["monthly"]


def test_ignores_irregular_shopping_and_too_few_charges():
    irregular_amounts = monthly("TESCO", [12.0, 85.5, 40.0, 7.25])
    irregular_dates = [
        Charge(date(2026, 1, 1) + timedelta(days=d), Decimal(20), "Corner Shop", "Food")
        for d in (0, 3, 30, 41)
    ]
    too_few = monthly("Hulu", [7.99, 7.99])
    assert detect_recurring(irregular_amounts + irregular_dates + too_few, TODAY) == []


def test_flags_charges_that_stopped():
    [found] = detect_recurring(monthly("Old Gym", [40] * 3, start=date(2025, 10, 1)), TODAY)
    assert not found.active


def test_same_day_charges_count_once_for_timing():
    charges = monthly("Parking", [5] * 3) + monthly("Parking", [5] * 3)
    [found] = detect_recurring(charges, TODAY)
    assert found.cadence == "monthly"
