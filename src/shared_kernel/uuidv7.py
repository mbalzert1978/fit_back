"""UUIDv7 generator for sortable, time-based unique identifiers."""

from uuid import UUID
from uuid import uuid7 as _uuid7


def uuid7() -> UUID:
    """Generiere eine zeitsortierte UUID (RFC 9562 Version 7).

    UUIDv7 ist eine zeitsortierte UUID, die einen Millisekunden-Zeitstempel
    enthält und monoton aufsteigende Werte erzeugt. Dies ist ideal für
    Datenbankindizes, da sequenzielle Inserts die Index-Lokalität behalten.

    Returns:
        Eine neue UUID (Version 7).
    """
    return _uuid7()
