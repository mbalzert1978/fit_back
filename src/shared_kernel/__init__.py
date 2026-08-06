"""Shared kernel: cross-cutting primitives (Result, TimeProvider, etc.)."""

from src.shared_kernel.concurrency import (
    ConcurrencyConflictError,
    RowVersion,
)
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
    "ConcurrencyConflictError",
    "Err",
    "FakeTimeProvider",
    "IUserOwned",
    "NotEmptyString",
    "Ok",
    "Result",
    "RowVersion",
    "SystemTimeProvider",
    "TimeProvider",
    "Timestamp",
    "not_blank",
]
