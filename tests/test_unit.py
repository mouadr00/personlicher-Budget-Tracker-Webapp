from datetime import date

import pytest

from budget_tracker_app.domain.models import Category, MonthlyBudget, Transaction
from budget_tracker_app.services.budget_service import BudgetService
from budget_tracker_app.services.password_service import PasswordService
from budget_tracker_app.services.validation_service import ValidationError, ValidationService


class FakeTransactionDAO:
    def __init__(self, transactions):
        self.transactions = transactions

    def list_for_period(self, start, end):
        return [transaction for transaction in self.transactions if start <= transaction.booking_date < end]


class FakeCategoryDAO:
    def list_all(self):
        return []


class FakeBudgetDAO:
    def get(self, year, month):
        return MonthlyBudget(
            year=year,
            month=month,
            planned_income_chf=3500.00,
            planned_expenses_chf=1800.00,
            savings_goal_chf=100.00,
        )


def make_transaction(day, kind, category_name, amount, transfer_direction=None):
    category = Category(id=1, name=category_name)
    transaction = Transaction(
        id=day,
        booking_date=date(2026, 5, day),
        kind=kind,
        category_id=category.id,
        amount_chf=amount,
        transfer_direction=transfer_direction,
    )
    transaction.category = category
    return transaction


def test_unit_money_parser_accepts_comma_amounts():
    assert ValidationService.parse_money("42,50") == 42.50


def test_unit_money_parser_rejects_more_than_two_decimals():
    with pytest.raises(ValidationError):
        ValidationService.parse_money("10.999")


def test_unit_plan_money_rejects_negative_values():
    with pytest.raises(ValidationError):
        ValidationService.parse_plan_money("-1")


def test_unit_date_parser_accepts_swiss_date_format():
    assert ValidationService.parse_date("17.05.2026") == date(2026, 5, 17)


def test_unit_password_hash_can_be_verified():
    service = PasswordService()
    password_hash = service.hash_password("budget123")

    assert service.verify("budget123", password_hash)
    assert not service.verify("wrong-password", password_hash)


def test_unit_monthly_summary_calculates_totals_and_largest_category():
    transactions = [
        make_transaction(1, "Einnahme", "Gehalt", 3500.00),
        make_transaction(2, "Ausgabe", "Miete", 1200.00),
        make_transaction(3, "Ausgabe", "Lebensmittel", 80.50),
        make_transaction(4, "Umbuchung", "Sparen", 40.00, "Budget zu Sparkonto"),
        make_transaction(5, "Umbuchung", "Sparen", 10.00, "Sparkonto zu Budget"),
    ]
    service = BudgetService(
        transaction_dao=FakeTransactionDAO(transactions),
        category_dao=FakeCategoryDAO(),
        budget_dao=FakeBudgetDAO(),
    )

    summary = service.monthly_summary(2026, 5)

    assert summary.income_chf == 3500.00
    assert summary.expenses_chf == 1280.50
    assert summary.balance_chf == 2189.50
    assert summary.largest_expense_category == "Miete"
    assert summary.largest_expense_share_pct == 93.7
    assert summary.savings_booked_chf == 30.00
    assert summary.transfer_to_savings_chf == 40.00
    assert summary.transfer_to_budget_chf == 10.00
    assert summary.budget_used_chf == 1310.50
    assert summary.savings_goal_progress_pct == 30.0
