"""FortiMonitor API client implementation."""

import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    Server,
    ServerListResponse,
    Outage,
    OutageListResponse,
    AgentResource,
    AgentResourceListResponse,
    OutageNote,
    MaintenanceWindow,
    MaintenanceWindowListResponse,
)
from .exceptions import (
    AuthenticationError,
    APIError,
    NotFoundError,
    RateLimitError,
)
from .schema import SchemaManager

logger = logging.getLogger(__name__)


class FortiMonitorClient:
    """Client for interacting with FortiMonitor API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        enable_schema_cache: bool = True,
        schema_cache_dir: Optional[Path] = None,
        schema_cache_ttl: int = 86400,
    ):
        """
        Initialize FortiMonitor API client.

        Args:
            base_url: Base URL for API (defaults to settings)
            api_key: API key for authentication (defaults to settings)
            enable_schema_cache: Whether to enable schema caching
            schema_cache_dir: Directory for schema cache
            schema_cache_ttl: Schema cache TTL in seconds
        """
        # Import settings lazily to avoid circular imports
        from ..config import get_settings

        _settings = get_settings()

        self.base_url = (base_url or _settings.api_base_url).rstrip("/")
        self.api_key = api_key or _settings.fortimonitor_api_key

        # Initialize schema manager
        self.schema = SchemaManager(
            api_key=self.api_key,
            base_url=self.base_url,
            cache_dir=schema_cache_dir or _settings.schema_cache_dir,
            cache_ttl=schema_cache_ttl,
            enable_cache=enable_schema_cache,
        )

        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to FortiMonitor API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON request body
            max_retries: Maximum number of retry attempts for 500 errors

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
        params["api_key"] = self.api_key

        # Retry loop for handling transient errors
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"API Request: {method} {url} (attempt {attempt + 1}/{max_retries})"
                )
                response = self.session.request(
                    method=method, url=url, params=params, json=json_data, timeout=30
                )

                # Handle 500 errors with retry and exponential backoff
                if response.status_code == 500:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(
                            f"FortiMonitor API returned 500 error for {endpoint}. "
                            f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(
                            f"FortiMonitor API returned 500 error after {max_retries} attempts"
                        )
                        raise APIError(
                            f"FortiMonitor API unavailable after {max_retries} retries",
                            status_code=500,
                        )

                # Handle other specific status codes
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key or unauthorized access")
                elif response.status_code == 404:
                    raise NotFoundError(
                        f"Resource not found: {endpoint}", status_code=404
                    )
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded", status_code=429)
                elif response.status_code >= 400:
                    error_msg = response.text or f"API error: {response.status_code}"
                    raise APIError(error_msg, status_code=response.status_code)

                response.raise_for_status()

                # Handle empty responses (common for PUT/POST/DELETE operations)
                if not response.text or response.text.strip() == "":
                    return {"success": True, "status_code": response.status_code}

                try:
                    return response.json()
                except ValueError:
                    # If response is not JSON, return as text
                    return {"success": True, "response": response.text, "status_code": response.status_code}

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed: {e}. Retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                logger.error(f"Request failed after {max_retries} attempts: {str(e)}")
                raise APIError(f"Request failed: {str(e)}")

        # Should never reach here, but just in case
        raise APIError("Request failed for unknown reason")

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
        full: bool = False,
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
            "tag_filter_mode": tag_filter_mode,
        }

        if full:
            params["full"] = "true"
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
        params = {}
        if full:
            params["full"] = "true"
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
        full: bool = False,
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
        }

        if full:
            params["full"] = "true"
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

        response = self._request("GET", "/outage", params=params)

        # Parse response
        return OutageListResponse(**response)

    def get_active_outages(
        self,
        server_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
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
            "offset": offset,
        }

        if server_id:
            params["server"] = server_id  # API expects "server", not "server_id"

        response = self._request("GET", "/outage/active", params=params)
        return OutageListResponse(**response)

    # Agent Resource Operations (Metrics)

    def get_server_agent_resources(
        self,
        server_id: int,
        limit: int = 50,
        offset: int = 0,
        full: bool = False,
    ) -> AgentResourceListResponse:
        """
        Get agent resources (metrics) for a server.

        Args:
            server_id: ID of the server
            limit: Maximum number of results
            offset: Offset for pagination
            full: Resolve all URLs to actual objects

        Returns:
            AgentResourceListResponse with resources and pagination info
        """
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if full:
            params["full"] = "true"

        response = self._request(
            "GET", f"/server/{server_id}/agent_resource", params=params
        )

        # Return structured response
        return AgentResourceListResponse(**response)

    # ============================================================================
    # PHASE 2 - OUTAGE MANAGEMENT METHODS
    # ============================================================================

    def get_current_user_url(self) -> Optional[str]:
        """
        Get the current user's URL for API operations.

        Returns:
            User URL string or None if unable to determine
        """
        try:
            response = self._request("GET", "/user", params={"limit": 1})
            if "user_list" in response and response["user_list"]:
                return response["user_list"][0].get("url")
        except Exception as e:
            logger.warning(f"Could not get current user: {e}")
        return None

    def acknowledge_outage(
        self, outage_id: int, user_url: Optional[str] = None, message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Acknowledge an outage.

        Args:
            outage_id: ID of the outage to acknowledge
            user_url: URL of user acknowledging (auto-detected if not provided)
            message: Optional message to broadcast

        Returns:
            Response from API

        Raises:
            NotFoundError: If outage not found
            APIError: If acknowledgment fails
        """
        endpoint = f"outage/{outage_id}/acknowledge"

        # Get user URL if not provided
        if not user_url:
            user_url = self.get_current_user_url()
            if not user_url:
                raise APIError("Could not determine user URL for acknowledgment")

        # Use PUT with JSON body as per API schema
        data = {"who": user_url}
        if message:
            data["message"] = message
            data["should_broadcast"] = True

        logger.info(f"Acknowledging outage {outage_id} by {user_url}")
        response = self._request("PUT", endpoint, json_data=data)
        return response

    def add_outage_log(
        self, outage_id: int, entry: str, user_url: Optional[str] = None, public: bool = False
    ) -> Dict[str, Any]:
        """
        Add a log entry/note to an outage.

        Args:
            outage_id: ID of the outage
            entry: Log message to add
            user_url: URL of user adding log (auto-detected if not provided)
            public: Whether to make the log entry public

        Returns:
            Response from API

        Raises:
            NotFoundError: If outage not found
            APIError: If log creation fails
        """
        endpoint = f"outage/{outage_id}/outage_log"

        # Get user URL if not provided
        if not user_url:
            user_url = self.get_current_user_url()
            if not user_url:
                raise APIError("Could not determine user URL for log entry")

        data = {
            "entry": entry,
            "user": user_url,
            "public": public,
        }

        logger.info(f"Adding log to outage {outage_id}")
        response = self._request("POST", endpoint, json_data=data)
        return response

    def add_outage_note(self, outage_id: int, note: str) -> OutageNote:
        """
        Add a note/comment to an outage (alias for add_outage_log).

        Args:
            outage_id: ID of the outage
            note: Note text to add

        Returns:
            OutageNote object

        Raises:
            NotFoundError: If outage not found
            APIError: If note creation fails
        """
        response = self.add_outage_log(outage_id, entry=note)
        # Convert response to OutageNote model
        return OutageNote(
            outage=f"{self.base_url}/outage/{outage_id}",
            note=note,
            **{k: v for k, v in response.items() if k in ["id", "created", "created_by"]}
        )

    def get_outage_details(self, outage_id: int, full: bool = False) -> Outage:
        """
        Get detailed information about a specific outage.

        Args:
            outage_id: ID of the outage
            full: Whether to expand nested objects (use with caution)

        Returns:
            Outage object with full details

        Raises:
            NotFoundError: If outage not found
            APIError: If retrieval fails
        """
        endpoint = f"outage/{outage_id}"
        params = {}

        # Note: full=true may cause issues, use sparingly
        if full:
            params["full"] = "true"

        logger.info(f"Getting details for outage {outage_id}")
        response = self._request("GET", endpoint, params=params)
        return Outage(**response)

    # ============================================================================
    # PHASE 2 - SERVER STATUS MANAGEMENT METHODS
    # ============================================================================

    def update_server_status(self, server_id: int, status: str) -> Server:
        """
        Update server monitoring status.

        Args:
            server_id: ID of the server
            status: New status ('active', 'inactive', 'paused')

        Returns:
            Updated Server object

        Raises:
            NotFoundError: If server not found
            APIError: If update fails
        """
        endpoint = f"server/{server_id}"

        valid_statuses = ["active", "inactive", "paused"]
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")

        data = {"status": status}

        logger.info(f"Updating server {server_id} status to {status}")
        response = self._request("PUT", endpoint, json_data=data)
        return Server(**response)

    def update_server(
        self,
        server_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update server properties.

        Args:
            server_id: ID of the server
            name: New server name
            description: New description
            tags: New list of tags (replaces existing)
            status: New status ('active', 'inactive', 'paused')

        Returns:
            API response dict

        Raises:
            NotFoundError: If server not found
            APIError: If update fails
        """
        endpoint = f"server/{server_id}"

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if tags is not None:
            data["tags"] = tags
        if status is not None:
            valid_statuses = ["active", "inactive", "paused"]
            if status not in valid_statuses:
                raise ValueError(f"Status must be one of: {valid_statuses}")
            data["status"] = status

        if not data:
            raise ValueError("At least one field must be provided for update")

        logger.info(f"Updating server {server_id} with {list(data.keys())}")
        response = self._request("PUT", endpoint, json_data=data)
        return response

    # ============================================================================
    # PHASE 2 - MAINTENANCE SCHEDULE METHODS
    # Note: FortiMonitor API uses "maintenance_schedule" not "maintenance_window"
    # ============================================================================

    def create_maintenance_schedule(
        self,
        name: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        duration: Optional[int] = None,
        servers: Optional[List[int]] = None,
        description: Optional[str] = None,
        pause_all_checks: bool = False,
    ) -> MaintenanceWindow:
        """
        Create a maintenance schedule.

        Args:
            name: Name for the maintenance schedule
            start_time: When maintenance begins
            end_time: When maintenance ends (provide either end_time or duration)
            duration: Duration in minutes (provide either end_time or duration)
            servers: List of server IDs to include (targets)
            description: Optional description
            pause_all_checks: Whether to pause all checks during maintenance

        Returns:
            MaintenanceWindow object

        Raises:
            APIError: If creation fails
            ValueError: If neither end_time nor duration provided
        """
        endpoint = "maintenance_schedule"

        # Validate that we have either end_time or duration
        if end_time is None and duration is None:
            raise ValueError("Must provide either end_time or duration")

        # Build the payload using correct API field names
        data = {
            "name": name,
            "original_start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "pause_all_checks": pause_all_checks,
        }

        # Set either original_end_time or duration
        if end_time:
            data["original_end_time"] = end_time.strftime("%Y-%m-%d %H:%M:%S")
        elif duration:
            data["duration"] = duration

        # Convert server IDs to URLs and use "targets" field
        if servers:
            data["targets"] = [f"{self.base_url}/server/{sid}" for sid in servers]

        if description:
            data["description"] = description

        logger.info(f"Creating maintenance schedule: {name}")
        response = self._request("POST", endpoint, json_data=data)

        # Handle response - API may return empty response on success
        if response.get("success") and "url" not in response:
            # Create a minimal MaintenanceWindow with the data we have
            return MaintenanceWindow(
                name=name,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=duration) if duration else end_time,
                servers=[f"{self.base_url}/server/{sid}" for sid in servers] if servers else [],
                description=description,
            )

        return MaintenanceWindow(**response)

    # Alias for backward compatibility
    create_maintenance_window = create_maintenance_schedule

    def list_maintenance_schedules(
        self,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = False,
    ) -> MaintenanceWindowListResponse:
        """
        List maintenance schedules.

        Args:
            limit: Maximum number of results
            offset: Pagination offset
            active_only: Only return currently active schedules

        Returns:
            MaintenanceWindowListResponse object

        Raises:
            APIError: If retrieval fails
        """
        # Use the correct endpoint based on filter
        if active_only:
            endpoint = "maintenance_schedule/active"
        else:
            endpoint = "maintenance_schedule"

        params = {
            "limit": limit,
            "offset": offset,
        }

        logger.info(
            f"Listing maintenance schedules (limit={limit}, active_only={active_only})"
        )
        response = self._request("GET", endpoint, params=params)
        return MaintenanceWindowListResponse(**response)

    # Alias for backward compatibility
    list_maintenance_windows = list_maintenance_schedules

    def get_maintenance_schedule_details(self, schedule_id: int) -> MaintenanceWindow:
        """
        Get details for a specific maintenance schedule.

        Args:
            schedule_id: ID of the maintenance schedule

        Returns:
            MaintenanceWindow object

        Raises:
            NotFoundError: If schedule not found
            APIError: If retrieval fails
        """
        endpoint = f"maintenance_schedule/{schedule_id}"

        logger.info(f"Getting maintenance schedule {schedule_id}")
        response = self._request("GET", endpoint)
        return MaintenanceWindow(**response)

    # Alias for backward compatibility
    get_maintenance_window_details = get_maintenance_schedule_details

    def update_maintenance_schedule(
        self,
        schedule_id: int,
        name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        servers: Optional[List[int]] = None,
        suppress_notifications: Optional[bool] = None,
    ) -> MaintenanceWindow:
        """
        Update a maintenance schedule.

        Args:
            schedule_id: ID of the maintenance schedule
            name: New name
            start_time: New start time
            end_time: New end time
            servers: New list of server IDs
            suppress_notifications: New notification suppression setting

        Returns:
            Updated MaintenanceWindow object

        Raises:
            NotFoundError: If schedule not found
            APIError: If update fails
        """
        endpoint = f"maintenance_schedule/{schedule_id}"

        data = {}
        if name:
            data["name"] = name
        if start_time:
            data["start"] = start_time.isoformat()
        if end_time:
            data["end"] = end_time.isoformat()
        if servers is not None:
            data["servers"] = [f"{self.base_url}/server/{sid}" for sid in servers]
        if suppress_notifications is not None:
            data["suppress_notification"] = suppress_notifications

        if not data:
            raise ValueError("At least one field must be provided for update")

        logger.info(f"Updating maintenance schedule {schedule_id}")
        response = self._request("PUT", endpoint, json_data=data)
        return MaintenanceWindow(**response)

    # Alias for backward compatibility
    update_maintenance_window = update_maintenance_schedule

    def delete_maintenance_schedule(self, schedule_id: int) -> bool:
        """
        Delete a maintenance schedule.

        Args:
            schedule_id: ID of the maintenance schedule to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If schedule not found
            APIError: If deletion fails
        """
        endpoint = f"maintenance_schedule/{schedule_id}"

        logger.info(f"Deleting maintenance schedule {schedule_id}")
        self._request("DELETE", endpoint)
        return True

    # Alias for backward compatibility
    delete_maintenance_window = delete_maintenance_schedule

    # ============================================================================
    # PHASE 2 - PRIORITY 3: SERVER GROUP METHODS
    # ============================================================================

    def list_server_groups(
        self, limit: int = 50, offset: int = 0
    ) -> "ServerGroupListResponse":
        """
        List all server groups.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            ServerGroupListResponse object

        Raises:
            APIError: If retrieval fails
        """
        from .models import ServerGroupListResponse

        endpoint = "server_group"
        params = {"limit": limit, "offset": offset}

        logger.info(f"Listing server groups (limit={limit})")
        response = self._request("GET", endpoint, params=params)
        return ServerGroupListResponse(**response)

    def get_server_group_details(self, group_id: int) -> "ServerGroup":
        """
        Get details for a specific server group.

        Args:
            group_id: ID of the server group

        Returns:
            ServerGroup object

        Raises:
            NotFoundError: If group not found
            APIError: If retrieval fails
        """
        from .models import ServerGroup

        endpoint = f"server_group/{group_id}"

        logger.info(f"Getting server group {group_id}")
        response = self._request("GET", endpoint)
        return ServerGroup(**response)

    def create_server_group(
        self,
        name: str,
        description: Optional[str] = None,
        server_ids: Optional[List[int]] = None,
    ) -> "ServerGroup":
        """
        Create a new server group.

        Args:
            name: Name of the group
            description: Optional description
            server_ids: Optional list of server IDs to include

        Returns:
            ServerGroup object

        Raises:
            APIError: If creation fails
        """
        from .models import ServerGroup

        endpoint = "server_group"

        # Build server URLs
        server_urls = []
        if server_ids:
            server_urls = [f"{self.base_url}/server/{sid}" for sid in server_ids]

        data = {"name": name, "servers": server_urls}
        if description:
            data["description"] = description

        logger.info(f"Creating server group: {name}")
        response = self._request("POST", endpoint, json_data=data)

        # Handle different response formats
        if isinstance(response, dict):
            # Check if it's a success response without object details
            if "success" in response and response.get("success") is True:
                # API returned success but not the object details
                # Fetch the created group by listing and finding by name
                logger.info("Server group created, fetching details by name...")

                groups_response = self.list_server_groups(limit=100)

                # Find by name (check most recent first)
                for group in reversed(groups_response.server_group_list):
                    if group.name == name:
                        logger.info(f"Found created group with ID: {group.id}")
                        return group

                # If not found, return minimal ServerGroup
                logger.warning("Could not find created group, returning minimal object")
                return ServerGroup(
                    name=name,
                    description=description,
                    servers=server_urls,
                )

            # Normal response with object details
            elif "name" in response:
                return ServerGroup(**response)

            else:
                raise APIError(f"Unexpected response format: {response}")

        raise APIError(f"Invalid response type: {type(response)}")

    def update_server_group(
        self,
        group_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        server_ids: Optional[List[int]] = None,
    ) -> "ServerGroup":
        """
        Update a server group.

        Args:
            group_id: ID of the group to update
            name: New name
            description: New description
            server_ids: New list of server IDs (replaces existing)

        Returns:
            ServerGroup object

        Raises:
            NotFoundError: If group not found
            APIError: If update fails
        """
        from .models import ServerGroup

        endpoint = f"server_group/{group_id}"

        # FIXED: Get current group to preserve required fields
        current_group = self.get_server_group_details(group_id)

        # Build update with ALL required fields
        data = {
            "name": name if name is not None else current_group.name,  # Required
        }

        # Handle servers
        if server_ids is not None:
            data["servers"] = [f"{self.base_url}/server/{sid}" for sid in server_ids]
        else:
            data["servers"] = current_group.servers if current_group.servers else []

        # Handle description
        if description is not None:
            data["description"] = description
        elif current_group.description:
            data["description"] = current_group.description

        logger.info(f"Updating server group {group_id}")
        response = self._request("PUT", endpoint, json_data=data)

        # Handle response format
        if isinstance(response, dict) and "success" in response:
            # Fetch updated group details
            return self.get_server_group_details(group_id)

        return ServerGroup(**response)

    def add_servers_to_group(self, group_id: int, server_ids: List[int]) -> "ServerGroup":
        """
        Add servers to an existing group.

        Args:
            group_id: ID of the group
            server_ids: Server IDs to add

        Returns:
            Updated ServerGroup object

        Raises:
            NotFoundError: If group not found
            APIError: If update fails
        """
        import re

        if not server_ids:
            raise ValueError("server_ids cannot be empty")

        endpoint = f"server_group/{group_id}"

        # Get current group details
        current_group = self.get_server_group_details(group_id)

        # Get current server URLs
        current_servers = current_group.servers if current_group.servers else []

        # Add new server URLs
        new_server_urls = [f"{self.base_url}/server/{sid}" for sid in server_ids]

        # Combine (avoid duplicates)
        all_servers = list(set(current_servers + new_server_urls))

        # FIXED: Include ALL required fields
        data = {
            "name": current_group.name,  # Required
            "servers": all_servers,
        }

        # Add description if it exists
        if current_group.description:
            data["description"] = current_group.description

        logger.info(f"Adding {len(server_ids)} servers to group {group_id}")
        response = self._request("PUT", endpoint, json_data=data)

        # Handle response format
        if isinstance(response, dict) and "success" in response:
            return self.get_server_group_details(group_id)

        from .models import ServerGroup
        return ServerGroup(**response)

    def remove_servers_from_group(
        self, group_id: int, server_ids: List[int]
    ) -> "ServerGroup":
        """
        Remove servers from a group.

        Args:
            group_id: ID of the group
            server_ids: Server IDs to remove

        Returns:
            Updated ServerGroup object

        Raises:
            NotFoundError: If group not found
            APIError: If update fails
        """
        if not server_ids:
            raise ValueError("server_ids cannot be empty")

        endpoint = f"server_group/{group_id}"

        # Get current group details
        current_group = self.get_server_group_details(group_id)

        # Get current server URLs
        current_servers = current_group.servers if current_group.servers else []

        # Create URLs for servers to remove
        remove_server_urls = {f"{self.base_url}/server/{sid}" for sid in server_ids}

        # Remove specified servers
        remaining_servers = [s for s in current_servers if s not in remove_server_urls]

        # FIXED: Include ALL required fields
        data = {
            "name": current_group.name,  # Required
            "servers": remaining_servers,
        }

        # Add description if it exists
        if current_group.description:
            data["description"] = current_group.description

        logger.info(f"Removing {len(server_ids)} servers from group {group_id}")
        response = self._request("PUT", endpoint, json_data=data)

        # Handle response format
        if isinstance(response, dict) and "success" in response:
            return self.get_server_group_details(group_id)

        from .models import ServerGroup
        return ServerGroup(**response)

    def delete_server_group(self, group_id: int) -> bool:
        """
        Delete a server group.

        Args:
            group_id: ID of the group to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If group not found
            APIError: If deletion fails
        """
        endpoint = f"server_group/{group_id}"

        logger.info(f"Deleting server group {group_id}")
        self._request("DELETE", endpoint)
        return True

    # ============================================================================
    # PHASE 2 - PRIORITY 3: SERVER TEMPLATE METHODS
    # ============================================================================

    def list_server_templates(
        self, limit: int = 50, offset: int = 0
    ) -> "ServerTemplateListResponse":
        """
        List all server templates.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            ServerTemplateListResponse object

        Raises:
            APIError: If retrieval fails
        """
        from .models import ServerTemplateListResponse

        endpoint = "server_template"
        params = {"limit": limit, "offset": offset}

        logger.info(f"Listing server templates (limit={limit})")
        response = self._request("GET", endpoint, params=params)
        return ServerTemplateListResponse(**response)

    def get_server_template_details(self, template_id: int) -> "ServerTemplate":
        """
        Get details for a specific template.

        Args:
            template_id: ID of the template

        Returns:
            ServerTemplate object

        Raises:
            NotFoundError: If template not found
            APIError: If retrieval fails
        """
        from .models import ServerTemplate

        endpoint = f"server_template/{template_id}"

        logger.info(f"Getting server template {template_id}")
        response = self._request("GET", endpoint)
        return ServerTemplate(**response)

    def apply_template_to_server(
        self, server_id: int, template_id: int
    ) -> Dict[str, Any]:
        """
        Apply a monitoring template to a server.

        Args:
            server_id: ID of the server
            template_id: ID of the template to apply

        Returns:
            API response dict

        Raises:
            NotFoundError: If server or template not found
            APIError: If application fails
        """
        endpoint = f"server/{server_id}"

        template_url = f"{self.base_url}/server_template/{template_id}"
        data = {"server_template": template_url}

        logger.info(f"Applying template {template_id} to server {server_id}")
        response = self._request("PUT", endpoint, json_data=data)
        return response

    # ============================================================================
    # PHASE 2 - PRIORITY 4: NOTIFICATION METHODS
    # ============================================================================

    def list_notification_schedules(
        self, limit: int = 50, offset: int = 0
    ) -> "NotificationScheduleListResponse":
        """
        List all notification schedules.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            NotificationScheduleListResponse object

        Raises:
            APIError: If retrieval fails
        """
        from .models import NotificationScheduleListResponse

        endpoint = "notification_schedule"
        params = {"limit": limit, "offset": offset}

        logger.info(f"Listing notification schedules (limit={limit})")
        response = self._request("GET", endpoint, params=params)
        return NotificationScheduleListResponse(**response)

    def get_notification_schedule_details(
        self, schedule_id: int
    ) -> "NotificationSchedule":
        """
        Get details for a specific notification schedule.

        Args:
            schedule_id: ID of the notification schedule

        Returns:
            NotificationSchedule object

        Raises:
            NotFoundError: If schedule not found
            APIError: If retrieval fails
        """
        from .models import NotificationSchedule

        endpoint = f"notification_schedule/{schedule_id}"

        logger.info(f"Getting notification schedule {schedule_id}")
        response = self._request("GET", endpoint)
        return NotificationSchedule(**response)

    def list_contact_groups(
        self, limit: int = 50, offset: int = 0
    ) -> "ContactGroupListResponse":
        """
        List all contact groups.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            ContactGroupListResponse object

        Raises:
            APIError: If retrieval fails
        """
        from .models import ContactGroupListResponse

        endpoint = "contact_group"
        params = {"limit": limit, "offset": offset}

        logger.info(f"Listing contact groups (endpoint={endpoint}, limit={limit})")
        response = self._request("GET", endpoint, params=params)
        return ContactGroupListResponse(**response)

    def get_contact_group_details(self, group_id: int) -> "ContactGroup":
        """
        Get details for a specific contact group.

        Args:
            group_id: ID of the contact group

        Returns:
            ContactGroup object

        Raises:
            NotFoundError: If group not found
            APIError: If retrieval fails
        """
        from .models import ContactGroup

        endpoint = f"contact_group/{group_id}"

        logger.info(f"Getting contact group {group_id} (endpoint={endpoint})")
        response = self._request("GET", endpoint)
        return ContactGroup(**response)

    def list_contacts(self, limit: int = 100, offset: int = 0) -> "ContactListResponse":
        """
        List all notification contacts.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            ContactListResponse object

        Raises:
            APIError: If retrieval fails
        """
        from .models import ContactListResponse

        endpoint = "contact"
        params = {"limit": limit, "offset": offset}

        logger.info(f"Listing contacts (limit={limit})")
        response = self._request("GET", endpoint, params=params)
        return ContactListResponse(**response)

    def get_contact_details(self, contact_id: int) -> "Contact":
        """
        Get details for a specific contact.

        Args:
            contact_id: ID of the contact

        Returns:
            Contact object

        Raises:
            NotFoundError: If contact not found
            APIError: If retrieval fails
        """
        from .models import Contact

        endpoint = f"contact/{contact_id}"

        logger.info(f"Getting contact {contact_id}")
        response = self._request("GET", endpoint)
        return Contact(**response)

    # ============================================================================
    # PHASE 2 - PRIORITY 4: AGENT RESOURCE METHODS
    # ============================================================================

    def list_agent_resource_types(
        self, limit: int = 100, offset: int = 0
    ) -> "AgentResourceTypeListResponse":
        """
        List all available agent resource types (metric types).

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            AgentResourceTypeListResponse object

        Raises:
            APIError: If retrieval fails
        """
        from .models import AgentResourceTypeListResponse

        endpoint = "agent_resource_type"
        params = {"limit": limit, "offset": offset}

        logger.info(f"Listing agent resource types (limit={limit})")
        response = self._request("GET", endpoint, params=params)
        return AgentResourceTypeListResponse(**response)

    def get_agent_resource_type_details(self, type_id: int) -> "AgentResourceType":
        """
        Get details for a specific agent resource type.

        Args:
            type_id: ID of the agent resource type

        Returns:
            AgentResourceType object

        Raises:
            NotFoundError: If type not found
            APIError: If retrieval fails
        """
        from .models import AgentResourceType

        endpoint = f"agent_resource_type/{type_id}"

        logger.info(f"Getting agent resource type {type_id}")
        response = self._request("GET", endpoint)
        return AgentResourceType(**response)

    def list_server_agent_resources(
        self, server_id: int, limit: int = 100, offset: int = 0
    ) -> "AgentResourceListResponse":
        """
        List all agent resources (metrics) for a specific server.

        Args:
            server_id: ID of the server
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            AgentResourceListResponse object

        Raises:
            NotFoundError: If server not found
            APIError: If retrieval fails
        """
        # Use existing AgentResourceListResponse from models
        endpoint = f"server/{server_id}/agent_resource"
        params = {"limit": limit, "offset": offset}

        logger.info(f"Listing agent resources for server {server_id}")
        response = self._request("GET", endpoint, params=params)
        return AgentResourceListResponse(**response)

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
