"""Shared Kernel: die Bausteine, die jeder Context teilt.

Haengt ausschliesslich an der stdlib - maschinell abgesichert durch den
`domain-purity`-Contract in setup.cfg. Was FastAPI, Pydantic, Starlette oder
asyncpg braucht, gehoert nicht hierher, sondern nach `src/api/` (HTTP-Rand) oder
`src/shared_infrastructure/` (geteilte Infrastruktur).
"""

from src.shared_kernel.not_empty_string import NotEmptyString, not_blank
from src.shared_kernel.result import Err, Ok, Result
from src.shared_kernel.time_provider import (
    FakeTimeProvider,
    SystemTimeProvider,
    TimeProvider,
)
from src.shared_kernel.timestamp import Timestamp
from src.shared_kernel.user_owned import IUserOwned

__all__ = [
    "Err",
    "FakeTimeProvider",
    "IUserOwned",
    "NotEmptyString",
    "Ok",
    "Result",
    "SystemTimeProvider",
    "TimeProvider",
    "Timestamp",
    "not_blank",
]
