"""IUserOwned protocol for ownership-based data access control."""

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
