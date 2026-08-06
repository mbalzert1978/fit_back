"""Implementiert den Domain-Port `EventPublisher` ueber die public Naht."""

from typing import final

from src.contexts.identity.application.register_user.abstractions import RegisterUserEventLog
from src.contexts.shared_kernel.events import DomainEvent

__all__ = ["EventPublisherAdapter"]


@final
class EventPublisherAdapter:
    """Uebersetzt ein Domaenen-Ereignis in die Primitive der Naht.

    Die ganze Uebersetzung ist `to_payload()` - und genau deshalb liegt sie im
    Ereignis und nicht hier: welcher Ausschnitt eines Aggregats den Context
    verlassen darf, ist eine fachliche Entscheidung des Identity-Context, keine
    Verdrahtungsfrage.
    """

    def __init__(self, log: RegisterUserEventLog) -> None:
        """Nimm die Naht-Implementierung entgegen (Fake oder Outbox)."""
        self._log = log

    async def publish(self, event: DomainEvent) -> None:
        """Reiche das Ereignis als Primitive an die Naht weiter."""
        await self._log.record(
            event.EVENT_TYPE,
            event.to_payload(),
            event.occurred_at.unix_seconds,
        )
