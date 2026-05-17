from datetime import date

from budget_tracker_app.data_access.dao import CategoryDAO, TransactionDAO
from budget_tracker_app.domain.models import Transaction


def test_db_default_categories_are_seeded(database):
    categories = CategoryDAO(database.engine).list_all()
    names = [category.name for category in categories]

    assert "Lebensmittel" in names
    assert "Gehalt" in names
    assert "Miete" in names


def test_db_saving_transaction_persists_booking_and_category(database):
    category = CategoryDAO(database.engine).get_by_name("Miete")
    transaction_dao = TransactionDAO(database.engine)

    transaction_dao.create(
        Transaction(
            booking_date=date(2026, 5, 1),
            kind="Ausgabe",
            category_id=category.id,
            amount_chf=1200.00,
            note="Mai-Miete",
        )
    )
    rows = transaction_dao.list_for_period(date(2026, 5, 1), date(2026, 6, 1))

    assert len(rows) == 1
    assert rows[0].category.name == "Miete"
    assert rows[0].amount_chf == 1200.00


def test_db_empty_month_returns_no_transactions(database):
    rows = TransactionDAO(database.engine).list_for_period(date(2026, 1, 1), date(2026, 2, 1))

    assert rows == []
