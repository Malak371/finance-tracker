import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Annotated

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


# --- dashboard ---


class CategoryTotal(BaseModel):
    category: str
    total: MoneyOut
    count: int


class DashboardSummary(BaseModel):
    month: str
    total_spent: MoneyOut
    previous_month_total: MoneyOut
    transaction_count: int
    by_category: list[CategoryTotal]
