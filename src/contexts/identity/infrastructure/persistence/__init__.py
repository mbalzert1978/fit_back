"""Persistenz des Identity-Context - erfuellt die Nahten der Slices ueber Postgres."""

from src.contexts.identity.infrastructure.persistence.user_store import PostgresUserStore

__all__ = ["PostgresUserStore"]
