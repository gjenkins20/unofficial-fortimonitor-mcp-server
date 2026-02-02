"""Custom exceptions for FortiMonitor API interactions."""

from typing import Optional


class FortiMonitorError(Exception):
    """Base exception for FortiMonitor API errors."""

    pass


class AuthenticationError(FortiMonitorError):
    """Raised when authentication fails."""

    pass


class APIError(FortiMonitorError):
    """Raised when API request fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class NotFoundError(APIError):
    """Raised when requested resource is not found."""

    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    pass


class ValidationError(FortiMonitorError):
    """Raised when request validation fails."""

    pass


class SchemaError(FortiMonitorError):
    """Raised when schema operations fail."""

    pass
