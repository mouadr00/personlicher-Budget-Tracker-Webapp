"""Initial data used by the app."""

from sqlmodel import Session

from ..domain.models import Category


DEFAULT_CATEGORIES = [
    "Lebensmittel",
    "Gehalt",
    "Miete",
    "Versicherung",
    "Freizeit",
    "Transport",
    "Sparen",
    "Schulden",
    "Sonstiges",
]


class CategorySeeder:
    """Seeds the standard categories from the CLI project."""

    def seed(self, session: Session) -> None:
        for name in DEFAULT_CATEGORIES:
            session.add(Category(name=name))
