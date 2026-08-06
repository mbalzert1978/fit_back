"""Public Test-API des Slice `register_user`.

Ausgeliefertes Artefakt des Slice, kein Testcode: sie ist die Bedien-Oberflaeche
fuer alles, was den Use Case verhaltensseitig pruefen will
(.rules/python/python-feature-slices.md).

Sie verdrahtet ueber `build_register_user_pipeline` **dieselbe** Pipeline wie die
Produktion - Validierung -> Request-Mapper -> Handler -> Domaene -> Response-Mapper -
und tauscht ausschliesslich an der aeussersten Naht In-Memory-Fakes ein. Zwischen
Naht und Response wird nichts gemockt.

Was sie **nicht** ist: eine Integrations- oder End-to-End-Testebene. Postgres via
Testcontainers und HTTP gegen die laufende App sind eine eigene, aeussere Ebene
(docs/milestones/02-test-pyramide.md) und kommen in Stufe 2 bzw. 3 dazu.
"""

from datetime import UTC, datetime
from typing import Self, final

from src.contexts.identity.application.register_user.fakes import (
    DeterministicPasswordHasher,
    InMemoryUserStore,
)
from src.contexts.identity.application.register_user.pipeline import build_register_user_pipeline
from src.contexts.identity.application.register_user.request import RegisterUserRequest
from src.contexts.identity.application.register_user.response import RegisterUserResponse
from src.contexts.identity.domain import Email, UserId
from src.shared_kernel import FakeTimeProvider

__all__ = ["RegisterUserTestApi"]

_DEFAULT_NOW = datetime(2026, 8, 6, 9, 30, tzinfo=UTC)


@final
class RegisterUserTestApi:
    """Arrange ueber `with_…`, Act ueber `run`, Assert gegen die Response-Union."""

    def __init__(self) -> None:
        """Starte mit leerem Nutzerbestand und fester Zeit."""
        self._store = InMemoryUserStore()
        self._hasher = DeterministicPasswordHasher()
        self._clock = FakeTimeProvider(_DEFAULT_NOW)

    # --- Arrange ---

    def with_registered_user(self, email: str, user_id: str | None = None) -> Self:
        """Es gibt bereits ein Konto zu dieser E-Mail."""
        self._store.register(_normalized(email), user_id or str(UserId.generate()))
        return self

    def with_email_taken_between_check_and_write(
        self,
        email: str,
        user_id: str | None = None,
    ) -> Self:
        """Ein anderer Vorgang belegt die E-Mail erst waehrend dieser Registrierung."""
        self._store.arm_write_collision(_normalized(email), user_id or str(UserId.generate()))
        return self

    def at_time(self, moment: datetime) -> Self:
        """Die Registrierung geschieht zu diesem Zeitpunkt."""
        self._clock.set_time(moment)
        return self

    # --- Act ---

    async def run(self, request: RegisterUserRequest) -> RegisterUserResponse:
        """Fuehre das echte Request-DTO durch die echte Pipeline."""
        pipeline = build_register_user_pipeline(self._store, self._hasher, self._clock)
        return await pipeline.run(request)


def _normalized(email: str) -> str:
    """Normalisiere genau wie die Produktion - die Test-API baut das nicht nach."""
    return Email.hydrate(email).value
