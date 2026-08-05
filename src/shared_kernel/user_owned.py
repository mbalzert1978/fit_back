"""IUserOwned protocol and mixin for ownership-based data access control."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


class IUserOwned(Protocol):
    """Protocol für Aggregate mit User-Ownership.

    Setzt voraus, dass jedes IUserOwned-Aggregate eine user_id besitzt.
    Repositories, die diesen Protocol implementieren, MÜSSEN auf UserId filtern,
    um Datenlecks zwischen Users zu verhindern.
    """

    @property
    def user_id(self) -> UUID:
        """Die UUID des Benutzers, dem dieses Aggregate gehört."""
        ...


@dataclass(frozen=True, slots=True)
class UserOwnedMixin:
    """Mixin-Dataclass für user-owned Aggregate.

    Stellt die user_id-Eigenschaft bereit und satisfiest das IUserOwned-Protocol.
    """

    user_id: UUID
