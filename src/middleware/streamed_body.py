"""Der Antwortkoerper aus der Middleware-Kette - einmal vollstaendig gelesen.

Warum es dieses Modul gibt: `BaseHTTPMiddleware` reicht jede Antwort aus der
Kette als `starlette.middleware.base._StreamingResponse` weiter - auch die, die
weiter innen ein `JSONResponse` war. Deren Rumpf steht nur ueber
`body_iterator` zur Verfuegung, und nur genau einmal.

Dieser Typ ist privat, und er erbt in Starlette 1.3.1 **direkt von `Response`**,
nicht von `StreamingResponse`. Ein `isinstance(response, StreamingResponse)`
traegt hier also nicht - und `Response` selbst kennt kein `body_iterator`. Was
eine Middleware tatsaechlich vor sich hat, traegt in Starlette damit keinen
oeffentlichen Namen; die Annotation `Response` ist zu weit, jede engere waere
ein Griff in fremde Interna.

Hier bekommt die Sache einen Namen - nicht als Nachbau der fremden Klasse,
sondern als das, was die Middlewares von ihr brauchen: ein einmal lesbarer
Strom von Byte-Stuecken. `IdempotencyKeyMiddleware` und
`ResponseEnvelopeMiddleware` stellen dieselbe Frage; sie wird deshalb an einer
Stelle beantwortet statt in beiden Dateien erneut.
"""

from collections.abc import AsyncIterable
from typing import Protocol, runtime_checkable

from starlette.responses import Response

__all__ = ["StreamedBody", "read_streamed_body"]


@runtime_checkable
class StreamedBody(Protocol):
    """Eine Antwort, deren Rumpf nur als Strom von Byte-Stuecken zu haben ist.

    Kein `@final`: ein Protocol beschreibt Fremdtypen, die es nicht kennt - das
    ist genau der Fall, in dem Vererbung (hier: strukturelle) vorgesehen ist.

    `AsyncIterable[bytes]` und nicht Starlettes weiteres `AsyncContentStream`
    (`str | bytes | memoryview`): das Protocol sagt, was der Leser braucht, und
    der fuegt die Stuecke zu `bytes` zusammen. Was `BaseHTTPMiddleware`
    einspeist, sind die `body`-Felder der ASGI-Nachrichten `http.response.body`
    - Bytes.
    """

    body_iterator: AsyncIterable[bytes]


async def read_streamed_body(response: Response) -> bytes:
    """Sammle den Rumpf der Antwort ein - vollstaendig und genau einmal.

    Args:
        response: Die Antwort, die `call_next` aus der Kette geliefert hat.

    Returns:
        Den vollstaendigen Rumpf. Der Strom ist danach erschoepft; wer diese
        Bytes noch ausliefern will, baut eine neue Antwort darum.

    Raises:
        TypeError: Wenn die Antwort keinen `body_iterator` traegt. Das kann nur
            eintreten, wenn `BaseHTTPMiddleware` seine Antworten nicht mehr als
            `_StreamingResponse` weiterreicht - die Annahme dieses Moduls waere
            dann durch ein Starlette-Update ungueltig geworden. Bisher lief
            derselbe Fall in ein `AttributeError` aus dem Inneren der Schleife:
            dasselbe Scheitern an derselben Stelle, nur benennt es das Symptom
            statt der Ursache. Aufgefangen wird hier so wenig wie vorher.

    """
    if not isinstance(response, StreamedBody):
        msg = (
            f"{type(response).__name__} hat kein `body_iterator` - "
            "BaseHTTPMiddleware liefert seine Antworten nicht mehr als Strom."
        )
        raise TypeError(msg)
    return b"".join([chunk async for chunk in response.body_iterator])
