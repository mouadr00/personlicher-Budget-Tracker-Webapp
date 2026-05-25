from datetime import date

from budget_tracker_app.data_access.dao import CategoryDAO, MonthlyBudgetDAO, TransactionDAO
from budget_tracker_app.domain.models import Transaction


def test_db_default_seed_contains_categories_budget_and_demo_bookings(database):
    categories = CategoryDAO(database.engine).list_all()
    names = [category.name for category in categories]
    may_rows = TransactionDAO(database.engine).list_for_period(date(2026, 5, 1), date(2026, 6, 1))
    may_plan = MonthlyBudgetDAO(database.engine).get(2026, 5)

    assert "Lebensmittel" in names
    assert "Gehalt" in names
    assert "Miete" in names
    assert len(may_rows) >= 10
    assert any(row.kind == "Umbuchung" and row.transfer_direction == "Budget zu Sparkonto" for row in may_rows)
    assert may_plan is not None


def test_db_saving_transaction_persists_booking_and_category(database):
    category = CategoryDAO(database.engine).get_by_name("Miete")
    transaction_dao = TransactionDAO(database.engine)

    transaction_dao.create(
        Transaction(
            booking_date=date(2030, 5, 1),
            kind="Ausgabe",
            category_id=category.id,
            amount_chf=1200.00,
            note="Mai-Miete",
        )
    )
    rows = transaction_dao.list_for_period(date(2030, 5, 1), date(2030, 6, 1))

    assert len(rows) == 1
    assert rows[0].category.name == "Miete"
    assert rows[0].amount_chf == 1200.00


def test_db_empty_month_returns_no_transactions(database):
    rows = TransactionDAO(database.engine).list_for_period(date(2030, 1, 1), date(2030, 2, 1))

    assert rows == []
