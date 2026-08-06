"""Internes Command des Use Case RegisterUser - fertig geparste Value Objects."""

from dataclasses import dataclass, field
from typing import final

from src.contexts.identity.domain import (
    DisplayName,
    Email,
    Locale,
    Password,
    UserTimeZone,
)

__all__ = ["RegisterUserCommand"]


@final
@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    """Was der Handler braucht - kein Primitiv mehr, kein DTO.

    Die Konstruktion ist infallibel: die Collect-all-Validierung ist eine Ebene
    hoeher bereits gelaufen, also braucht das Command keinen eigenen Fehlerkanal
    (.rules/python/python-rule-pattern.md).
    """

    email: Email
    password: Password = field(repr=False)
    display_name: DisplayName
    locale: Locale
    time_zone: UserTimeZone
