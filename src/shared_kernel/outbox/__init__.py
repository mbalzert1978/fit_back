"""Outbox pattern implementation: publisher and relay worker.

Fire-and-forget event relay between bounded contexts, using Postgres-backed
outbox with SELECT...FOR UPDATE SKIP LOCKED and LISTEN/NOTIFY for low-latency
delivery.
"""

__all__ = ["publish_outbox_event", "relay_outbox_events"]

from src.shared_kernel.outbox.publisher import publish_outbox_event
from src.shared_kernel.outbox.relay import relay_outbox_events
