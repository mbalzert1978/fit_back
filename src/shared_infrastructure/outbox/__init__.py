"""Outbox infrastructure: SQLAlchemy model for transactional event publishing.

Separate from shared_kernel to avoid external (SQLAlchemy) dependencies in the
domain/kernel layer.
"""

__all__ = ["OutboxEvent"]

from src.shared_infrastructure.outbox.model import OutboxEvent
