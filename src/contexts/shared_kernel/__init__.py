"""Shared Kernel: die Bausteine, die jeder Context teilt.

Haengt ausschliesslich an der stdlib - maschinell abgesichert durch den
`domain-purity`-Contract in setup.cfg. Was FastAPI, Pydantic, Starlette oder
asyncpg braucht, gehoert nicht hierher, sondern nach `src/api/` (HTTP-Rand) oder
`src/infrastructure/` (geteilte Infrastruktur).
"""

from src.contexts.shared_kernel.result import Err, Ok, Result
from src.contexts.shared_kernel.text_rules import NotBlankError, TextIsEmpty, not_blank
from src.contexts.shared_kernel.time_provider import (
    FakeTimeProvider,
    SystemTimeProvider,
    TimeProvider,
)
from src.contexts.shared_kernel.timestamp import Timestamp
from src.contexts.shared_kernel.user_owned import IUserOwned

__all__ = [
    "Err",
    "FakeTimeProvider",
    "IUserOwned",
    "NotBlankError",
    "Ok",
    "Result",
    "SystemTimeProvider",
    "TextIsEmpty",
    "TimeProvider",
    "Timestamp",
    "not_blank",
]
