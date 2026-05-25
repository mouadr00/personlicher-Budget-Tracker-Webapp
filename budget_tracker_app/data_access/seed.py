"""Initial data used by the app."""

from calendar import monthrange
from datetime import date

from sqlmodel import Session, select

from ..domain.models import Category, MonthlyBudget, Transaction


DEMO_YEAR = 2026
MIN_SEEDED_TRANSACTIONS = 100

DEFAULT_CATEGORIES = [
    "Lebensmittel",
    "Gehalt",
    "Miete",
    "Versicherung",
    "Freizeit",
    "Transport",
    "Sparkonto",
    "Schulden",
    "Sonstiges",
]


class CategorySeeder:
    """Seeds categories plus realistic starter budget data."""

    def seed(self, session: Session) -> None:
        category_ids = self._ensure_categories(session)
        self._seed_monthly_budgets(session)
        self._seed_transactions(session, category_ids)

    def _ensure_categories(self, session: Session) -> dict[str, int]:
        categories: dict[str, Category] = {}
        for name in DEFAULT_CATEGORIES:
            category = session.exec(select(Category).where(Category.name == name)).first()
            if category is None and name == "Sparkonto":
                legacy_category = session.exec(select(Category).where(Category.name == "Sparen")).first()
                if legacy_category is not None:
                    legacy_category.name = "Sparkonto"
                    session.add(legacy_category)
                    session.flush()
                    category = legacy_category
            if category is None:
                category = Category(name=name)
                session.add(category)
                session.flush()
            categories[name] = category

        return {name: category.id or 0 for name, category in categories.items()}

    def _seed_monthly_budgets(self, session: Session) -> None:
        existing_plan = session.exec(select(MonthlyBudget).where(MonthlyBudget.year == DEMO_YEAR)).first()
        if existing_plan is not None:
            return

        for month in range(1, 13):
            planned_income = 2450.00
            planned_expenses = 2025.00
            savings_goal = 180.00

            if month in (2, 9):
                planned_expenses = 2425.00
                savings_goal = 80.00

            session.add(
                MonthlyBudget(
                    year=DEMO_YEAR,
                    month=month,
                    planned_income_chf=planned_income,
                    planned_expenses_chf=planned_expenses,
                    savings_goal_chf=savings_goal,
                )
            )

    def _seed_transactions(self, session: Session, category_ids: dict[str, int]) -> None:
        existing_transaction = session.exec(select(Transaction)).first()
        if existing_transaction is not None:
            return

        total_seeded = 0
        for month in range(1, 13):
            last_day = monthrange(DEMO_YEAR, month)[1]
            entries = [
                (1, "Einnahme", "Gehalt", 1850.00, "Teilzeitlohn Campusjob"),
                (3, "Einnahme", "Sonstiges", 420.00, "Stipendium"),
                (4, "Ausgabe", "Miete", 780.00, "WG-Zimmer"),
                (5, "Ausgabe", "Versicherung", 145.00, "Krankenversicherung"),
                (7, "Umbuchung", "Sparkonto", 120.00, "Notgroschen", "Budget zu Sparkonto"),
                (9, "Ausgabe", "Transport", 62.00, "Studenten-ÖV-Abo"),
                (11, "Ausgabe", "Freizeit", 58.00, "Kino und Cafe"),
                (13, "Ausgabe", "Lebensmittel", 86.70, "Wocheneinkauf"),
                (17, "Ausgabe", "Lebensmittel", 79.90, "Wocheneinkauf"),
                (19, "Ausgabe", "Schulden", 95.00, "BAföG-Rücklage"),
                (22, "Ausgabe", "Freizeit", 42.00, "Sportverein"),
                (24, "Ausgabe", "Lebensmittel", 91.40, "Wocheneinkauf"),
                (27, "Ausgabe", "Transport", 18.60, "Spätbus"),
                (29, "Ausgabe", "Sonstiges", 36.50, "Lernmaterial"),
            ]

            if month in (2, 9):
                entries.append((15, "Ausgabe", "Sonstiges", 320.00, "Semestergebühren"))

            for entry in entries:
                day, kind, category_name, amount, note, *direction = entry
                session.add(
                    Transaction(
                        booking_date=date(DEMO_YEAR, month, min(day, last_day)),
                        kind=kind,
                        category_id=category_ids[category_name],
                        amount_chf=amount,
                        note=note,
                        transfer_direction=direction[0] if direction else None,
                    )
                )
                total_seeded += 1

        if total_seeded < MIN_SEEDED_TRANSACTIONS:
            raise ValueError(
                f"Seed data must contain at least {MIN_SEEDED_TRANSACTIONS} transactions, got {total_seeded}."
            )
