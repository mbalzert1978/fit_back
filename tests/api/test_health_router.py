"""Test des Health-Endpunkts ohne Datenbank.

Der Weg mit erreichbarer Datenbank steht in `tests/api/test_app_startup.py` -
dort laeuft er gegen die echte Engine. Hier bleibt der Fall, den es dort nicht
gibt: die Engine ist noch gar nicht da, weil der Startup nicht durchgelaufen
ist. Genau dafuer existiert der Endpunkt.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.health_router import health_router

pytestmark = pytest.mark.asyncio


async def test_ohne_engine_meldet_der_health_check_503() -> None:
    app = FastAPI()
    app.include_router(health_router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy"}
