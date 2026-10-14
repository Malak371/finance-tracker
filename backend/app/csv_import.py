"""Parsing bank/credit-card CSV exports into expenses.

Pure functions only (no database access), so the tricky parsing rules are easy to test.
The flow is: parse_csv() -> the user confirms a ColumnMapping -> extract_transactions().
"""

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Literal

MAX_ROWS = 5000
ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")
DELIMITERS = ",;\t|"

# Checked in order; the first format that parses every sample wins. Day-first and month-first
# formats are both listed so ambiguous files can be reported back to the user.
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d.%m.%Y",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%Y/%m/%d",
    "%d/%m/%y",
    "%m/%d/%y",
    "%d %b %Y",
    "%b %d, %Y",
    "%Y%m%d",
]

HEADER_HINTS = {
    "date": (
        "transaction date",
        "trans date",
        "date",
        "posted",
        "posting date",
        "booking date",
        "value date",
    ),
    "description": (
        "description",
        "details",
        "merchant",
        "payee",
        "narrative",
        "transaction",
        "name",
        "memo",
        "reference",
    ),
    "amount": ("amount", "value", "transaction amount"),
    "debit": ("debit", "withdrawal", "money out", "paid out", "out"),
    "credit": ("credit", "deposit", "money in", "paid in", "in"),
    "category": ("category",),
}


class CSVImportError(ValueError):
    """A problem with the uploaded file that the user can fix."""


@dataclass
class ParsedCSV:
    headers: list[str]
    rows: list[list[str]]


@dataclass
class ColumnMapping:
    date_column: int
    description_column: int
    amount_mode: Literal["single", "split"] = "single"
    amount_column: int | None = None
    debit_column: int | None = None
    credit_column: int | None = None
    # For a single amount column: are expenses the negative or the positive numbers?
    expense_sign: Literal["negative", "positive"] = "negative"
    date_format: str = "%Y-%m-%d"
    category_column: int | None = None


@dataclass
class Transaction:
    row: int
    date: date
    amount: Decimal
    description: str
    category: str | None = None


@dataclass
class Skipped:
    row: int
    reason: str


@dataclass
class Extraction:
    transactions: list[Transaction] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)


# --- reading the file ---


def decode(content: bytes) -> str:
    for encoding in ENCODINGS:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CSVImportError("Couldn't read the file. Please upload a text CSV export.")


def parse_csv(content: bytes) -> ParsedCSV:
    text = decode(content)
    if not text.strip():
        raise CSVImportError("The file is empty.")
    sample = text[:10_000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=DELIMITERS)
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    rows = [
        [cell.strip() for cell in row]
        for row in csv.reader(io.StringIO(text), delimiter=delimiter)
        if any(cell.strip() for cell in row)
    ]
    if len(rows) < 2:
        raise CSVImportError("The file needs a header row and at least one transaction.")

    # Some banks put account details above the real table. The header is the first row
    # with as many columns as the most common row width.
    width = Counter(len(r) for r in rows).most_common(1)[0][0]
    if width < 2:
        raise CSVImportError("Couldn't find separate columns. Is this a CSV file?")
    header_index = next(i for i, r in enumerate(rows) if len(r) == width)
    headers = rows[header_index]
    data = [r + [""] * (width - len(r)) for r in rows[header_index + 1 :] if len(r) <= width]
    if not data:
        raise CSVImportError("No transactions found below the header row.")
    if len(data) > MAX_ROWS:
        raise CSVImportError(f"Files can have at most {MAX_ROWS} rows. Split the file and try again.")
    return ParsedCSV(headers=headers, rows=data)


# --- guessing the mapping ---


def _find_column(headers: list[str], role: str, exclude: set[int]) -> int | None:
    normalized = [h.strip().lower() for h in headers]
    for hint in HEADER_HINTS[role]:
        for i, header in enumerate(normalized):
            if i not in exclude and (header == hint or (len(hint) > 3 and hint in header)):
                return i
    return None


def candidate_date_formats(values: list[str]) -> list[str]:
    """Every known format that parses all of the given non-empty values."""
    samples = [v for v in values if v][:200]
    if not samples:
        return []
    return [fmt for fmt in DATE_FORMATS if all(_parse_date(v, fmt) for v in samples)]


def suggest_mapping(parsed: ParsedCSV) -> dict:
    """Best-effort guess the user confirms or edits before previewing."""
    used: set[int] = set()

    def take(role: str) -> int | None:
        index = _find_column(parsed.headers, role, used)
        if index is not None:
            used.add(index)
        return index

    date_column = take("date")
    amount_column = take("amount")
    debit_column = credit_column = None
    if amount_column is None:
        debit_column = take("debit")
        credit_column = take("credit")
    description_column = take("description")
    category_column = take("category")

    date_formats = (
        candidate_date_formats([row[date_column] for row in parsed.rows]) if date_column is not None else []
    )

    expense_sign = "negative"
    if amount_column is not None:
        amounts = [parse_amount(row[amount_column]) for row in parsed.rows]
        negatives = sum(1 for a in amounts if a is not None and a < 0)
        positives = sum(1 for a in amounts if a is not None and a > 0)
        # Credit card exports often list purchases as positive numbers.
        expense_sign = "negative" if negatives >= positives else "positive"

    return {
        "date_column": date_column,
        "description_column": description_column,
        "amount_mode": "split" if amount_column is None and debit_column is not None else "single",
        "amount_column": amount_column,
        "debit_column": debit_column,
        "credit_column": credit_column,
        "expense_sign": expense_sign,
        "date_format": date_formats[0] if date_formats else None,
        "date_format_options": date_formats,
        "category_column": category_column,
    }


# --- value parsing ---


def _parse_date(value: str, fmt: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), fmt).date()
    except ValueError:
        return None


def parse_amount(value: str) -> Decimal | None:
    """Parse amounts like '1,234.56', '-12.00', '(12.00)', '$12', '1.234,56', '12.00-'."""
    text = value.strip()
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = re.sub(r"[^\d,.\-]", "", text)
    if text.endswith("-"):
        negative, text = True, text[:-1]
    if text.startswith("-"):
        negative, text = not negative, text[1:]
    if not text or "-" in text:
        return None

    if "," in text and "." in text:
        # Whichever separator comes last is the decimal point.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        # "12,50" is a decimal comma; "1,250" is a thousands separator.
        text = text.replace(",", ".") if re.fullmatch(r"\d+,\d{1,2}", text) else text.replace(",", "")

    try:
        amount = Decimal(text)
    except InvalidOperation:
        return None
    return -amount if negative else amount


def normalize_description(description: str) -> str:
    return re.sub(r"\s+", " ", description).strip().lower()


# --- turning rows into expenses ---


def _cell(row: list[str], index: int | None) -> str:
    return row[index] if index is not None and 0 <= index < len(row) else ""


def validate_mapping(mapping: ColumnMapping, width: int) -> None:
    columns = {
        "date_column": mapping.date_column,
        "description_column": mapping.description_column,
        "amount_column": mapping.amount_column,
        "debit_column": mapping.debit_column,
        "credit_column": mapping.credit_column,
        "category_column": mapping.category_column,
    }
    for name, index in columns.items():
        if index is not None and not 0 <= index < width:
            raise CSVImportError(f"{name} points at a column that doesn't exist.")
    if mapping.amount_mode == "single" and mapping.amount_column is None:
        raise CSVImportError("Choose the amount column.")
    if mapping.amount_mode == "split" and mapping.debit_column is None:
        raise CSVImportError("Choose the debit (money out) column.")
    if mapping.date_format not in DATE_FORMATS:
        raise CSVImportError("Unsupported date format.")


def extract_transactions(rows: list[list[str]], mapping: ColumnMapping) -> Extraction:
    """Turn raw rows into expenses. Income, refunds and unreadable rows are skipped with a reason."""
    result = Extraction()
    for i, row in enumerate(rows):
        row_number = i + 1
        raw_date = _cell(row, mapping.date_column)
        parsed_date = _parse_date(raw_date, mapping.date_format)
        if parsed_date is None:
            result.skipped.append(Skipped(row_number, f"Couldn't read the date '{raw_date}'"))
            continue

        if mapping.amount_mode == "split":
            debit = parse_amount(_cell(row, mapping.debit_column))
            credit = parse_amount(_cell(row, mapping.credit_column))
            if debit:
                amount = abs(debit)
            elif credit:
                result.skipped.append(Skipped(row_number, "Money in (credit), not an expense"))
                continue
            else:
                result.skipped.append(Skipped(row_number, "No amount"))
                continue
        else:
            raw_amount = _cell(row, mapping.amount_column)
            value = parse_amount(raw_amount)
            if value is None:
                result.skipped.append(Skipped(row_number, f"Couldn't read the amount '{raw_amount}'"))
                continue
            if value == 0:
                result.skipped.append(Skipped(row_number, "Zero amount"))
                continue
            is_expense = value < 0 if mapping.expense_sign == "negative" else value > 0
            if not is_expense:
                result.skipped.append(Skipped(row_number, "Money in (income or refund), not an expense"))
                continue
            amount = abs(value)

        amount = amount.quantize(Decimal("0.01"))
        if amount >= Decimal("10000000000"):
            result.skipped.append(Skipped(row_number, "Amount is too large"))
            continue

        description = re.sub(r"\s+", " ", _cell(row, mapping.description_column)).strip()[:255]
        category = _cell(row, mapping.category_column)[:50].strip() or None
        result.transactions.append(Transaction(row_number, parsed_date, amount, description, category))
    return result


def find_duplicates(
    transactions: list[Transaction], existing: list[tuple[date, Decimal, str | None]]
) -> list[bool]:
    """Flag transactions that are already recorded.

    Matching is on (date, amount, normalised description) and counts occurrences: if a file
    has two identical coffees on one day and one is already saved, only one is flagged. That
    way re-importing a file, or an overlapping statement, is caught without hiding genuine
    repeat purchases.
    """
    remaining = Counter((d, a, normalize_description(desc or "")) for d, a, desc in existing)
    flags = []
    for t in transactions:
        key = (t.date, t.amount, normalize_description(t.description))
        if remaining[key] > 0:
            remaining[key] -= 1
            flags.append(True)
        else:
            flags.append(False)
    return flags
