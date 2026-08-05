"""Shared kernel: cross-cutting primitives (Result, UUIDv7, TimeProvider, etc.)."""

from src.shared_kernel.result import Err, Ok, Result
from src.shared_kernel.time_provider import (
    FakeTimeProvider,
    SystemTimeProvider,
    TimeProvider,
)

__all__ = [
    "Err",
    "FakeTimeProvider",
    "Ok",
    "Result",
    "SystemTimeProvider",
    "TimeProvider",
]
