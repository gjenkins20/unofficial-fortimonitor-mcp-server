"""FortiMonitor API client and related modules."""

from .client import FortiMonitorClient
from .exceptions import (
    FortiMonitorError,
    AuthenticationError,
    APIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    SchemaError,
)

__all__ = [
    "FortiMonitorClient",
    "FortiMonitorError",
    "AuthenticationError",
    "APIError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "SchemaError",
]
