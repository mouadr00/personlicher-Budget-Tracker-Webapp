"""Business logic for transactions, transfers, summaries, and budget plans."""

from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean
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
SAVINGS_CATEGORY = "Sparkonto"
LEGACY_SAVINGS_CATEGORY = "Sparen"


@dataclass
class RecurringExpense:
    name: str
    category: str
    monthly_amount_chf: float
    yearly_amount_chf: float
    months_seen: int


@dataclass
class MonthlySummary:
    year: int
    month: int
    income_chf: float
    expenses_chf: float
    cash_flow_chf: float
    balance_chf: float
    budget_cash_chf: float
    savings_balance_chf: float
    net_worth_chf: float
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
    available_per_day_chf: float
    budget_health_score: int
    budget_health_label: str
    category_expenses: Dict[str, float]
    recurring_expenses: List[RecurringExpense]
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
        cumulative_transactions = self._transactions_until(end)

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

            if category_name in (SAVINGS_CATEGORY, LEGACY_SAVINGS_CATEGORY):
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
        cash_flow = round(income - expenses, 2)
        planned_expenses = plan.planned_expenses_chf if plan else 0.0
        remaining_expense_budget = round(planned_expenses - budget_used, 2) if plan else 0.0
        spending_budget_used_pct = round((max(budget_used, 0.0) / planned_expenses) * 100, 1) if planned_expenses else 0.0
        savings_goal_progress_pct = (
            round((max(savings_booked, 0.0) / plan.savings_goal_chf) * 100, 1)
            if plan and plan.savings_goal_chf
            else 0.0
        )
        largest_expense_share_pct = round((largest_amount / expenses) * 100, 1) if expenses else 0.0
        budget_cash, savings_balance, net_worth = self._cumulative_balances(cumulative_transactions)
        available_per_day = self._available_per_day(year, month, remaining_expense_budget, bool(plan))
        health_score, health_label = self._budget_health(
            has_plan=bool(plan),
            spending_budget_used_pct=spending_budget_used_pct,
            savings_goal_progress_pct=savings_goal_progress_pct,
            cash_flow_chf=cash_flow,
            savings_booked_chf=savings_booked,
            largest_expense_share_pct=largest_expense_share_pct,
        )
        recurring_expenses = self._recurring_expenses(cumulative_transactions)

        return MonthlySummary(
            year=year,
            month=month,
            income_chf=income,
            expenses_chf=expenses,
            cash_flow_chf=cash_flow,
            balance_chf=round(income - budget_used, 2),
            budget_cash_chf=budget_cash,
            savings_balance_chf=savings_balance,
            net_worth_chf=net_worth,
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
            available_per_day_chf=available_per_day,
            budget_health_score=health_score,
            budget_health_label=health_label,
            category_expenses=category_expenses,
            recurring_expenses=recurring_expenses,
            transactions=transactions,
            plan=plan,
        )

    def _transactions_until(self, end: date) -> list[Transaction]:
        if hasattr(self.transaction_dao, "list_until"):
            return self.transaction_dao.list_until(end)
        return self.transaction_dao.list_for_period(date(2000, 1, 1), end)

    def _cumulative_balances(self, transactions: list[Transaction]) -> tuple[float, float, float]:
        budget_cash = 0.0
        savings_balance = 0.0

        for transaction in transactions:
            category_name = transaction.category.name if transaction.category else ""
            if transaction.kind == "Einnahme":
                budget_cash += transaction.amount_chf
            elif transaction.kind == "Umbuchung":
                normalized_direction = self._normalize_transfer_direction(transaction.transfer_direction)
                if normalized_direction == TRANSFER_TO_BUDGET:
                    budget_cash += transaction.amount_chf
                    savings_balance -= transaction.amount_chf
                else:
                    budget_cash -= transaction.amount_chf
                    savings_balance += transaction.amount_chf
            elif category_name in (SAVINGS_CATEGORY, LEGACY_SAVINGS_CATEGORY):
                budget_cash -= transaction.amount_chf
                savings_balance += transaction.amount_chf
            else:
                budget_cash -= transaction.amount_chf

        budget_cash = round(budget_cash, 2)
        savings_balance = round(savings_balance, 2)
        return budget_cash, savings_balance, round(budget_cash + savings_balance, 2)

    @staticmethod
    def _available_per_day(year: int, month: int, remaining_budget: float, has_plan: bool) -> float:
        if not has_plan:
            return 0.0

        today = date.today()
        last_day = monthrange(year, month)[1]
        if (year, month) == (today.year, today.month):
            days_left = max(last_day - today.day + 1, 1)
        elif (year, month) > (today.year, today.month):
            days_left = last_day
        else:
            days_left = 0

        return round(remaining_budget / days_left, 2) if days_left else 0.0

    @staticmethod
    def _budget_health(
        *,
        has_plan: bool,
        spending_budget_used_pct: float,
        savings_goal_progress_pct: float,
        cash_flow_chf: float,
        savings_booked_chf: float,
        largest_expense_share_pct: float,
    ) -> tuple[int, str]:
        score = 100
        if not has_plan:
            score -= 20
        elif spending_budget_used_pct > 100:
            score -= 35
        elif spending_budget_used_pct >= 80:
            score -= 15

        if has_plan and savings_goal_progress_pct < 50:
            score -= 12
        if cash_flow_chf < 0:
            score -= 20
        if savings_booked_chf < 0:
            score -= 10
        if largest_expense_share_pct >= 45:
            score -= 8

        score = max(0, min(100, score))
        if score >= 80:
            label = "Stark"
        elif score >= 60:
            label = "Okay"
        elif score >= 40:
            label = "Achtung"
        else:
            label = "Kritisch"
        return score, label

    def _recurring_expenses(self, transactions: list[Transaction]) -> list[RecurringExpense]:
        grouped: dict[tuple[str, str], list[Transaction]] = defaultdict(list)
        excluded_categories = {"Lebensmittel", "Freizeit", "Sonstiges", SAVINGS_CATEGORY, LEGACY_SAVINGS_CATEGORY}

        for transaction in transactions:
            if transaction.kind != "Ausgabe" or not transaction.category:
                continue
            category_name = transaction.category.name
            if category_name in excluded_categories:
                continue
            key = (category_name, (transaction.note or category_name).strip().lower())
            grouped[key].append(transaction)

        recurring: list[RecurringExpense] = []
        for (category_name, note), rows in grouped.items():
            months_seen = {(row.booking_date.year, row.booking_date.month) for row in rows}
            if len(months_seen) < 3:
                continue
            amounts = [row.amount_chf for row in rows]
            average_amount = mean(amounts)
            if max(amounts) - min(amounts) > max(20.0, average_amount * 0.15):
                continue
            display_name = note.title() if note and note != category_name.lower() else category_name
            recurring.append(
                RecurringExpense(
                    name=display_name,
                    category=category_name,
                    monthly_amount_chf=round(average_amount, 2),
                    yearly_amount_chf=round(average_amount * 12, 2),
                    months_seen=len(months_seen),
                )
            )

        return sorted(recurring, key=lambda item: item.yearly_amount_chf, reverse=True)[:5]

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
