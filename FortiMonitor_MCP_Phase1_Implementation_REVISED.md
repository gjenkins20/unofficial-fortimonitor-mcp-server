# FortiMonitor MCP Server - Phase 1 Implementation Guide (REVISED)

## Project Overview

This document provides detailed engineering instructions for implementing Phase 1 of the FortiMonitor MCP (Model Context Protocol) server with **accurate API endpoints and schema integration** based on the FortiMonitor/Panopta v2 API.

**Timeline**: Week 1-2  
**Deliverable**: Working MCP server with FortiMonitor API integration using actual endpoints  
**API Base**: `https://api2.panopta.com/v2`

---

## What Changed from Original Plan

### Key Corrections

1. **Endpoint Structure**: FortiMonitor uses specific endpoints:
   - `/server` (not `/servers`) - List servers
   - `/server/{server_id}` - Server details
   - `/outage` - Alerts/outages (not `/alerts`)
   - `/server/{server_id}/agent_resource` - Metrics

2. **Response Format**: API returns structured responses with pagination:
   - `server_list` array (not `servers`)
   - Pagination metadata: `limit`, `offset`, `next`, `total_count`
   - Filter modes: `tag_filter_mode`, `attribute_filter_mode`

3. **Schema Discovery**: API provides runtime schema documentation at:
   - `/schema/resources` - Lists all available resources
   - `/schema/resources/{resource_name}` - Get schema for specific resource

4. **Parameter Requirements**: Many endpoints have specific required/optional parameters that differ from generic REST patterns

---

## Phase 1 Objectives

1. Set up MCP server project structure
2. Implement FortiMonitor API client with correct endpoints
3. **Add schema discovery and validation**
4. Create four core MCP tools:
   - `get_servers` - List all monitored servers
   - `get_server_details` - Get specific server information  
   - `get_outages` - Query outages (alerts)
   - `get_server_metrics` - Retrieve agent resource metrics
5. Implement authentication and configuration management
6. Add error handling and logging with schema awareness
7. Test integration with Claude

---

## Prerequisites

### Required Software
- Python 3.9 or higher
- pip (Python package manager)
- Git (version control)
- Text editor or IDE (VS Code recommended)
- Access to FortiMonitor/Panopta instance

### Required Access
- FortiMonitor API key
- FortiMonitor base URL (e.g., `https://api2.panopta.com/v2`)
- Network connectivity to FortiMonitor instance

---

## Project Structure

```
fortimonitor-mcp-server/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── server.py              # Main MCP server
│   ├── config.py              # Configuration management
│   ├── fortimonitor/
│   │   ├── __init__.py
│   │   ├── client.py          # FortiMonitor API client
│   │   ├── schema.py          # Schema discovery & validation
│   │   ├── models.py          # Data models
│   │   └── exceptions.py      # Custom exceptions
│   └── tools/
│       ├── __init__.py
│       ├── servers.py         # Server-related tools
│       ├── outages.py         # Outage-related tools (alerts)
│       └── metrics.py         # Metrics-related tools
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_schema.py
│   └── test_tools.py
├── cache/
│   └── schemas/               # Cached API schemas
└── docs/
    ├── API_REFERENCE.md
    └── DEPLOYMENT.md
```

---

## Step 1: Initial Project Setup

### 1.1 Create Project Directory

```bash
mkdir fortimonitor-mcp-server
cd fortimonitor-mcp-server
mkdir -p src/fortimonitor src/tools tests cache/schemas docs
git init
```

### 1.2 Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.3 Create requirements.txt

```txt
# MCP and Core Dependencies
mcp>=0.9.0

# HTTP and API
requests>=2.31.0
httpx>=0.25.0

# Configuration
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Utilities
python-dateutil>=2.8.2

# Logging
structlog>=23.2.0

# Development Dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.12.0
flake8>=6.1.0
mypy>=1.7.0

# Type stubs
types-requests>=2.31.0
```

### 1.4 Install Dependencies

```bash
pip install -r requirements.txt
```

### 1.5 Create .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
build/
dist/
*.egg-info/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
logs/

# Cache
cache/
*.cache
```

### 1.6 Create .env.example

```bash
# FortiMonitor Configuration
FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2
FORTIMONITOR_API_KEY=your_api_key_here

# MCP Server Configuration
MCP_SERVER_NAME=fortimonitor-mcp
MCP_SERVER_VERSION=0.1.0
LOG_LEVEL=INFO

# Optional: Caching
ENABLE_SCHEMA_CACHE=true
SCHEMA_CACHE_DIR=cache/schemas
SCHEMA_CACHE_TTL=86400

# Optional: Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

---

## Step 2: Configuration Management

### 2.1 Create src/config.py

```python
"""Configuration management for FortiMonitor MCP Server."""

from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    # FortiMonitor API Configuration
    fortimonitor_base_url: HttpUrl = Field(
        ...,
        description="Base URL for FortiMonitor API"
    )
    fortimonitor_api_key: str = Field(
        ...,
        description="API key for FortiMonitor authentication"
    )
    
    # MCP Server Configuration
    mcp_server_name: str = Field(
        default="fortimonitor-mcp",
        description="Name of the MCP server"
    )
    mcp_server_version: str = Field(
        default="0.1.0",
        description="Version of the MCP server"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Schema Caching
    enable_schema_cache: bool = Field(
        default=True,
        description="Enable schema caching"
    )
    schema_cache_dir: Path = Field(
        default=Path("cache/schemas"),
        description="Directory for cached schemas"
    )
    schema_cache_ttl: int = Field(
        default=86400,
        description="Schema cache TTL in seconds (default: 24 hours)"
    )
    
    # Optional: Rate Limiting
    rate_limit_requests: int = Field(
        default=100,
        description="Maximum requests per period"
    )
    rate_limit_period: int = Field(
        default=60,
        description="Rate limit period in seconds"
    )
    
    @property
    def api_base_url(self) -> str:
        """Get API base URL as string."""
        return str(self.fortimonitor_base_url).rstrip('/')


# Global settings instance
settings = Settings()
```

---

## Step 3: Data Models and Exceptions

### 3.1 Create src/fortimonitor/exceptions.py

```python
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
```

### 3.2 Create src/fortimonitor/models.py

```python
"""Data models for FortiMonitor API responses."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PaginatedResponse(BaseModel):
    """Base model for paginated API responses."""
    
    limit: int
    offset: int
    total_count: Optional[int] = None
    next: Optional[str] = None
    previous: Optional[str] = None


class Server(BaseModel):
    """FortiMonitor server model."""
    
    id: int
    name: str
    fqdn: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    server_key: Optional[str] = None
    partner_server_id: Optional[str] = None
    server_group: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class ServerListResponse(PaginatedResponse):
    """Response model for server list endpoint."""
    
    server_list: List[Server]


class Outage(BaseModel):
    """FortiMonitor outage (alert) model."""
    
    id: int
    server: Optional[str] = None  # URL reference
    server_name: Optional[str] = None
    severity: str
    status: str
    message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class OutageListResponse(PaginatedResponse):
    """Response model for outage list endpoint."""
    
    outage_list: List[Outage]


class AgentResource(BaseModel):
    """FortiMonitor agent resource (metric) model."""
    
    id: int
    name: str
    resource_type: Optional[str] = None
    label: Optional[str] = None
    unit: Optional[str] = None
    current_value: Optional[float] = None
    last_check: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


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
```

---

## Step 4: Schema Discovery System

### 4.1 Create src/fortimonitor/schema.py

```python
"""Schema discovery and validation for FortiMonitor API."""

import json
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime, timedelta
import requests

from .exceptions import SchemaError, APIError
from ..config import settings


logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages FortiMonitor API schema discovery and caching."""
    
    def __init__(self, api_key: str, base_url: str):
        """
        Initialize schema manager.
        
        Args:
            api_key: FortiMonitor API key
            base_url: API base URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.cache_dir = settings.schema_cache_dir
        self.cache_ttl = settings.schema_cache_ttl
        self.enable_cache = settings.enable_schema_cache
        
        # Create cache directory if it doesn't exist
        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._resource_list: Optional[List[str]] = None
        self._schemas: Dict[str, Dict[str, Any]] = {}
    
    def get_resource_list(self) -> List[str]:
        """
        Get list of available API resources.
        
        Returns:
            List of resource names
        """
        if self._resource_list is not None:
            return self._resource_list
        
        cache_file = self.cache_dir / "resource_list.json"
        
        # Check cache
        if self.enable_cache and self._is_cache_valid(cache_file):
            logger.debug("Loading resource list from cache")
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                self._resource_list = cached_data.get('resources', [])
                return self._resource_list
        
        # Fetch from API
        try:
            url = f"{self.base_url}/schema/resources"
            params = {"api_key": self.api_key}
            
            logger.info("Fetching resource list from API")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            resources = [api['path'].split('/')[-1] for api in data.get('apis', [])]
            self._resource_list = resources
            
            # Cache the result
            if self.enable_cache:
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'resources': resources
                }
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
            
            logger.info(f"Found {len(resources)} API resources")
            return resources
            
        except requests.exceptions.RequestException as e:
            raise SchemaError(f"Failed to fetch resource list: {e}")
    
    def get_resource_schema(self, resource_name: str) -> Dict[str, Any]:
        """
        Get schema for a specific resource.
        
        Args:
            resource_name: Name of the resource (e.g., 'server', 'outage')
            
        Returns:
            Schema dictionary
        """
        if resource_name in self._schemas:
            return self._schemas[resource_name]
        
        cache_file = self.cache_dir / f"{resource_name}_schema.json"
        
        # Check cache
        if self.enable_cache and self._is_cache_valid(cache_file):
            logger.debug(f"Loading {resource_name} schema from cache")
            with open(cache_file, 'r') as f:
                schema = json.load(f)
                self._schemas[resource_name] = schema
                return schema
        
        # Fetch from API
        try:
            url = f"{self.base_url}/schema/resources/{resource_name}"
            params = {"api_key": self.api_key}
            
            logger.info(f"Fetching {resource_name} schema from API")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            schema = response.json()
            self._schemas[resource_name] = schema
            
            # Cache the result
            if self.enable_cache:
                with open(cache_file, 'w') as f:
                    json.dump(schema, f, indent=2)
            
            logger.info(f"Loaded schema for {resource_name}")
            return schema
            
        except requests.exceptions.RequestException as e:
            raise SchemaError(f"Failed to fetch schema for {resource_name}: {e}")
    
    def get_operation_parameters(self, resource_name: str, path: str, method: str) -> List[Dict[str, Any]]:
        """
        Get parameters for a specific API operation.
        
        Args:
            resource_name: Resource name
            path: API path
            method: HTTP method
            
        Returns:
            List of parameter definitions
        """
        schema = self.get_resource_schema(resource_name)
        
        for api in schema.get('apis', []):
            if api.get('path') == path:
                for operation in api.get('operations', []):
                    if operation.get('method', '').upper() == method.upper():
                        return operation.get('parameters', [])
        
        return []
    
    def validate_parameters(
        self,
        resource_name: str,
        path: str,
        method: str,
        provided_params: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate provided parameters against schema.
        
        Args:
            resource_name: Resource name
            path: API path
            method: HTTP method
            provided_params: Parameters provided by user
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        params_def = self.get_operation_parameters(resource_name, path, method)
        errors = []
        
        # Check required parameters
        for param in params_def:
            if param.get('required', False):
                param_name = param.get('name')
                if param_name not in provided_params:
                    errors.append(f"Missing required parameter: {param_name}")
        
        return len(errors) == 0, errors
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file exists and is still valid."""
        if not cache_file.exists():
            return False
        
        # Check age
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return file_age < timedelta(seconds=self.cache_ttl)
```

---

## Step 5: FortiMonitor API Client

### 5.1 Create src/fortimonitor/client.py

```python
"""FortiMonitor API client implementation."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    Server, ServerListResponse,
    Outage, OutageListResponse,
    AgentResource
)
from .exceptions import (
    AuthenticationError,
    APIError,
    NotFoundError,
    RateLimitError,
    ValidationError
)
from .schema import SchemaManager
from ..config import settings


logger = logging.getLogger(__name__)


class FortiMonitorClient:
    """Client for interacting with FortiMonitor API."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize FortiMonitor API client.
        
        Args:
            base_url: Base URL for API (defaults to settings)
            api_key: API key for authentication (defaults to settings)
        """
        self.base_url = (base_url or settings.api_base_url).rstrip('/')
        self.api_key = api_key or settings.fortimonitor_api_key
        
        # Initialize schema manager
        self.schema = SchemaManager(self.api_key, self.base_url)
        
        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to FortiMonitor API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON request body
            
        Returns:
            API response as dictionary
            
        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If resource not found
            RateLimitError: If rate limit exceeded
            APIError: For other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add API key to params
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        try:
            logger.debug(f"API Request: {method} {url}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=30
            )
            
            # Handle specific status codes
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or unauthorized access")
            elif response.status_code == 404:
                raise NotFoundError(f"Resource not found: {endpoint}", status_code=404)
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded", status_code=429)
            elif response.status_code >= 400:
                error_msg = response.text or f"API error: {response.status_code}"
                raise APIError(error_msg, status_code=response.status_code)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise APIError(f"Request failed: {str(e)}")
    
    # Server Operations
    
    def get_servers(
        self,
        name: Optional[str] = None,
        fqdn: Optional[str] = None,
        server_group: Optional[int] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tag_filter_mode: str = "or",
        limit: int = 50,
        offset: int = 0,
        full: bool = False
    ) -> ServerListResponse:
        """
        Get list of monitored servers.
        
        Args:
            name: Filter by server name
            fqdn: Filter by FQDN
            server_group: Filter by server group ID
            status: Filter by status
            tags: Filter by tags (list)
            tag_filter_mode: Tag filter mode ('or' or 'and')
            limit: Maximum number of results (default: 50)
            offset: Offset for pagination
            full: Resolve all URLs to actual objects
            
        Returns:
            ServerListResponse with server_list and pagination info
        """
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "full": str(full).lower() if full else None,
            "tag_filter_mode": tag_filter_mode
        }
        
        if name:
            params["name"] = name
        if fqdn:
            params["fqdn"] = fqdn
        if server_group:
            params["server_group"] = server_group
        if status:
            params["status"] = status
        if tags:
            params["tags"] = ",".join(tags)
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = self._request("GET", "/server", params=params)
        
        # Parse response
        return ServerListResponse(**response)
    
    def get_server_details(self, server_id: int, full: bool = False) -> Server:
        """
        Get detailed information about a specific server.
        
        Args:
            server_id: ID of the server
            full: Resolve all URLs to actual objects
            
        Returns:
            Server object with full details
            
        Raises:
            NotFoundError: If server not found
        """
        params = {"full": str(full).lower()} if full else {}
        response = self._request("GET", f"/server/{server_id}", params=params)
        return Server(**response)
    
    # Outage Operations (Alerts)
    
    def get_outages(
        self,
        server_id: Optional[int] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
        full: bool = False
    ) -> OutageListResponse:
        """
        Get outages (alerts) based on filters.
        
        Args:
            server_id: Filter by server ID
            severity: Filter by severity
            status: Filter by status (active, resolved)
            start_time: Filter outages after this time
            end_time: Filter outages before this time
            limit: Maximum number of results (default: 50)
            offset: Offset for pagination
            full: Resolve all URLs to actual objects
            
        Returns:
            OutageListResponse with outage_list and pagination info
        """
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "full": str(full).lower() if full else None
        }
        
        if server_id:
            params["server"] = server_id
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status
        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%d %H:%M:%S")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = self._request("GET", "/outage", params=params)
        
        # Parse response
        return OutageListResponse(**response)
    
    def get_active_outages(
        self,
        server_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> OutageListResponse:
        """
        Get active outages only.
        
        Args:
            server_id: Filter by server ID
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            OutageListResponse with active outages
        """
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset
        }
        
        if server_id:
            params["server_id"] = server_id
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = self._request("GET", "/outage/active", params=params)
        return OutageListResponse(**response)
    
    # Agent Resource Operations (Metrics)
    
    def get_server_agent_resources(
        self,
        server_id: int,
        limit: int = 50,
        offset: int = 0,
        full: bool = False
    ) -> List[AgentResource]:
        """
        Get agent resources (metrics) for a server.
        
        Args:
            server_id: ID of the server
            limit: Maximum number of results
            offset: Offset for pagination
            full: Resolve all URLs to actual objects
            
        Returns:
            List of AgentResource objects
        """
        params = {
            "limit": limit,
            "offset": offset,
            "full": str(full).lower() if full else None
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = self._request("GET", f"/server/{server_id}/agent_resource", params=params)
        
        # Parse agent_resource_list
        resources = []
        for resource_data in response.get("agent_resource_list", []):
            try:
                resources.append(AgentResource(**resource_data))
            except Exception as e:
                logger.warning(f"Failed to parse agent resource data: {e}")
        
        return resources
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
```

---

## Step 6: MCP Tools Implementation

### 6.1 Create src/tools/servers.py

```python
"""MCP tools for server operations."""

from typing import Optional
import logging

from mcp.types import Tool, TextContent
from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import FortiMonitorError

logger = logging.getLogger(__name__)


def get_servers_tool_definition() -> Tool:
    """Define the get_servers MCP tool."""
    return Tool(
        name="get_servers",
        description=(
            "List all monitored servers in FortiMonitor. "
            "Supports filtering by name, FQDN, server group, status, and tags."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Filter by server name (partial match)"
                },
                "fqdn": {
                    "type": "string",
                    "description": "Filter by FQDN"
                },
                "server_group": {
                    "type": "integer",
                    "description": "Filter by server group ID"
                },
                "status": {
                    "type": "string",
                    "description": "Filter by server status"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Maximum number of servers to return"
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                    "minimum": 0,
                    "description": "Offset for pagination"
                }
            }
        }
    )


async def handle_get_servers(arguments: dict, client: FortiMonitorClient) -> list[TextContent]:
    """Handle get_servers tool execution."""
    try:
        name = arguments.get("name")
        fqdn = arguments.get("fqdn")
        server_group = arguments.get("server_group")
        status = arguments.get("status")
        tags = arguments.get("tags")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)
        
        logger.info(f"Getting servers: name={name}, status={status}, limit={limit}")
        
        response = client.get_servers(
            name=name,
            fqdn=fqdn,
            server_group=server_group,
            status=status,
            tags=tags,
            limit=limit,
            offset=offset
        )
        
        if not response.server_list:
            return [TextContent(
                type="text",
                text="No servers found matching the specified criteria."
            )]
        
        # Format server list
        server_list = []
        for server in response.server_list:
            server_info = (
                f"**Server ID: {server.id}**\n"
                f"Name: {server.name}\n"
                f"FQDN: {server.fqdn or 'N/A'}\n"
                f"Status: {server.status or 'N/A'}\n"
                f"Tags: {', '.join(server.tags) if server.tags else 'None'}\n"
            )
            server_list.append(server_info)
        
        # Add pagination info
        result_text = (
            f"Found {response.total_count or len(response.server_list)} total server(s) "
            f"(showing {len(response.server_list)} starting at offset {response.offset}):\n\n"
        )
        result_text += "\n---\n".join(server_list)
        
        if response.next:
            result_text += f"\n\n*More results available (use offset={response.offset + response.limit})*"
        
        return [TextContent(type="text", text=result_text)]
        
    except FortiMonitorError as e:
        logger.error(f"FortiMonitor API error: {e}")
        return [TextContent(
            type="text",
            text=f"Error retrieving servers: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error in get_servers")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]


def get_server_details_tool_definition() -> Tool:
    """Define the get_server_details MCP tool."""
    return Tool(
        name="get_server_details",
        description="Get detailed information about a specific server by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server to retrieve"
                },
                "full": {
                    "type": "boolean",
                    "default": False,
                    "description": "Resolve all URLs to actual objects"
                }
            },
            "required": ["server_id"]
        }
    )


async def handle_get_server_details(arguments: dict, client: FortiMonitorClient) -> list[TextContent]:
    """Handle get_server_details tool execution."""
    try:
        server_id = arguments["server_id"]
        full = arguments.get("full", False)
        
        logger.info(f"Getting details for server {server_id}")
        
        server = client.get_server_details(server_id, full=full)
        
        # Format detailed server information
        details = (
            f"**Server Details for ID {server.id}**\n\n"
            f"Name: {server.name}\n"
            f"FQDN: {server.fqdn or 'N/A'}\n"
            f"Description: {server.description or 'N/A'}\n"
            f"Status: {server.status or 'N/A'}\n"
            f"Server Key: {server.server_key or 'N/A'}\n"
            f"Partner Server ID: {server.partner_server_id or 'N/A'}\n"
            f"Tags: {', '.join(server.tags) if server.tags else 'None'}\n"
            f"Created: {server.created or 'N/A'}\n"
            f"Updated: {server.updated or 'N/A'}\n"
        )
        
        if server.attributes:
            details += "\n**Attributes:**\n"
            for key, value in server.attributes.items():
                details += f"  - {key}: {value}\n"
        
        return [TextContent(type="text", text=details)]
        
    except FortiMonitorError as e:
        logger.error(f"FortiMonitor API error: {e}")
        return [TextContent(
            type="text",
            text=f"Error retrieving server details: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error in get_server_details")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]
```

### 6.2 Create src/tools/outages.py

```python
"""MCP tools for outage (alert) operations."""

from typing import Optional
from datetime import datetime, timedelta
import logging

from mcp.types import Tool, TextContent
from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import FortiMonitorError

logger = logging.getLogger(__name__)


def get_outages_tool_definition() -> Tool:
    """Define the get_outages MCP tool."""
    return Tool(
        name="get_outages",
        description=(
            "Query FortiMonitor outages (alerts) with various filters. "
            "Returns active and recent outages for monitored servers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "Filter by specific server ID"
                },
                "severity": {
                    "type": "string",
                    "description": "Filter by outage severity"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "resolved"],
                    "description": "Filter by outage status"
                },
                "hours_back": {
                    "type": "integer",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168,
                    "description": "How many hours back to search (default: 24)"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum number of outages to return"
                },
                "active_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only return active outages"
                }
            }
        }
    )


async def handle_get_outages(arguments: dict, client: FortiMonitorClient) -> list[TextContent]:
    """Handle get_outages tool execution."""
    try:
        server_id = arguments.get("server_id")
        severity = arguments.get("severity")
        status = arguments.get("status")
        hours_back = arguments.get("hours_back", 24)
        limit = arguments.get("limit", 50)
        active_only = arguments.get("active_only", False)
        
        logger.info(
            f"Getting outages: server_id={server_id}, severity={severity}, "
            f"status={status}, hours_back={hours_back}, active_only={active_only}"
        )
        
        # Use active outages endpoint if requested
        if active_only:
            response = client.get_active_outages(
                server_id=server_id,
                limit=limit
            )
        else:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            response = client.get_outages(
                server_id=server_id,
                severity=severity,
                status=status,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
        
        if not response.outage_list:
            time_desc = "active" if active_only else f"in the last {hours_back} hours"
            return [TextContent(
                type="text",
                text=f"No outages found {time_desc} matching the specified criteria."
            )]
        
        # Group outages by severity
        outages_by_severity = {"critical": [], "warning": [], "info": [], "other": []}
        for outage in response.outage_list:
            severity_key = outage.severity.lower()
            if severity_key not in outages_by_severity:
                severity_key = "other"
            outages_by_severity[severity_key].append(outage)
        
        # Format outage list
        time_desc = "active" if active_only else f"in the last {hours_back} hours"
        result_parts = [
            f"Found {response.total_count or len(response.outage_list)} total outage(s) {time_desc} "
            f"(showing {len(response.outage_list)}):\n"
        ]
        
        for sev in ["critical", "warning", "info", "other"]:
            sev_outages = outages_by_severity[sev]
            if sev_outages:
                result_parts.append(f"\n**{sev.upper()} ({len(sev_outages)})**:")
                for outage in sev_outages:
                    ack_status = "✓ Acknowledged" if outage.acknowledged else "⚠ Not Acknowledged"
                    duration = f"{outage.duration // 60}m" if outage.duration else "ongoing"
                    outage_info = (
                        f"\n  Outage ID: {outage.id}\n"
                        f"  Server: {outage.server_name or 'N/A'}\n"
                        f"  Status: {outage.status} | {ack_status}\n"
                        f"  Duration: {duration}\n"
                        f"  Start: {outage.start_time}\n"
                    )
                    if outage.message:
                        outage_info += f"  Message: {outage.message}\n"
                    result_parts.append(outage_info)
        
        return [TextContent(type="text", text="".join(result_parts))]
        
    except FortiMonitorError as e:
        logger.error(f"FortiMonitor API error: {e}")
        return [TextContent(
            type="text",
            text=f"Error retrieving outages: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error in get_outages")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]
```

### 6.3 Create src/tools/metrics.py

```python
"""MCP tools for metrics operations."""

from typing import Optional
import logging

from mcp.types import Tool, TextContent
from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import FortiMonitorError

logger = logging.getLogger(__name__)


def get_server_metrics_tool_definition() -> Tool:
    """Define the get_server_metrics MCP tool."""
    return Tool(
        name="get_server_metrics",
        description=(
            "Retrieve agent resource metrics for a specific server. "
            "Shows available monitoring resources (CPU, memory, disk, etc.)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server to retrieve metrics for"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum number of resources to return"
                },
                "full": {
                    "type": "boolean",
                    "default": False,
                    "description": "Resolve all URLs to actual objects"
                }
            },
            "required": ["server_id"]
        }
    )


async def handle_get_server_metrics(arguments: dict, client: FortiMonitorClient) -> list[TextContent]:
    """Handle get_server_metrics tool execution."""
    try:
        server_id = arguments["server_id"]
        limit = arguments.get("limit", 50)
        full = arguments.get("full", False)
        
        logger.info(f"Getting metrics for server {server_id}")
        
        resources = client.get_server_agent_resources(
            server_id=server_id,
            limit=limit,
            full=full
        )
        
        if not resources:
            return [TextContent(
                type="text",
                text=f"No agent resources (metrics) found for server {server_id}."
            )]
        
        # Group resources by type
        resources_by_type: dict = {}
        for resource in resources:
            res_type = resource.resource_type or "unknown"
            if res_type not in resources_by_type:
                resources_by_type[res_type] = []
            resources_by_type[res_type].append(resource)
        
        # Format results
        result_parts = [
            f"**Agent Resources for Server {server_id}**\n\n"
            f"Found {len(resources)} resource(s):\n"
        ]
        
        for res_type, type_resources in resources_by_type.items():
            result_parts.append(f"\n**{res_type.upper()} Resources ({len(type_resources)})**:")
            for resource in type_resources:
                current_val = f"{resource.current_value} {resource.unit}" if resource.current_value is not None else "N/A"
                resource_info = (
                    f"\n  ID: {resource.id}\n"
                    f"  Name: {resource.name}\n"
                    f"  Label: {resource.label or 'N/A'}\n"
                    f"  Current Value: {current_val}\n"
                    f"  Last Check: {resource.last_check or 'N/A'}\n"
                )
                result_parts.append(resource_info)
        
        return [TextContent(type="text", text="".join(result_parts))]
        
    except FortiMonitorError as e:
        logger.error(f"FortiMonitor API error: {e}")
        return [TextContent(
            type="text",
            text=f"Error retrieving metrics: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error in get_server_metrics")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]
```

---

## Step 7: Main MCP Server

### 7.1 Create src/server.py

```python
"""Main MCP server implementation for FortiMonitor."""

import logging
import asyncio
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import settings
from .fortimonitor.client import FortiMonitorClient
from .tools.servers import (
    get_servers_tool_definition,
    handle_get_servers,
    get_server_details_tool_definition,
    handle_get_server_details
)
from .tools.outages import (
    get_outages_tool_definition,
    handle_get_outages
)
from .tools.metrics import (
    get_server_metrics_tool_definition,
    handle_get_server_metrics
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FortiMonitorMCPServer:
    """MCP Server for FortiMonitor integration."""
    
    def __init__(self):
        """Initialize the FortiMonitor MCP server."""
        self.server = Server(settings.mcp_server_name)
        self.client: FortiMonitorClient = None
        self._setup_handlers()
        
        logger.info(f"Initialized {settings.mcp_server_name} v{settings.mcp_server_version}")
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                get_servers_tool_definition(),
                get_server_details_tool_definition(),
                get_outages_tool_definition(),
                get_server_metrics_tool_definition()
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool execution requests."""
            logger.info(f"Tool called: {name}")
            
            # Ensure client is initialized
            if not self.client:
                self.client = FortiMonitorClient()
            
            # Route to appropriate handler
            if name == "get_servers":
                return await handle_get_servers(arguments, self.client)
            elif name == "get_server_details":
                return await handle_get_server_details(arguments, self.client)
            elif name == "get_outages":
                return await handle_get_outages(arguments, self.client)
            elif name == "get_server_metrics":
                return await handle_get_server_metrics(arguments, self.client)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting FortiMonitor MCP server...")
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                init_options = InitializationOptions(
                    server_name=settings.mcp_server_name,
                    server_version=settings.mcp_server_version,
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
                
                await self.server.run(
                    read_stream,
                    write_stream,
                    init_options
                )
        except Exception as e:
            logger.exception("Server error")
            raise
        finally:
            if self.client:
                self.client.close()
            logger.info("FortiMonitor MCP server stopped")


def main():
    """Main entry point."""
    server = FortiMonitorMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
```

---

## Step 8: Testing and Validation

### 8.1 Create API Connectivity Test

Create a test script `test_connectivity.py`:

```python
"""Test FortiMonitor API connectivity."""

from src.fortimonitor.client import FortiMonitorClient

def main():
    print("Testing FortiMonitor API connectivity...")
    
    try:
        # Initialize client
        client = FortiMonitorClient()
        print("✓ Client initialized")
        
        # Test server list
        response = client.get_servers(limit=5)
        print(f"✓ Server list endpoint works! Found {len(response.server_list)} servers")
        print(f"  Total count: {response.total_count}")
        print(f"  Pagination: limit={response.limit}, offset={response.offset}")
        
        if response.server_list:
            server = response.server_list[0]
            print(f"\n✓ First server: {server.name} (ID: {server.id})")
            
            # Test server details
            details = client.get_server_details(server.id)
            print(f"✓ Server details endpoint works for server {details.name}")
        
        # Test active outages
        outages = client.get_active_outages(limit=5)
        print(f"\n✓ Active outages endpoint works! Found {len(outages.outage_list)} active outages")
        
        # Test schema discovery
        resources = client.schema.get_resource_list()
        print(f"\n✓ Schema discovery works! Found {len(resources)} resources")
        print(f"  Sample resources: {', '.join(resources[:5])}")
        
        print("\n✅ All connectivity tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
```

Run the test:
```bash
python test_connectivity.py
```

### 8.2 Create Unit Tests

Create `tests/test_client.py`:

```python
"""Tests for FortiMonitor API client."""

import pytest
from src.fortimonitor.client import FortiMonitorClient


def test_client_initialization():
    """Test client can be initialized."""
    client = FortiMonitorClient()
    assert client is not None
    assert client.base_url is not None
    assert client.api_key is not None
    assert client.schema is not None


def test_get_servers_returns_response():
    """Test getting server list returns structured response."""
    client = FortiMonitorClient()
    response = client.get_servers(limit=1)
    
    assert hasattr(response, 'server_list')
    assert hasattr(response, 'limit')
    assert hasattr(response, 'offset')
    assert isinstance(response.server_list, list)


# Add more tests as needed
```

---

## Step 9: Documentation

### 9.1 Update README.md

```markdown
# FortiMonitor MCP Server

Model Context Protocol (MCP) server for FortiMonitor/Panopta v2 API integration with Claude AI.

## Features

- **Server Management**: List and retrieve details for monitored servers
- **Outage Monitoring**: Query active and resolved outages (alerts)
- **Metrics Access**: Retrieve agent resource metrics for servers
- **Schema Discovery**: Runtime API schema validation and caching
- **Real-time Integration**: Direct API access during Claude conversations

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your FortiMonitor API key
   ```

3. **Test connectivity**:
   ```bash
   python test_connectivity.py
   ```

4. **Run the server**:
   ```bash
   python -m src.server
   ```

## Configuration

Edit `.env`:
```bash
FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2
FORTIMONITOR_API_KEY=your_api_key_here
```

## Available Tools

### 1. get_servers
List monitored servers with filtering support.

**Example**: "Show me all servers in production"

### 2. get_server_details
Get detailed information about a specific server.

**Example**: "Get details for server 12345"

### 3. get_outages
Query outages (alerts) with various filters.

**Example**: "Show me critical outages from the last 6 hours"

### 4. get_server_metrics
Retrieve agent resource metrics for a server.

**Example**: "Show metrics for server 12345"

## Integration with Claude

Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/fortimonitor-mcp-server",
      "env": {
        "FORTIMONITOR_BASE_URL": "https://api2.panopta.com/v2",
        "FORTIMONITOR_API_KEY": "your_key"
      }
    }
  }
}
```

## API Documentation

The server automatically discovers and caches FortiMonitor API schemas for validation and documentation. Schemas are cached in `cache/schemas/` by default.

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black src/ tests/
```

## License

[Your License]
```

---

## Step 10: Deployment Checklist

### Phase 1 Completion Checklist

- [ ] Create project directory structure
- [ ] Initialize Git repository
- [ ] Create virtual environment
- [ ] Install dependencies from requirements.txt
- [ ] Create `.env` file with FortiMonitor credentials
- [ ] Implement configuration management (config.py)
- [ ] Implement exceptions (exceptions.py)
- [ ] Implement data models (models.py)
- [ ] Implement schema discovery system (schema.py)
- [ ] Implement FortiMonitor API client (client.py)
- [ ] Implement MCP tools (servers.py, outages.py, metrics.py)
- [ ] Implement main MCP server (server.py)
- [ ] Create connectivity test script
- [ ] Test API connectivity successfully
- [ ] Test each tool individually
- [ ] Configure MCP server in Claude Desktop
- [ ] Test tools through Claude interface
- [ ] Verify schema caching works
- [ ] Complete README documentation

---

## Validation Steps

### 1. Environment Setup Test
```bash
# Verify Python version
python --version  # Should be 3.9+

# Verify virtual environment
which python  # Should point to venv

# Verify dependencies
pip list | grep -E "mcp|pydantic|requests"
```

### 2. API Connectivity Test
```bash
python test_connectivity.py
```

Expected output:
```
Testing FortiMonitor API connectivity...
✓ Client initialized
✓ Server list endpoint works! Found 5 servers
  Total count: 76
  Pagination: limit=5, offset=0

✓ First server: production-web-01 (ID: 12345)
✓ Server details endpoint works for server production-web-01

✓ Active outages endpoint works! Found 3 active outages

✓ Schema discovery works! Found 33 resources
  Sample resources: server, outage, server_group, user, contact

✅ All connectivity tests passed!
```

### 3. Run MCP Server
```bash
python -m src.server
```

Server should start without errors.

### 4. Test in Claude

Try these queries:
- "List all monitored servers"
- "Show me details for server 12345"
- "What active outages do we have?"
- "Show metrics for server 12345"

---

## Troubleshooting

### Authentication Errors
- Verify API key in `.env`
- Check base URL is correct (`https://api2.panopta.com/v2`)
- Test API key with curl:
  ```bash
  curl "https://api2.panopta.com/v2/server?api_key=YOUR_KEY&limit=1"
  ```

### Schema Discovery Failures
- Check network connectivity
- Verify `cache/schemas/` directory exists and is writable
- Check schema cache TTL setting
- Clear cache and retry: `rm -rf cache/schemas/*`

### Response Parsing Errors
- Check API response format hasn't changed
- Review data models in `models.py`
- Enable DEBUG logging to see raw responses

### MCP Server Not Appearing in Claude
- Check Claude Desktop config syntax
- Verify file paths are absolute
- Restart Claude Desktop completely
- Check server logs for startup errors

---

## Next Steps (Phase 2)

After Phase 1 is validated:
1. Add outage acknowledgment capability
2. Implement server group management
3. Add bulk operations support
4. Implement template management
5. Add advanced filtering and search

---

**Document Version**: 2.0 (REVISED)  
**Last Updated**: January 2026  
**Phase**: 1 - Foundation with Schema Integration  
**API Version**: FortiMonitor/Panopta v2
