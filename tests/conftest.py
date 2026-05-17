from pathlib import Path
from uuid import uuid4

import pytest

from budget_tracker_app.data_access.dao import CategoryDAO, MonthlyBudgetDAO, TransactionDAO
from budget_tracker_app.data_access.db import Database
from budget_tracker_app.services.budget_service import BudgetService
from budget_tracker_app.services.report_service import ReportService


@pytest.fixture()
def test_data_dir() -> Path:
    path = Path(__file__).resolve().parents[1] / ".test-data" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture()
def database(test_data_dir: Path) -> Database:
    db_path = (test_data_dir / "test.db").as_posix()
    db = Database(database_url=f"sqlite:///{db_path}")
    db.init_schema_and_seed()
    return db


@pytest.fixture()
def budget_service(database: Database) -> BudgetService:
    engine = database.engine
    return BudgetService(
        transaction_dao=TransactionDAO(engine),
        category_dao=CategoryDAO(engine),
        budget_dao=MonthlyBudgetDAO(engine),
    )


@pytest.fixture()
def report_service(test_data_dir: Path) -> ReportService:
    return ReportService(report_dir=str(test_data_dir / "reports"))
