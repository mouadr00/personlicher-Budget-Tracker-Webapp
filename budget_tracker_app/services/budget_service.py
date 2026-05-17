"""Business logic for transactions, summaries, and budget plans."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..data_access.dao import CategoryDAO, MonthlyBudgetDAO, TransactionDAO
from ..domain.models import MonthlyBudget, Transaction
from .validation_service import ValidationError, ValidationService


TRANSACTION_KINDS = ("Einnahme", "Ausgabe")


@dataclass
class MonthlySummary:
    year: int
    month: int
    income_chf: float
    expenses_chf: float
    balance_chf: float
    largest_expense_category: Optional[str]
    largest_expense_chf: float
    category_expenses: Dict[str, float]
    transactions: List[Transaction]
    plan: Optional[MonthlyBudget]


class BudgetService:
    """Coordinates validation, persistence, and monthly calculations."""

    def __init__(
        self,
        transaction_dao: TransactionDAO,
        category_dao: CategoryDAO,
        budget_dao: MonthlyBudgetDAO,
    ) -> None:
        self.transaction_dao = transaction_dao
        self.category_dao = category_dao
        self.budget_dao = budget_dao

    def list_categories(self) -> list[str]:
        return [category.name for category in self.category_dao.list_all()]

    def add_category(self, name: str) -> str:
        cleaned = ValidationService.clean_category_name(name)
        existing = self.category_dao.get_by_name(cleaned)
        if existing:
            raise ValidationError("Diese Kategorie existiert bereits.")
        self.category_dao.create(cleaned)
        return cleaned

    def add_transaction(self, booking_date: str | date, kind: str, category_name: str, amount: str | float, note: str = "") -> Transaction:
        if kind not in TRANSACTION_KINDS:
            raise ValidationError("Bitte Einnahme oder Ausgabe auswählen.")

        parsed_date = ValidationService.parse_date(booking_date)
        parsed_amount = ValidationService.parse_money(amount)
        category = self.category_dao.get_by_name(category_name)
        if category is None:
            raise ValidationError("Bitte eine gültige Kategorie auswählen.")

        transaction = Transaction(
            booking_date=parsed_date,
            kind=kind,
            category_id=category.id or 0,
            amount_chf=parsed_amount,
            note=(note or "").strip()[:160],
        )
        return self.transaction_dao.create(transaction)

    def delete_transaction(self, transaction_id: int) -> bool:
        return self.transaction_dao.delete(transaction_id)

    def save_plan(self, year: int, month: int, planned_income: str | float, planned_expenses: str | float, savings_goal: str | float) -> MonthlyBudget:
        self._validate_month(year, month)
        return self.budget_dao.save(
            year=year,
            month=month,
            planned_income=ValidationService.parse_plan_money(planned_income),
            planned_expenses=ValidationService.parse_plan_money(planned_expenses),
            savings_goal=ValidationService.parse_plan_money(savings_goal),
        )

    def monthly_summary(self, year: int, month: int) -> MonthlySummary:
        self._validate_month(year, month)
        start, end = self._period(year, month)
        transactions = self.transaction_dao.list_for_period(start, end)

        income = round(sum(t.amount_chf for t in transactions if t.kind == "Einnahme"), 2)
        expenses = round(sum(t.amount_chf for t in transactions if t.kind == "Ausgabe"), 2)
        category_expenses: Dict[str, float] = {}

        for transaction in transactions:
            if transaction.kind != "Ausgabe":
                continue
            category_name = transaction.category.name if transaction.category else "Unbekannt"
            category_expenses[category_name] = round(
                category_expenses.get(category_name, 0.0) + transaction.amount_chf,
                2,
            )

        largest_category = None
        largest_amount = 0.0
        if category_expenses:
            largest_category = max(category_expenses, key=category_expenses.get)
            largest_amount = category_expenses[largest_category]

        return MonthlySummary(
            year=year,
            month=month,
            income_chf=income,
            expenses_chf=expenses,
            balance_chf=round(income - expenses, 2),
            largest_expense_category=largest_category,
            largest_expense_chf=largest_amount,
            category_expenses=category_expenses,
            transactions=transactions,
            plan=self.budget_dao.get(year, month),
        )

    @staticmethod
    def _period(year: int, month: int) -> tuple[date, date]:
        last_day = monthrange(year, month)[1]
        start = date(year, month, 1)
        end = date(year, month, last_day) + timedelta(days=1)
        return start, end

    @staticmethod
    def _validate_month(year: int, month: int) -> None:
        if year < 2000 or year > 2100 or month < 1 or month > 12:
            raise ValidationError("Bitte einen gültigen Monat auswählen.")
