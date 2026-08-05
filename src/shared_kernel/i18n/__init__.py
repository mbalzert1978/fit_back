"""Internationalization (i18n) support for the API."""

from .middleware import AcceptLanguageMiddleware

__all__ = [
    "AcceptLanguageMiddleware",
]
