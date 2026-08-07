"""Tagged Union AccountStatus - jeder Fall traegt seine eigenen Daten, kein Enum."""

from dataclasses import dataclass
from typing import assert_never, final

from src.contexts.shared_kernel import Timestamp

__all__ = [
    "AccountStatus",
    "Active",
    "PendingDeletion",
    "Suspended",
    "account_status_tag",
]


@final
@dataclass(frozen=True, slots=True)
class Active:
    """Konto ist regulaer nutzbar."""


@final
@dataclass(frozen=True, slots=True)
class Suspended:
    """Konto ist administrativ gesperrt."""


@final
@dataclass(frozen=True, slots=True)
class PendingDeletion:
    """Loeschung beantragt - der Fall traegt sein Wirksamkeitsdatum selbst."""

    effective_at: Timestamp


type AccountStatus = Active | Suspended | PendingDeletion


def account_status_tag(status: AccountStatus) -> str:
    """Bilde den Kontostatus auf seinen Diskriminator ab - nur an Aussengrenzen."""
    match status:
        case Active():
            return "active"
        case Suspended():
            return "suspended"
        case PendingDeletion():
            return "pending-deletion"
        case _:
            assert_never(status)
