"""Verdrahtung der Identity-Slices gegen die konkrete Infrastruktur.

Getrennt vom Router, weil der ausschliesslich HTTP gegen Application-DTOs
uebersetzt (CLAUDE.md, "Architektur"). Was hinter der Naht steckt, geht ihn
nichts an.
"""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncConnection

from src.api.composition import request_transaction
from src.contexts.identity.application.register_user import (
    RegisterUserPipeline,
    build_register_user_pipeline,
)
from src.contexts.identity.infrastructure.hashing import Argon2PasswordHasher
from src.contexts.identity.infrastructure.idn import IdnaLabels
from src.contexts.identity.infrastructure.persistence import PostgresUserStore
from src.contexts.identity.infrastructure.tokens import JwtAccessTokens, PostgresSessionTokens
from src.contexts.shared_kernel.time_provider import SystemTimeProvider
from src.infrastructure.outbox.publishers import RegisterUserOutbox

__all__ = ["RegisterUser"]


def _register_user(
    request: Request,
    connection: Annotated[AsyncConnection, Depends(request_transaction)],
) -> RegisterUserPipeline:
    """Baue die Pipeline gegen Postgres, Argon2id und die Outbox.

    `PostgresUserStore`, `PostgresSessionTokens` und `RegisterUserOutbox`
    bekommen **dieselbe** Verbindung - daran haengt, dass Nutzer-Zeile,
    Refresh-Token und Ereignis gemeinsam sichtbar werden. Zwei Verbindungen
    waeren hier ein stiller Bruch der Zusage.

    Das Signaturgeheimnis kommt aus `app.state.settings` und damit aus der
    Umgebung - der Lifespan hat es beim Start gegen `src/settings.py` geprueft.

    Dieselbe Fabrik wie in der Test-API; getauscht wird nur, was hinter der Naht
    steckt.
    """
    return build_register_user_pipeline(
        store=PostgresUserStore(connection),
        hasher=Argon2PasswordHasher(),
        labels=IdnaLabels(),
        events=RegisterUserOutbox(connection),
        sessions=PostgresSessionTokens(
            connection, JwtAccessTokens(request.app.state.settings.jwt_secret)
        ),
        clock=SystemTimeProvider(),
    )


type RegisterUser = Annotated[RegisterUserPipeline, Depends(_register_user)]
