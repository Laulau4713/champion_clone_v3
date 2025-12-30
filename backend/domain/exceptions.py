"""
Domain Exceptions.

Custom exceptions for business logic errors.
These are caught by FastAPI exception handlers and converted to proper HTTP responses.
"""


class ChampionCloneError(Exception):
    """Base exception for the application."""
    pass


class NotFoundError(ChampionCloneError):
    """Resource not found."""
    def __init__(self, resource: str, identifier: str | int):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' not found")


class AlreadyExistsError(ChampionCloneError):
    """Resource already exists."""
    def __init__(self, resource: str, field: str, value: str):
        self.resource = resource
        self.field = field
        self.value = value
        super().__init__(f"{resource} with {field} '{value}' already exists")


class ValidationError(ChampionCloneError):
    """Business validation error."""
    pass


class AuthenticationError(ChampionCloneError):
    """Authentication failed."""
    pass


class AuthorizationError(ChampionCloneError):
    """Access denied."""
    pass


class ExternalServiceError(ChampionCloneError):
    """External service error (Claude API, Whisper, etc.)."""
    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(f"Service '{service}' error: {message}")
