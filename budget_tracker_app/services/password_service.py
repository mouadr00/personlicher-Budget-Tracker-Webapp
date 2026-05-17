"""Password hashing and verification."""

from __future__ import annotations

import hashlib


class PasswordService:
    """Small password service using SHA-256 like the original CLI project."""

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def validate_new_password(self, password: str) -> None:
        if len(password or "") < 6:
            raise ValueError("Das Passwort muss mindestens 6 Zeichen lang sein.")

    def verify(self, password: str, password_hash: str) -> bool:
        return self.hash_password(password) == password_hash
