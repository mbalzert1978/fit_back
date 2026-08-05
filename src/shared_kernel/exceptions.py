"""Domain exceptions for error handling."""


class DomainException(Exception):
    """Base exception for domain errors.

    Maps to HTTP 4xx/5xx ProblemDetails responses. Subclasses should define
    error_type, http_status, and title.
    """

    error_type: str = "https://api.example/errors/domain-error"
    http_status: int = 500
    title: str = "Domain Error"

    def __init__(
        self,
        detail: str,
        *,
        instance: str | None = None,
        error_type: str | None = None,
        http_status: int | None = None,
        title: str | None = None,
    ) -> None:
        """Initialize domain exception.

        Args:
            detail: Detailed error message for the client.
            instance: URI identifying the specific problem instance (e.g., request path).
            error_type: Overrides class-level error_type if provided.
            http_status: Overrides class-level http_status if provided.
            title: Overrides class-level title if provided.
        """
        self.detail = detail
        self.instance = instance
        self.error_type = error_type or self.__class__.error_type
        self.http_status = http_status or self.__class__.http_status
        self.title = title or self.__class__.title
        super().__init__(detail)
