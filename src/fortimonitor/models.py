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

    @field_validator("acknowledged", mode="before")
    @classmethod
    def parse_acknowledged(cls, v):
        """Parse acknowledged field - can be bool, dict, or None."""
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, dict):
            # If it's a dict (user info), that means it's acknowledged
            return True
        # Try to convert to bool
        return bool(v)

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


# ============================================================================
# PHASE 2 - PRIORITY 1 MODELS
# ============================================================================


class OutageNote(BaseModel):
    """Model for outage notes/comments."""

    id: Optional[int] = None
    outage: Optional[str] = None  # URL to parent outage
    note: str
    created: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        populate_by_name = True

    @field_validator("created", mode="before")
    @classmethod
    def parse_rfc2822_datetime(cls, v):
        """Parse RFC 2822 datetime format."""
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


class OutageUpdate(BaseModel):
    """Model for outage update requests."""

    acknowledged: Optional[bool] = None
    status: Optional[str] = None
    end: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class MaintenanceWindow(BaseModel):
    """Model for maintenance windows."""

    id: Optional[int] = None
    url: Optional[str] = None
    name: str
    start_time: Optional[datetime] = Field(default=None, alias="start")
    end_time: Optional[datetime] = Field(default=None, alias="end")
    servers: List[str] = Field(default_factory=list)  # List of server URLs
    suppress_notifications: bool = Field(default=True, alias="suppress_notification")
    description: Optional[str] = None
    recurrence: Optional[str] = None  # e.g., "daily", "weekly", "monthly"
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    @field_validator("start_time", "end_time", "created", "updated", mode="before")
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
    def window_id(self) -> Optional[int]:
        """Extract maintenance window ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return self.id


class MaintenanceWindowListResponse(BaseModel):
    """Model for maintenance schedule list response.

    Note: FortiMonitor API uses 'maintenance_schedule_list' in the response.
    """

    maintenance_schedule_list: List[MaintenanceWindow] = Field(
        default_factory=list, alias="maintenance_schedule_list"
    )
    meta: PaginationMeta

    class Config:
        populate_by_name = True

    @property
    def maintenance_window_list(self) -> List[MaintenanceWindow]:
        """Alias for backward compatibility."""
        return self.maintenance_schedule_list

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


# ============================================================================
# PHASE 2 - PRIORITY 3 MODELS (Server Groups & Templates)
# ============================================================================


class ServerGroup(BaseModel):
    """Model for server groups."""

    url: Optional[str] = None
    name: str
    description: Optional[str] = None
    servers: List[str] = Field(default_factory=list)  # Server URLs
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        populate_by_name = True

    @field_validator("created", "updated", mode="before")
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
        """Extract server group ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None

    @property
    def server_count(self) -> int:
        """Get the number of servers in the group."""
        return len(self.servers)


class ServerGroupListResponse(BaseModel):
    """Model for server group list response."""

    server_group_list: List[ServerGroup] = Field(default_factory=list)
    meta: PaginationMeta

    class Config:
        populate_by_name = True

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


class ServerTemplate(BaseModel):
    """Model for server monitoring templates."""

    url: Optional[str] = None
    name: str
    description: Optional[str] = None
    agent_resource_types: List[str] = Field(default_factory=list)  # Resource type URLs
    network_services: List[str] = Field(default_factory=list)  # Network service URLs
    notification_group: Optional[str] = None  # Notification group URL
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        populate_by_name = True

    @field_validator("created", "updated", mode="before")
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
        """Extract template ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None


class ServerTemplateListResponse(BaseModel):
    """Model for server template list response."""

    server_template_list: List[ServerTemplate] = Field(default_factory=list)
    meta: PaginationMeta

    class Config:
        populate_by_name = True

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


# ============================================================================
# PHASE 2 - PRIORITY 4 MODELS (Notifications & Agent Resources)
# ============================================================================


class NotificationSchedule(BaseModel):
    """Model for notification schedules."""

    url: Optional[str] = None
    name: str
    timezone: Optional[str] = None
    schedule_type: Optional[str] = None  # e.g., "weekly", "daily"
    intervals: Optional[List[Dict[str, Any]]] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        populate_by_name = True

    @field_validator("created", "updated", mode="before")
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
        """Extract schedule ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None


class NotificationScheduleListResponse(BaseModel):
    """Model for notification schedule list response."""

    notification_schedule_list: List[NotificationSchedule] = Field(default_factory=list)
    meta: PaginationMeta

    class Config:
        populate_by_name = True

    @property
    def limit(self) -> int:
        return self.meta.limit

    @property
    def offset(self) -> int:
        return self.meta.offset

    @property
    def total_count(self) -> Optional[int]:
        return self.meta.total_count


class NotificationGroup(BaseModel):
    """Model for notification groups."""

    url: Optional[str] = None
    name: str
    contacts: List[str] = Field(default_factory=list)  # Contact URLs
    notification_schedule: Optional[str] = None  # Schedule URL
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        populate_by_name = True

    @field_validator("created", "updated", mode="before")
    @classmethod
    def parse_datetime(cls, v):
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
        """Extract group ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None

    @property
    def contact_count(self) -> int:
        return len(self.contacts)


class NotificationGroupListResponse(BaseModel):
    """Model for notification group list response."""

    notification_group_list: List[NotificationGroup] = Field(default_factory=list)
    meta: PaginationMeta

    class Config:
        populate_by_name = True

    @property
    def limit(self) -> int:
        return self.meta.limit

    @property
    def offset(self) -> int:
        return self.meta.offset

    @property
    def total_count(self) -> Optional[int]:
        return self.meta.total_count


class Contact(BaseModel):
    """Model for notification contacts."""

    url: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    sms: Optional[str] = None
    notification_methods: Optional[List[str]] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        populate_by_name = True

    @field_validator("created", "updated", mode="before")
    @classmethod
    def parse_datetime(cls, v):
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
        """Extract contact ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None


class ContactListResponse(BaseModel):
    """Model for contact list response."""

    contact_list: List[Contact] = Field(default_factory=list)
    meta: PaginationMeta

    class Config:
        populate_by_name = True

    @property
    def limit(self) -> int:
        return self.meta.limit

    @property
    def offset(self) -> int:
        return self.meta.offset

    @property
    def total_count(self) -> Optional[int]:
        return self.meta.total_count


class AgentResourceType(BaseModel):
    """Model for agent resource types (metric types)."""

    url: Optional[str] = None
    # API uses 'label' for the name field
    name: Optional[str] = Field(default=None, alias="label")
    category: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    monitoring_type: Optional[str] = None
    created: Optional[datetime] = None

    class Config:
        populate_by_name = True

    @field_validator("created", mode="before")
    @classmethod
    def parse_datetime(cls, v):
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
        """Extract type ID from URL."""
        if self.url:
            parts = self.url.rstrip("/").split("/")
            try:
                return int(parts[-1])
            except (ValueError, IndexError):
                return None
        return None


class AgentResourceTypeListResponse(BaseModel):
    """Model for agent resource type list response."""

    agent_resource_type_list: List[AgentResourceType] = Field(default_factory=list)
    meta: PaginationMeta

    class Config:
        populate_by_name = True

    @property
    def limit(self) -> int:
        return self.meta.limit

    @property
    def offset(self) -> int:
        return self.meta.offset

    @property
    def total_count(self) -> Optional[int]:
        return self.meta.total_count
