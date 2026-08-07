"""Eingabe-Validierung des Use Case RegisterUser (Collect-all Rule Pattern)."""

from src.contexts.identity.application.register_user.validators.register_user_rules import (
    build_register_user_rules,
)

__all__ = ["build_register_user_rules"]
