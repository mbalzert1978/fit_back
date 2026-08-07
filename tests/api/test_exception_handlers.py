"""Tests des Validierungs-Handlers am HTTP-Rand.

Fruehere Tests dieser Datei prueften einen `DomainException`-Handler. Der ist
entfallen: fachliche Fehlausgaenge tragen die Slices in ihrer Response-Union,
und der Router waehlt daraus Statuscode und Body - ein Exception-basierter
zweiter Fehlerkanal daneben hatte keinen einzigen Werfer und haette die
Verzweigung nur unsichtbar gemacht.

Was bleibt, ist der Fall, den FastAPI selbst wirft: ein Body, der nicht die
erwartete Gestalt hat.

Angesprochen wird die App wie in jeder anderen Testdatei hier ueber
`httpx.ASGITransport`, nicht ueber `fastapi.testclient.TestClient`: der
TestClient ist ein Synchron-Wrapper, der die App ueber einen eigenen Event-Loop
faehrt, und Starlette hat ihn inzwischen an `httpx2` gebunden. Der direkte
ASGI-Transport braucht diesen Umweg nicht.
"""

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, field_validator

from src.api.exception_handlers import register_exception_handlers
from src.api.i18n import create_resources


class TestValidationErrorHandler:
    """RequestValidationError wird zu RFC-7807 mit Status 400."""

    @pytest.mark.asyncio
    async def test_ungueltiger_body_wird_zu_problem_json(self) -> None:
        """400 statt FastAPIs 422 - der Aufrufer sieht ueberall dasselbe Format."""
        app = FastAPI()
        app.state.resources = create_resources()
        register_exception_handlers(app)

        class RegisterRequest(BaseModel):
            email: str
            password: str

            @field_validator("password")
            @classmethod
            def password_min_length(cls, v: str) -> str:
                if len(v) < 10:
                    raise ValueError("Must be at least 10 characters")
                return v

        @app.post("/api/v1/register")
        async def register(data: RegisterRequest) -> dict:
            return {"success": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/register",
                json={"email": "test", "password": "short"},
            )

        assert response.status_code == 400
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        assert data["type"] == "https://api.example/errors/validation-failed"
        assert data["status"] == 400
        assert data["instance"] == "/api/v1/register"
        assert data["errors"]

    def test_der_handler_ist_registriert(self) -> None:
        """`register_exception_handlers` haengt den Handler tatsaechlich an die App."""
        app = FastAPI()
        register_exception_handlers(app)

        assert RequestValidationError in app.exception_handlers
