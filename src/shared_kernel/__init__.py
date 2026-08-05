"""Shared kernel: cross-cutting primitives (Result, UUIDv7, TimeProvider, etc.)."""

from src.shared_kernel.concurrency import (
    ConcurrencyConflictError,
    RowVersion,
)
from src.shared_kernel.result import Err, Ok, Result
from src.shared_kernel.time_provider import (
    FakeTimeProvider,
    SystemTimeProvider,
    TimeProvider,
)
from src.shared_kernel.user_owned import IUserOwned, UserOwnedMixin
from src.shared_kernel.uuidv7 import uuid7

__all__ = [
    "ConcurrencyConflictError",
    "Err",
    "FakeTimeProvider",
    "IUserOwned",
    "Ok",
    "Result",
    "RowVersion",
    "SystemTimeProvider",
    "TimeProvider",
    "UserOwnedMixin",
    "uuid7",
]
