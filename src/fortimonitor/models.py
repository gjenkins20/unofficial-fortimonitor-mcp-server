"""Data models for FortiMonitor API responses."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from email.utils import parsedate_to_datetime


class AttributePair(BaseModel):
    """Single attribute name-value pair."""

    name: str
    value: str


class PaginationMeta(BaseModel):
    """Pagination metadata from API responses."""

    limit: int
    offset: int
    next: Optional[str] = None
    previous: Optional[str] = None
    total_count: Optional[int] = None


class Server(BaseModel):
    """FortiMonitor server model."""

    # The API uses a URL field, not a simple 'id'
    url: str = Field(alias="url")
    name: str
    fqdn: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    server_key: Optional[str] = None
    partner_server_id: Optional[str] = None
    server_group: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Attributes comes as a list of {name, value} objects
    attributes: List[AttributePair] = Field(default_factory=list)

    # Date fields use RFC 2822 format
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        populate_by_name = True

    @field_validator("created", "updated", mode="before")
    @classmethod
    def parse_rfc2822_datetime(cls, v):
        """Parse RFC 2822 datetime format."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                # Parse RFC 2822 format: "Thu, 12 Dec 2024 01:33:48 -0000"
                return parsedate_to_datetime(v)
            except Exception:
                # If parsing fails, return None
                return None
        return v

    @property
    def id(self) -> Optional[int]:
        """Extract server ID from URL."""
        if self.url:
            # URL format: https://api2.panopta.com/v2/server/{id}
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None

    def get_attributes_dict(self) -> Dict[str, str]:
        """Convert attributes list to dictionary."""
        return {attr.name: attr.value for attr in self.attributes}


class ServerListResponse(BaseModel):
    """Response model for server list endpoint."""

    server_list: List[Server]
    meta: PaginationMeta

    @property
    def limit(self) -> int:
        """Get limit from meta."""
        return self.meta.limit

    @property
    def offset(self) -> int:
        """Get offset from meta."""
        return self.meta.offset

    @property
    def total_count(self) -> Optional[int]:
        """Get total count from meta."""
        return self.meta.total_count

    @property
    def next(self) -> Optional[str]:
        """Get next URL from meta."""
        return self.meta.next


class Outage(BaseModel):
    """FortiMonitor outage (alert) model."""

    url: str = Field(alias="url")
    server: Optional[str] = None  # URL reference to server
    server_name: Optional[str] = None
    severity: str
    status: str
    message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    acknowledged: Optional[bool] = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        populate_by_name = True

    @field_validator("start_time", "end_time", "acknowledged_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime in various formats."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                # Try RFC 2822 first
                return parsedate_to_datetime(v)
            except Exception:
                try:
                    # Try ISO format
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
                except Exception:
                    return None
        return v

    @property
    def id(self) -> Optional[int]:
        """Extract outage ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None


class OutageListResponse(BaseModel):
    """Response model for outage list endpoint."""

    outage_list: List[Outage]
    meta: PaginationMeta

    @property
    def limit(self) -> int:
        """Get limit from meta."""
        return self.meta.limit

    @property
    def offset(self) -> int:
        """Get offset from meta."""
        return self.meta.offset

    @property
    def total_count(self) -> Optional[int]:
        """Get total count from meta."""
        return self.meta.total_count

    @property
    def next(self) -> Optional[str]:
        """Get next URL from meta."""
        return self.meta.next


class AgentResource(BaseModel):
    """FortiMonitor agent resource (metric) model."""

    url: str = Field(alias="url")
    name: str
    # API returns "agent_resource_type", map it to resource_type
    resource_type: Optional[str] = Field(default=None, alias="agent_resource_type")
    label: Optional[str] = None
    unit: Optional[str] = None
    current_value: Optional[float] = None
    last_check: Optional[datetime] = None
    # Additional fields the API may return
    status: Optional[str] = None
    value: Optional[float] = None  # Alternative to current_value

    class Config:
        populate_by_name = True

    @field_validator("last_check", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime in various formats."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return parsedate_to_datetime(v)
            except Exception:
                try:
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
                except Exception:
                    return None
        return v

    @property
    def id(self) -> Optional[int]:
        """Extract resource ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None


class AgentResourceListResponse(BaseModel):
    """Response model for agent resource list endpoint."""

    agent_resource_list: List[AgentResource]
    meta: PaginationMeta

    @property
    def limit(self) -> int:
        """Get limit from meta."""
        return self.meta.limit

    @property
    def offset(self) -> int:
        """Get offset from meta."""
        return self.meta.offset

    @property
    def total_count(self) -> Optional[int]:
        """Get total count from meta."""
        return self.meta.total_count


class MetricDataPoint(BaseModel):
    """Single metric data point."""

    timestamp: datetime
    value: float

    class Config:
        populate_by_name = True


class SchemaResource(BaseModel):
    """Schema resource definition."""

    description: str
    path: str


class SchemaResourceList(BaseModel):
    """List of available schema resources."""

    apiVersion: str
    apis: List[SchemaResource]
