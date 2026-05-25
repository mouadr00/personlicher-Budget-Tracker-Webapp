"""SQLModel domain and persistence models."""

from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Category(SQLModel, table=True):
    """A valid transaction category."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, min_length=2, max_length=60)

    transactions: list["Transaction"] = Relationship(back_populates="category")


class Transaction(SQLModel, table=True):
    """A single income or expense booking."""

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_date: date = Field(index=True)
    kind: str = Field(index=True, min_length=6, max_length=10)
    category_id: int = Field(foreign_key="category.id", index=True)
    amount_chf: float = Field(gt=0, le=1_000_000)
    note: str = Field(default="", max_length=160)
    transfer_direction: Optional[str] = Field(default=None, max_length=24)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    category: Category = Relationship(back_populates="transactions")

    @property
    def signed_amount_chf(self) -> float:
        if self.kind == "Einnahme":
            return self.amount_chf
        if self.kind == "Umbuchung" and self.transfer_direction in ("Sparkonto zu Budget", "Sparen zu Budget"):
            return self.amount_chf
        if self.kind == "Umbuchung" and self.transfer_direction in ("Budget zu Sparkonto", "Budget zu Sparen"):
            return -self.amount_chf
        return -self.amount_chf


class MonthlyBudget(SQLModel, table=True):
    """Plan values for a specific month."""

    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True, ge=2000, le=2100)
    month: int = Field(index=True, ge=1, le=12)
    planned_income_chf: float = Field(default=0.0, ge=0)
    planned_expenses_chf: float = Field(default=0.0, ge=0)
    savings_goal_chf: float = Field(default=0.0, ge=0)


class UserAccount(SQLModel, table=True):
    """Single local user account for password protection."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(default="admin", index=True, min_length=3, max_length=40)
    password_hash: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
