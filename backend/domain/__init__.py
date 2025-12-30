"""
Domain Layer.

Contains business logic, domain models, and custom exceptions.
"""

from .exceptions import (
    ChampionCloneError,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
)

__all__ = [
    "ChampionCloneError",
    "NotFoundError",
    "AlreadyExistsError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ExternalServiceError",
]
