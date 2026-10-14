import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
    field_validator,
)

# Exact decimal on the way in, plain JSON number on the way out.
MoneyIn = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
MoneyOut = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _check_not_blank(value: str) -> str:
    if not value:
        raise ValueError("must not be blank")
    return value


Category = Annotated[str, AfterValidator(_clean_text), AfterValidator(_check_not_blank), Field(max_length=50)]
Description = Annotated[str, AfterValidator(_clean_text), Field(max_length=255)]

EARLIEST_DATE = date(2000, 1, 1)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- auth ---


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def bcrypt_length_limit(cls, value: str) -> str:
        if len(value.encode()) > 72:
            raise ValueError("must be at most 72 bytes")
        return value


class UserOut(ORMModel):
    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- expenses ---


class ExpenseIn(BaseModel):
    amount: MoneyIn
    category: Category
    date: date
    description: Description | None = None

    @field_validator("date")
    @classmethod
    def plausible_date(cls, value: date) -> date:
        if value < EARLIEST_DATE or value > date.today() + timedelta(days=366):
            raise ValueError("must be between 2000-01-01 and one year from today")
        return value

    @field_validator("description")
    @classmethod
    def empty_description_is_none(cls, value: str | None) -> str | None:
        return value or None


class ExpenseOut(ORMModel):
    id: int
    amount: MoneyOut
    category: str
    category_source: str
    date: date
    description: str | None


# --- budgets ---


class BudgetIn(BaseModel):
    category: Category
    amount: MoneyIn


class BudgetOut(ORMModel):
    id: int
    category: str
    amount: MoneyOut


class BudgetStatus(BudgetOut):
    spent: MoneyOut
    remaining: MoneyOut
    percent: float
    status: Literal["ok", "warning", "over"]
    # Month-end spend at the current daily pace; only for the month in progress.
    projected: MoneyOut | None


# --- dashboard ---


class CategoryTotal(BaseModel):
    category: str
    total: MoneyOut
    count: int


class MonthTotal(BaseModel):
    month: str
    total: MoneyOut


class DashboardSummary(BaseModel):
    month: str
    total_spent: MoneyOut
    previous_month_total: MoneyOut
    transaction_count: int
    by_category: list[CategoryTotal]


# --- CSV import ---


class ParsedFile(BaseModel):
    headers: list[str]
    rows: list[list[str]]
    suggested_mapping: dict


class ColumnMappingIn(BaseModel):
    date_column: int = Field(ge=0)
    description_column: int = Field(ge=0)
    amount_mode: Literal["single", "split"] = "single"
    amount_column: int | None = Field(default=None, ge=0)
    debit_column: int | None = Field(default=None, ge=0)
    credit_column: int | None = Field(default=None, ge=0)
    expense_sign: Literal["negative", "positive"] = "negative"
    date_format: str
    category_column: int | None = Field(default=None, ge=0)


class PreviewRequest(BaseModel):
    mapping: ColumnMappingIn
    rows: list[list[Annotated[str, Field(max_length=1000)]]] = Field(max_length=5000)


class PreviewTransaction(BaseModel):
    row: int
    date: date
    amount: MoneyOut
    description: str
    category: str
    category_source: str
    confidence: float | None
    duplicate: bool


class SkippedRow(BaseModel):
    row: int
    reason: str


class PreviewResponse(BaseModel):
    transactions: list[PreviewTransaction]
    skipped: list[SkippedRow]


CategorySource = Literal["manual", "file", "rule", "history", "model", "default", "none"]


class ImportTransaction(ExpenseIn):
    # "manual" when the user picked or changed the category in the preview, which makes the
    # row training data for their classifier; otherwise the source the preview suggested.
    category_source: CategorySource = "manual"


class ImportRequest(BaseModel):
    transactions: list[ImportTransaction] = Field(min_length=1, max_length=5000)


class ImportResult(BaseModel):
    imported: int


# --- categorisation rules ---


def _normalize_keyword(value: str) -> str:
    from app.categorization import normalize

    keyword = normalize(value)
    if len(keyword) < 2:
        raise ValueError("must contain at least 2 letters or digits")
    return keyword


Keyword = Annotated[str, Field(max_length=100), AfterValidator(_normalize_keyword)]


class RuleIn(BaseModel):
    keyword: Keyword
    category: Category


class RuleCreate(RuleIn):
    # Also re-categorise existing expenses that were auto-categorised or left Uncategorized.
    apply_to_existing: bool = False


class RuleOut(ORMModel):
    id: int
    keyword: str
    category: str


class RuleCreated(RuleOut):
    applied: int


class DefaultRule(BaseModel):
    keyword: str
    category: str
