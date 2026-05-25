"""Controllers used by the NiceGUI pages."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from nicegui import app

from ..data_access.dao import CategoryDAO, UserAccountDAO
from ..domain.models import MonthlyBudget, Transaction
from ..services.budget_service import BudgetService, MonthlySummary
from ..services.password_service import PasswordService
from ..services.report_service import ReportService


class AuthController:
    """Handles login state and password changes."""

    def __init__(self, user_dao: UserAccountDAO, password_service: PasswordService) -> None:
        self.user_dao = user_dao
        self.password_service = password_service

    def has_account(self) -> bool:
        return self.user_dao.get_admin() is not None

    def setup_password(self, password: str) -> None:
        self.password_service.validate_new_password(password)
        self.user_dao.create_admin(self.password_service.hash_password(password))
        app.storage.user["authenticated"] = True

    def login(self, password: str) -> bool:
        user = self.user_dao.get_admin()
        if user is None:
            return False
        ok = self.password_service.verify(password, user.password_hash)
        app.storage.user["authenticated"] = ok
        return ok

    def logout(self) -> None:
        app.storage.user["authenticated"] = False

    def is_authenticated(self) -> bool:
        return bool(app.storage.user.get("authenticated", False))

    def change_password(self, current_password: str, new_password: str) -> None:
        user = self.user_dao.get_admin()
        if user is None:
            raise ValueError("Es existiert noch kein Passwort.")
        if not self.password_service.verify(current_password, user.password_hash):
            raise ValueError("Das aktuelle Passwort ist falsch.")
        self.password_service.validate_new_password(new_password)
        self.user_dao.update_password(self.password_service.hash_password(new_password))


class BudgetController:
    """Coordinates UI actions for budget data."""

    def __init__(self, budget_service: BudgetService, report_service: ReportService) -> None:
        self.budget_service = budget_service
        self.report_service = report_service

    def categories(self) -> list[str]:
        return self.budget_service.list_categories()

    def add_category(self, name: str) -> str:
        return self.budget_service.add_category(name)

    def add_transaction(
        self,
        booking_date: str | date,
        kind: str,
        category_name: str,
        amount: str | float,
        note: str = "",
        transfer_direction: str | None = None,
    ) -> Transaction:
        return self.budget_service.add_transaction(booking_date, kind, category_name, amount, note, transfer_direction)

    def transaction(self, transaction_id: int) -> Transaction | None:
        return self.budget_service.get_transaction(transaction_id)

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
        return self.budget_service.update_transaction(
            transaction_id,
            booking_date,
            kind,
            category_name,
            amount,
            note,
            transfer_direction,
        )

    def delete_transaction(self, transaction_id: int) -> bool:
        return self.budget_service.delete_transaction(transaction_id)

    def summary(self, year: int, month: int) -> MonthlySummary:
        return self.budget_service.monthly_summary(year, month)

    def save_plan(self, year: int, month: int, planned_income: str | float, planned_expenses: str | float, savings_goal: str | float) -> MonthlyBudget:
        return self.budget_service.save_plan(year, month, planned_income, planned_expenses, savings_goal)

    def export_pdf(self, year: int, month: int) -> Path:
        return self.report_service.create_monthly_pdf(self.summary(year, month))

    def export_csv(self, year: int, month: int) -> Path:
        return self.report_service.create_monthly_csv(self.summary(year, month))


class CategoryController:
    """Controller for category maintenance."""

    def __init__(self, category_dao: CategoryDAO) -> None:
        self.category_dao = category_dao

    def list_categories(self) -> list[str]:
        return [category.name for category in self.category_dao.list_all()]

    def add_category(self, name: str) -> str:
        from ..services.validation_service import ValidationService

        cleaned = ValidationService.clean_category_name(name)
        if self.category_dao.get_by_name(cleaned):
            raise ValueError("Diese Kategorie existiert bereits.")
        self.category_dao.create(cleaned)
        return cleaned
