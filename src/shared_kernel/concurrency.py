"""Optimistic concurrency control via RowVersion and If-Match headers."""

from dataclasses import dataclass
from typing import final

from src.shared_kernel.exceptions import DomainException
from src.shared_kernel.result import Err, Ok, Result


@final
@dataclass(frozen=True, slots=True)
class RowVersion:
    """Value Object für Optimistic-Concurrency-Control via PostgreSQL xmin.

    Wird vom ORM aus dem PostgreSQL xmin-Feld (interne Row-Version) extrahiert
    und im If-Match-Header übertragen. Beim Update muss der Client die aktuelle
    RowVersion mitliefern; unterscheidet sie sich von der Serverversion,
    wird ein 409 Conflict geworfen.
    """

    xmin: int
    """Interne PostgreSQL-Row-Version (xmin aus system columns)."""

    @classmethod
    def from_xmin(cls, xmin: int) -> RowVersion:
        """Erstelle eine RowVersion aus PostgreSQL xmin.

        Args:
            xmin: Der xmin-Wert aus PostgreSQL system columns.

        Returns:
            Eine neue RowVersion.
        """
        if xmin < 0:
            msg = f"xmin must be non-negative, got {xmin}"
            raise ValueError(msg)
        return cls(xmin=xmin)

    def __str__(self) -> str:
        """Serialisiere zu String für If-Match-Header."""
        return str(self.xmin)

    @classmethod
    def from_if_match(cls, if_match: str | None) -> Result[RowVersion, str] | None:
        """Parse RowVersion aus If-Match-Header.

        Args:
            if_match: Der Wert des If-Match-Headers, oder None.

        Returns:
            Ok(RowVersion) falls Header gültig, Err(str) bei Parsing-Fehler,
            oder None falls Header nicht gesetzt.
        """
        if if_match is None:
            return None
        try:
            xmin = int(if_match)
            return Ok(cls.from_xmin(xmin))
        except ValueError:
            msg = f"Invalid If-Match header: {if_match}"
            return Err(msg)


@final
class ConcurrencyConflictError(DomainException):
    """Fehlgeschlagenes Update aufgrund veralterter RowVersion.

    Wird geworfen, wenn der Client einen Update mit veralteter oder fehlender
    RowVersion versucht und die Serverversion unterscheidet sich.
    HTTP-Status: 409 Conflict.
    """

    error_type: str = "https://api.example/errors/concurrency-conflict"
    http_status: int = 409
    title: str = "Concurrency Conflict"

    def __init__(
        self,
        detail: str,
        current_version: RowVersion,
        *,
        instance: str | None = None,
    ) -> None:
        """Initialisiere Concurrency-Fehler.

        Args:
            detail: Fehlermeldung für den Client.
            current_version: Die aktuelle Server-RowVersion.
            instance: Optional: URI der betroffenen Ressource.
        """
        super().__init__(detail, instance=instance)
        self.current_version = current_version
