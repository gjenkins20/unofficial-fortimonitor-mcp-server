"""FortiMonitor API client implementation."""

import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
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
                return response.json()

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

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
