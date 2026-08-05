"""Tests for exception handlers."""

import json

import pytest
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator

from ..exception_handlers import register_exception_handlers
from ..exceptions import DomainException


class TestDomainException:
    """Tests for DomainException."""

    def test_domain_exception_creation(self) -> None:
        """Test creating a DomainException instance."""
        exc = DomainException(detail="Test error")
        assert exc.detail == "Test error"
        assert exc.error_type == "https://api.example/errors/domain-error"
        assert exc.http_status == 500
        assert exc.title == "Domain Error"

    def test_domain_exception_with_custom_values(self) -> None:
        """Test DomainException with custom error_type and http_status."""
        exc = DomainException(
            detail="Product not found",
            error_type="https://api.example/errors/product-not-found",
            http_status=status.HTTP_404_NOT_FOUND,
            title="Product Not Found",
        )
        assert exc.detail == "Product not found"
        assert exc.error_type == "https://api.example/errors/product-not-found"
        assert exc.http_status == 404
        assert exc.title == "Product Not Found"

    def test_domain_exception_instance_tracking(self) -> None:
        """Test that instance (request path) can be tracked."""
        exc = DomainException(
            detail="Error at endpoint",
            instance="/api/v1/products/123",
        )
        assert exc.instance == "/api/v1/products/123"


class TestExceptionHandlers:
    """Tests for FastAPI exception handlers."""

    def test_domain_exception_handler_in_endpoint(self) -> None:
        """Test domain exception handler in a FastAPI endpoint."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/api/v1/test-error")
        async def test_endpoint() -> None:
            raise DomainException(
                detail="Product with ID 123 not found",
                error_type="https://api.example/errors/product-not-found",
                http_status=status.HTTP_404_NOT_FOUND,
                title="Product Not Found",
            )

        client = TestClient(app)
        response = client.get("/api/v1/test-error")

        assert response.status_code == 404
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        assert data["type"] == "https://api.example/errors/product-not-found"
        assert data["title"] == "Product Not Found"
        assert data["status"] == 404
        assert data["detail"] == "Product with ID 123 not found"
        assert data["instance"] == "/api/v1/test-error"
        assert data.get("errors") is None

    def test_validation_error_handler_in_endpoint(self) -> None:
        """Test validation error handler for invalid request body."""
        app = FastAPI()
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

        client = TestClient(app)
        response = client.post(
            "/api/v1/register",
            json={"email": "test", "password": "short"},
        )

        assert response.status_code == 400
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        assert data["type"] == "https://api.example/errors/validation-failed"
        assert data["status"] == 400
        assert data["instance"] == "/api/v1/register"
        assert data.get("errors") is not None
        # Errors should contain validation issues
        assert len(data["errors"]) > 0

    def test_domain_exception_with_custom_instance(self) -> None:
        """Test domain exception with custom instance path."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/api/v1/products/{product_id}")
        async def get_product(product_id: str) -> None:
            raise DomainException(
                detail=f"Product {product_id} not found",
                instance=f"/api/v1/products/{product_id}",
                error_type="https://api.example/errors/product-not-found",
                http_status=status.HTTP_404_NOT_FOUND,
                title="Product Not Found",
            )

        client = TestClient(app)
        response = client.get("/api/v1/products/999")

        assert response.status_code == 404
        data = response.json()
        assert data["instance"] == "/api/v1/products/999"

    def test_domain_exception_server_error(self) -> None:
        """Test domain exception for 5xx server errors."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/api/v1/server-error")
        async def server_error() -> None:
            raise DomainException(
                detail="Database connection failed",
                error_type="https://api.example/errors/database-error",
                http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
                title="Service Unavailable",
            )

        client = TestClient(app)
        response = client.get("/api/v1/server-error")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == 503
        assert data["title"] == "Service Unavailable"

    def test_exception_handlers_registered(self) -> None:
        """Test that exception handlers are registered with the app."""
        app = FastAPI()
        register_exception_handlers(app)
        # Check that handlers are in the app's exception handlers
        assert DomainException in app.exception_handlers
        assert RequestValidationError in app.exception_handlers
