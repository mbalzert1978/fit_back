"""Der Antwortkoerper aus der Middleware-Kette - einmal vollstaendig gelesen.

`BaseHTTPMiddleware` reicht jede Antwort als `_StreamingResponse` weiter. Der Typ ist
privat und erbt in Starlette 1.3.1 direkt von `Response`, nicht von `StreamingResponse` -
er hat also keinen oeffentlichen Namen, gegen den sich pruefen liesse. Das Protocol hier
nennt stattdessen das, was die Middlewares brauchen.
"""

from collections.abc import AsyncIterable
from typing import Protocol, runtime_checkable

from starlette.responses import Response

__all__ = ["StreamedBody", "read_streamed_body"]


@runtime_checkable
class StreamedBody(Protocol):
    """Eine Antwort, deren Rumpf nur als Strom von Byte-Stuecken zu haben ist."""

    body_iterator: AsyncIterable[bytes]


async def read_streamed_body(response: Response) -> bytes:
    """Sammle den Rumpf der Antwort ein - vollstaendig und genau einmal."""
    if not isinstance(response, StreamedBody):
        msg = (
            f"{type(response).__name__} hat kein `body_iterator` - "
            "BaseHTTPMiddleware liefert seine Antworten nicht mehr als Strom."
        )
        raise TypeError(msg)
    return b"".join([chunk async for chunk in response.body_iterator])
