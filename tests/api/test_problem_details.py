"""Tests for ProblemDetails model."""

import json

import pytest
from pydantic import ValidationError

from src.api.problem_details import ProblemDetails


class TestProblemDetails:
    """Tests for RFC 7807 ProblemDetails model."""

    def test_problem_details_basic_structure(self) -> None:
        problem = ProblemDetails(
            type="https://api.example/errors/not-found",
            title="Not Found",
            status=404,
            detail="Resource not found",
            instance="/api/v1/test",
        )
        assert problem.type == "https://api.example/errors/not-found"
        assert problem.title == "Not Found"
        assert problem.status == 404
        assert problem.detail == "Resource not found"
        assert problem.instance == "/api/v1/test"
        assert problem.errors is None

    def test_problem_details_with_validation_errors(self) -> None:
        problem = ProblemDetails(
            type="https://api.example/errors/validation-failed",
            title="Validation Failed",
            status=400,
            detail="Input validation failed",
            instance="/api/v1/register",
            errors={
                "password": ["Must be at least 10 characters"],
                "email": ["Invalid email format"],
            },
        )
        assert problem.status == 400
        assert problem.errors is not None
        assert len(problem.errors) == 2
        assert problem.errors["password"] == ["Must be at least 10 characters"]
        assert problem.errors["email"] == ["Invalid email format"]

    def test_problem_details_serialization(self) -> None:
        problem = ProblemDetails(
            type="https://api.example/errors/conflict",
            title="Conflict",
            status=409,
            detail="Concurrency conflict",
            instance="/api/v1/products/123",
        )
        json_str = problem.model_dump_json()
        data = json.loads(json_str)
        assert data["type"] == "https://api.example/errors/conflict"
        assert data["title"] == "Conflict"
        assert data["status"] == 409
        assert "errors" not in data or data["errors"] is None

    def test_problem_details_status_validation(self) -> None:
        with pytest.raises(ValidationError):
            ProblemDetails(
                type="https://api.example/errors/bad",
                title="Bad",
                status=200,  # Invalid: 200 is 2xx, not 4xx/5xx
                detail="Error",
                instance="/api/v1/test",
            )

    def test_problem_details_exclude_none_in_json(self) -> None:
        problem = ProblemDetails(
            type="https://api.example/errors/server-error",
            title="Server Error",
            status=500,
            detail="Internal server error",
            instance="/api/v1/test",
            errors=None,
        )
        dumped = problem.model_dump(exclude_none=True)
        assert "errors" not in dumped
