from datetime import date
from decimal import Decimal

import pytest

from app.csv_import import (
    ColumnMapping,
    CSVImportError,
    Transaction,
    extract_transactions,
    find_duplicates,
    parse_amount,
    parse_csv,
    suggest_mapping,
)

# --- parsing values ---


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12.50", "12.50"),
        ("-12.50", "-12.50"),
        ("1,234.56", "1234.56"),
        ("1.234,56", "1234.56"),
        ("12,50", "12.50"),
        ("1,250", "1250"),
        ("(45.00)", "-45.00"),
        ("$ 9.99", "9.99"),
        ("-€1.234,50", "-1234.50"),
        ("20.00-", "-20.00"),
        ("", None),
        ("n/a", None),
        ("1-2", None),
    ],
)
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == (Decimal(expected) if expected is not None else None)


# --- reading files ---


def test_parse_csv_skips_preamble_and_blank_lines():
    content = (
        b"Account: 12345678\n"
        b"Statement period: Jan 2026\n"
        b"\n"
        b"Date,Description,Amount\n"
        b"2026-01-02,COFFEE SHOP,-3.50\n"
        b",,\n"
        b"2026-01-03,SALARY,2000.00\n"
    )
    parsed = parse_csv(content)
    assert parsed.headers == ["Date", "Description", "Amount"]
    assert parsed.rows == [["2026-01-02", "COFFEE SHOP", "-3.50"], ["2026-01-03", "SALARY", "2000.00"]]


def test_parse_csv_handles_semicolons_bom_and_cp1252():
    content = "﻿Datum;Omschrijving;Bedrag\n03.01.2026;Café;-4,20\n".encode()
    parsed = parse_csv(content)
    assert parsed.headers == ["Datum", "Omschrijving", "Bedrag"]
    assert parsed.rows == [["03.01.2026", "Café", "-4,20"]]

    latin = "Date,Description,Amount\n2026-01-03,Café,-4.20\n".encode("cp1252")
    assert parse_csv(latin).rows[0][1] == "Café"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"", "empty"),
        (b"just one line\n", "header row"),
        (b"no\ncolumns\nhere\n", "columns"),
        (b"\xff\xfe\x00\x00binary", None),
    ],
)
def test_parse_csv_rejects_bad_files(content, message):
    with pytest.raises(CSVImportError, match=message):
        parse_csv(content)


# --- suggesting a mapping ---


def test_suggests_single_signed_amount_column():
    parsed = parse_csv(
        b"Transaction Date,Details,Amount,Balance\n"
        b"02/01/2026,TESCO,-25.00,975.00\n"
        b"15/01/2026,UBER,-12.40,962.60\n"
    )
    mapping = suggest_mapping(parsed)
    assert mapping["date_column"] == 0
    assert mapping["description_column"] == 1
    assert mapping["amount_mode"] == "single"
    assert mapping["amount_column"] == 2
    assert mapping["expense_sign"] == "negative"
    # 15/01 rules out month-first, so only day-first formats remain.
    assert mapping["date_format"] == "%d/%m/%Y"
    assert "%m/%d/%Y" not in mapping["date_format_options"]


def test_suggests_split_debit_credit_and_reports_ambiguous_dates():
    parsed = parse_csv(
        b"Date,Payee,Debit,Credit,Category\n"
        b"03/04/2026,NETFLIX,15.99,,Entertainment\n"
        b"05/04/2026,REFUND,,20.00,\n"
    )
    mapping = suggest_mapping(parsed)
    assert mapping["amount_mode"] == "split"
    assert (mapping["debit_column"], mapping["credit_column"]) == (2, 3)
    assert mapping["category_column"] == 4
    assert {"%d/%m/%Y", "%m/%d/%Y"} <= set(mapping["date_format_options"])


def test_credit_card_exports_with_positive_purchases():
    parsed = parse_csv(
        b"Date,Description,Amount\n2026-01-02,AMAZON,30.00\n2026-01-09,PAYMENT,-500.00\n2026-01-10,SHELL,40\n"
    )
    assert suggest_mapping(parsed)["expense_sign"] == "positive"


# --- extracting expenses ---


def test_extract_single_column_skips_income_and_bad_rows():
    rows = [
        ["2026-01-02", "COFFEE  SHOP", "-3.50"],
        ["2026-01-03", "SALARY", "2000.00"],
        ["not a date", "X", "-1"],
        ["2026-01-04", "X", "abc"],
        ["2026-01-05", "X", "0"],
    ]
    mapping = ColumnMapping(date_column=0, description_column=1, amount_column=2)
    result = extract_transactions(rows, mapping)

    assert result.transactions == [Transaction(1, date(2026, 1, 2), Decimal("3.50"), "COFFEE SHOP")]
    assert [(s.row, s.reason.split(" ")[0]) for s in result.skipped] == [
        (2, "Money"),
        (3, "Couldn't"),
        (4, "Couldn't"),
        (5, "Zero"),
    ]


def test_extract_split_columns_with_category():
    rows = [
        ["03/04/2026", "NETFLIX", "15.99", "", "Entertainment"],
        ["05/04/2026", "REFUND", "", "20.00", ""],
    ]
    mapping = ColumnMapping(
        date_column=0,
        description_column=1,
        amount_mode="split",
        debit_column=2,
        credit_column=3,
        category_column=4,
        date_format="%m/%d/%Y",
    )
    result = extract_transactions(rows, mapping)
    assert result.transactions == [
        Transaction(1, date(2026, 3, 4), Decimal("15.99"), "NETFLIX", "Entertainment")
    ]
    assert result.skipped[0].reason.startswith("Money in")


# --- duplicates ---


def test_duplicates_are_matched_by_count():
    coffee = Transaction(1, date(2026, 1, 2), Decimal("3.50"), "Coffee Shop")
    file_rows = [
        coffee,
        Transaction(2, coffee.date, coffee.amount, "COFFEE  SHOP"),
        Transaction(3, coffee.date, Decimal("9"), "Lunch"),
    ]
    already_saved = [(date(2026, 1, 2), Decimal("3.50"), "coffee shop")]

    # One of the two identical coffees is already saved; the other is a genuine second purchase.
    assert find_duplicates(file_rows, already_saved) == [True, False, False]
