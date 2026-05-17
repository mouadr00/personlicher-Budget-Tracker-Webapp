"""SQLite and SQLModel database setup."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, Session, create_engine, select

from ..domain.models import Category
from .seed import CategorySeeder


class Database:
    """Database facade that owns the SQLAlchemy engine."""

    def __init__(self, database_url: Optional[str] = None, *, echo: bool = False) -> None:
        self._database_url = database_url or os.getenv("DATABASE_URL") or self._default_sqlite_url()
        self._engine: Engine = create_engine(
            self._database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
        )

    @staticmethod
    def _default_sqlite_url() -> str:
        Path("data").mkdir(parents=True, exist_ok=True)
        return "sqlite:///data/budget_tracker.db"

    @property
    def engine(self) -> Engine:
        return self._engine

    def init_schema_and_seed(self) -> None:
        SQLModel.metadata.create_all(self._engine)
        with Session(self._engine) as session:
            if session.exec(select(Category)).first() is None:
                CategorySeeder().seed(session)
                session.commit()

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        session = Session(self._engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
