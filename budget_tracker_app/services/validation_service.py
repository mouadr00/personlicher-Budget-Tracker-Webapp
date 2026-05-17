"""Input validation helpers."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation


class ValidationError(ValueError):
    """Raised when user input cannot be accepted."""


class ValidationService:
    """Validates and normalizes input values."""

    @staticmethod
    def parse_date(value: str | date) -> date:
        if isinstance(value, date):
            return value
        if not value:
            return date.today()
        try:
            if "-" in value:
                return datetime.strptime(value, "%Y-%m-%d").date()
            return datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError as exc:
            raise ValidationError("Bitte ein gültiges Datum eingeben.") from exc

    @staticmethod
    def parse_money(value: str | float | int | Decimal) -> float:
        text = str(value).replace(",", ".").strip()
        try:
            amount = Decimal(text)
        except InvalidOperation as exc:
            raise ValidationError("Bitte einen gültigen Betrag eingeben.") from exc

        if amount <= 0:
            raise ValidationError("Der Betrag muss grösser als 0 sein.")
        if amount.as_tuple().exponent < -2:
            raise ValidationError("Maximal zwei Nachkommastellen sind erlaubt.")
        if amount > Decimal("1000000"):
            raise ValidationError("Der Betrag ist zu hoch.")
        return float(amount)

    @staticmethod
    def parse_plan_money(value: str | float | int | Decimal) -> float:
        text = str(value or "0").replace(",", ".").strip()
        try:
            amount = Decimal(text)
        except InvalidOperation as exc:
            raise ValidationError("Bitte gültige Planwerte eingeben.") from exc
        if amount < 0:
            raise ValidationError("Planwerte dürfen nicht negativ sein.")
        if amount.as_tuple().exponent < -2:
            raise ValidationError("Maximal zwei Nachkommastellen sind erlaubt.")
        return float(amount)

    @staticmethod
    def clean_category_name(name: str) -> str:
        cleaned = " ".join((name or "").strip().split())
        if len(cleaned) < 2:
            raise ValidationError("Die Kategorie muss mindestens zwei Zeichen haben.")
        if len(cleaned) > 60:
            raise ValidationError("Die Kategorie ist zu lang.")
        return cleaned.title()
