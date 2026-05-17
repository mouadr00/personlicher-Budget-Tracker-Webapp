"""Application wiring for the NiceGUI budget tracker."""

from __future__ import annotations

from typing import Optional

from nicegui import ui

from .data_access.dao import CategoryDAO, MonthlyBudgetDAO, TransactionDAO, UserAccountDAO
from .data_access.db import Database
from .services.budget_service import BudgetService
from .services.password_service import PasswordService
from .services.report_service import ReportService
from .ui.controllers import AuthController, BudgetController, CategoryController
from .ui.pages import Pages


class BudgetTrackerApplication:
    """Composition root for database, services, controllers, and pages."""

    def __init__(self, database: Optional[Database] = None, report_dir: str = "./data/reports") -> None:
        self.database = database or Database()
        self.database.init_schema_and_seed()

        engine = self.database.engine
        self.category_dao = CategoryDAO(engine)
        self.transaction_dao = TransactionDAO(engine)
        self.budget_dao = MonthlyBudgetDAO(engine)
        self.user_dao = UserAccountDAO(engine)

        self.password_service = PasswordService()
        self.report_service = ReportService(report_dir=report_dir)
        self.budget_service = BudgetService(
            transaction_dao=self.transaction_dao,
            category_dao=self.category_dao,
            budget_dao=self.budget_dao,
        )

        self.auth_controller = AuthController(
            user_dao=self.user_dao,
            password_service=self.password_service,
        )
        self.budget_controller = BudgetController(
            budget_service=self.budget_service,
            report_service=self.report_service,
        )
        self.category_controller = CategoryController(category_dao=self.category_dao)
        self.pages = Pages(
            auth_controller=self.auth_controller,
            budget_controller=self.budget_controller,
            category_controller=self.category_controller,
        )

    def run(self, host: str = "0.0.0.0", port: int = 8080, reload: bool = False) -> None:
        self.pages.register()
        ui.run(
            host=host,
            port=port,
            reload=reload,
            title="Budget Tracker",
            storage_secret="budget-tracker-local-secret",
        )
