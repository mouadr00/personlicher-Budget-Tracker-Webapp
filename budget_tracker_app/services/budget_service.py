"""Business logic for transactions, transfers, summaries, and budget plans."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..data_access.dao import CategoryDAO, MonthlyBudgetDAO, TransactionDAO
from ..domain.models import Category, MonthlyBudget, Transaction
from .validation_service import ValidationError, ValidationService


TRANSACTION_KINDS = ("Einnahme", "Ausgabe", "Umbuchung")
TRANSFER_TO_SAVINGS = "Budget zu Sparkonto"
TRANSFER_TO_BUDGET = "Sparkonto zu Budget"
LEGACY_TRANSFER_TO_SAVINGS = "Budget zu Sparen"
LEGACY_TRANSFER_TO_BUDGET = "Sparen zu Budget"
TRANSFER_DIRECTIONS = (TRANSFER_TO_SAVINGS, TRANSFER_TO_BUDGET)
TRANSFER_DIRECTION_ALIASES = {
    LEGACY_TRANSFER_TO_SAVINGS: TRANSFER_TO_SAVINGS,
    LEGACY_TRANSFER_TO_BUDGET: TRANSFER_TO_BUDGET,
}
SAVINGS_CATEGORY = "Sparen"


@dataclass
class MonthlySummary:
    year: int
    month: int
    income_chf: float
    expenses_chf: float
    balance_chf: float
    largest_expense_category: Optional[str]
    largest_expense_chf: float
    largest_expense_share_pct: float
    planned_expenses_chf: float
    remaining_expense_budget_chf: float
    savings_booked_chf: float
    transfer_to_savings_chf: float
    transfer_to_budget_chf: float
    budget_used_chf: float
    spending_budget_used_pct: float
    savings_goal_progress_pct: float
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

    def add_transaction(
        self,
        booking_date: str | date,
        kind: str,
        category_name: str,
        amount: str | float,
        note: str = "",
        transfer_direction: str | None = None,
    ) -> Transaction:
        parsed_date, parsed_amount, category, parsed_direction = self._validated_transaction_fields(
            booking_date=booking_date,
            kind=kind,
            category_name=category_name,
            amount=amount,
            transfer_direction=transfer_direction,
        )
        transaction = Transaction(
            booking_date=parsed_date,
            kind=kind,
            category_id=category.id or 0,
            amount_chf=parsed_amount,
            note=(note or "").strip()[:160],
            transfer_direction=parsed_direction,
        )
        return self.transaction_dao.create(transaction)

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        return self.transaction_dao.get(transaction_id)

    def update_transaction(
        self,
        transaction_id: int,
        booking_date: str | date,
        kind: str,
        category_name: str,
        amount: str | float,
        note: str = "",
        transfer_direction: str | None = None,
    ) -> Transaction:
        parsed_date, parsed_amount, category, parsed_direction = self._validated_transaction_fields(
            booking_date=booking_date,
            kind=kind,
            category_name=category_name,
            amount=amount,
            transfer_direction=transfer_direction,
        )
        updated = self.transaction_dao.update(
            transaction_id=transaction_id,
            booking_date=parsed_date,
            kind=kind,
            category_id=category.id or 0,
            amount_chf=parsed_amount,
            note=(note or "").strip()[:160],
            transfer_direction=parsed_direction,
        )
        if updated is None:
            raise ValidationError("Die Buchung wurde nicht gefunden.")
        return updated

    def delete_transaction(self, transaction_id: int) -> bool:
        return self.transaction_dao.delete(transaction_id)

    def save_plan(
        self,
        year: int,
        month: int,
        planned_income: str | float,
        planned_expenses: str | float,
        savings_goal: str | float,
    ) -> MonthlyBudget:
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
        expenses = 0.0
        transfer_to_savings = 0.0
        transfer_to_budget = 0.0
        category_expenses: Dict[str, float] = {}

        for transaction in transactions:
            category_name = transaction.category.name if transaction.category else "Unbekannt"

            if transaction.kind == "Umbuchung":
                normalized_direction = self._normalize_transfer_direction(transaction.transfer_direction)
                if normalized_direction == TRANSFER_TO_BUDGET:
                    transfer_to_budget = round(transfer_to_budget + transaction.amount_chf, 2)
                else:
                    transfer_to_savings = round(transfer_to_savings + transaction.amount_chf, 2)
                continue

            if transaction.kind != "Ausgabe":
                continue

            if category_name == SAVINGS_CATEGORY:
                transfer_to_savings = round(transfer_to_savings + transaction.amount_chf, 2)
                continue

            expenses = round(expenses + transaction.amount_chf, 2)
            category_expenses[category_name] = round(
                category_expenses.get(category_name, 0.0) + transaction.amount_chf,
                2,
            )

        largest_category = None
        largest_amount = 0.0
        if category_expenses:
            largest_category = max(category_expenses, key=category_expenses.get)
            largest_amount = category_expenses[largest_category]

        plan = self.budget_dao.get(year, month)
        savings_booked = round(transfer_to_savings - transfer_to_budget, 2)
        budget_used = round(expenses + transfer_to_savings - transfer_to_budget, 2)
        planned_expenses = plan.planned_expenses_chf if plan else 0.0
        remaining_expense_budget = round(planned_expenses - budget_used, 2) if plan else 0.0
        spending_budget_used_pct = round((max(budget_used, 0.0) / planned_expenses) * 100, 1) if planned_expenses else 0.0
        savings_goal_progress_pct = (
            round((max(savings_booked, 0.0) / plan.savings_goal_chf) * 100, 1)
            if plan and plan.savings_goal_chf
            else 0.0
        )
        largest_expense_share_pct = round((largest_amount / expenses) * 100, 1) if expenses else 0.0

        return MonthlySummary(
            year=year,
            month=month,
            income_chf=income,
            expenses_chf=expenses,
            balance_chf=round(income - budget_used, 2),
            largest_expense_category=largest_category,
            largest_expense_chf=largest_amount,
            largest_expense_share_pct=largest_expense_share_pct,
            planned_expenses_chf=planned_expenses,
            remaining_expense_budget_chf=remaining_expense_budget,
            savings_booked_chf=savings_booked,
            transfer_to_savings_chf=transfer_to_savings,
            transfer_to_budget_chf=transfer_to_budget,
            budget_used_chf=budget_used,
            spending_budget_used_pct=spending_budget_used_pct,
            savings_goal_progress_pct=savings_goal_progress_pct,
            category_expenses=category_expenses,
            transactions=transactions,
            plan=plan,
        )

    def _validated_transaction_fields(
        self,
        booking_date: str | date,
        kind: str,
        category_name: str,
        amount: str | float,
        transfer_direction: str | None = None,
    ) -> tuple[date, float, Category, str | None]:
        if kind not in TRANSACTION_KINDS:
            raise ValidationError("Bitte Einnahme, Ausgabe oder Umbuchung auswählen.")

        parsed_date = ValidationService.parse_date(booking_date)
        parsed_amount = ValidationService.parse_money(amount)
        parsed_direction = None

        if kind == "Umbuchung":
            parsed_direction = self._normalize_transfer_direction(transfer_direction)
            if parsed_direction not in TRANSFER_DIRECTIONS:
                raise ValidationError("Bitte eine gültige Umbuchungsrichtung auswählen.")
            category_name = SAVINGS_CATEGORY

        category = self.category_dao.get_by_name(category_name)
        if category is None:
            raise ValidationError("Bitte eine gültige Kategorie auswählen.")
        return parsed_date, parsed_amount, category, parsed_direction

    @staticmethod
    def _normalize_transfer_direction(direction: str | None) -> str:
        if not direction:
            return TRANSFER_TO_SAVINGS
        return TRANSFER_DIRECTION_ALIASES.get(direction, direction)

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
