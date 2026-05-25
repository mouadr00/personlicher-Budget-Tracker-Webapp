"""Repository/DAO classes for database access."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..domain.models import Category, MonthlyBudget, Transaction, UserAccount


class BaseDAO:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def session(self) -> Session:
        return Session(self.engine)


class CategoryDAO(BaseDAO):
    def list_all(self) -> List[Category]:
        with self.session() as session:
            return list(session.exec(select(Category).order_by(Category.name)).all())

    def get_by_name(self, name: str) -> Optional[Category]:
        with self.session() as session:
            statement = select(Category).where(Category.name == name.strip())
            return session.exec(statement).first()

    def create(self, name: str) -> Category:
        with self.session() as session:
            category = Category(name=name.strip())
            session.add(category)
            session.commit()
            session.refresh(category)
            return category


class TransactionDAO(BaseDAO):
    def create(self, transaction: Transaction) -> Transaction:
        with self.session() as session:
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction

    def get(self, transaction_id: int) -> Optional[Transaction]:
        with self.session() as session:
            statement = (
                select(Transaction)
                .where(Transaction.id == transaction_id)
                .options(selectinload(Transaction.category))
            )
            return session.exec(statement).first()

    def update(
        self,
        transaction_id: int,
        booking_date: date,
        kind: str,
        category_id: int,
        amount_chf: float,
        note: str,
        transfer_direction: str | None = None,
    ) -> Optional[Transaction]:
        with self.session() as session:
            transaction = session.get(Transaction, transaction_id)
            if transaction is None:
                return None

            transaction.booking_date = booking_date
            transaction.kind = kind
            transaction.category_id = category_id
            transaction.amount_chf = amount_chf
            transaction.note = note
            transaction.transfer_direction = transfer_direction
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction

    def delete(self, transaction_id: int) -> bool:
        with self.session() as session:
            transaction = session.get(Transaction, transaction_id)
            if transaction is None:
                return False
            session.delete(transaction)
            session.commit()
            return True

    def list_for_period(self, start: date, end: date) -> List[Transaction]:
        with self.session() as session:
            statement = (
                select(Transaction)
                .where(Transaction.booking_date >= start)
                .where(Transaction.booking_date < end)
                .options(selectinload(Transaction.category))
                .order_by(Transaction.booking_date.desc(), Transaction.id.desc())
            )
            return list(session.exec(statement).all())

    def list_until(self, end: date) -> List[Transaction]:
        with self.session() as session:
            statement = (
                select(Transaction)
                .where(Transaction.booking_date < end)
                .options(selectinload(Transaction.category))
                .order_by(Transaction.booking_date.asc(), Transaction.id.asc())
            )
            return list(session.exec(statement).all())


class MonthlyBudgetDAO(BaseDAO):
    def get(self, year: int, month: int) -> Optional[MonthlyBudget]:
        with self.session() as session:
            statement = select(MonthlyBudget).where(
                MonthlyBudget.year == year,
                MonthlyBudget.month == month,
            )
            return session.exec(statement).first()

    def save(self, year: int, month: int, planned_income: float, planned_expenses: float, savings_goal: float) -> MonthlyBudget:
        with self.session() as session:
            statement = select(MonthlyBudget).where(
                MonthlyBudget.year == year,
                MonthlyBudget.month == month,
            )
            budget = session.exec(statement).first()
            if budget is None:
                budget = MonthlyBudget(year=year, month=month)
                session.add(budget)

            budget.planned_income_chf = planned_income
            budget.planned_expenses_chf = planned_expenses
            budget.savings_goal_chf = savings_goal
            session.commit()
            session.refresh(budget)
            return budget


class UserAccountDAO(BaseDAO):
    def get_admin(self) -> Optional[UserAccount]:
        with self.session() as session:
            statement = select(UserAccount).where(UserAccount.username == "admin")
            return session.exec(statement).first()

    def create_admin(self, password_hash: str) -> UserAccount:
        with self.session() as session:
            user = UserAccount(username="admin", password_hash=password_hash)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_password(self, password_hash: str) -> None:
        with self.session() as session:
            statement = select(UserAccount).where(UserAccount.username == "admin")
            user = session.exec(statement).first()
            if user is None:
                user = UserAccount(username="admin", password_hash=password_hash)
                session.add(user)
            else:
                user.password_hash = password_hash
            session.commit()
