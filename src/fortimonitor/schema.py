"""Schema discovery and validation for FortiMonitor API."""

import json
import logging
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import requests

from .exceptions import SchemaError

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages FortiMonitor API schema discovery and caching."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = 86400,
        enable_cache: bool = True,
    ):
        """
        Initialize schema manager.

        Args:
            api_key: FortiMonitor API key
            base_url: API base URL
            cache_dir: Directory for schema cache
            cache_ttl: Cache TTL in seconds
            enable_cache: Whether to enable caching
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.cache_dir = cache_dir or Path("cache/schemas")
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache

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
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
                self._resource_list = cached_data.get("resources", [])
                return self._resource_list

        # Fetch from API
        try:
            url = f"{self.base_url}/schema/resources"
            params = {"api_key": self.api_key}

            logger.info("Fetching resource list from API")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            resources = [api["path"].split("/")[-1] for api in data.get("apis", [])]
            self._resource_list = resources

            # Cache the result
            if self.enable_cache:
                cache_data = {
                    "timestamp": datetime.now().isoformat(),
                    "resources": resources,
                }
                with open(cache_file, "w") as f:
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
            with open(cache_file, "r") as f:
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
                with open(cache_file, "w") as f:
                    json.dump(schema, f, indent=2)

            logger.info(f"Loaded schema for {resource_name}")
            return schema

        except requests.exceptions.RequestException as e:
            raise SchemaError(f"Failed to fetch schema for {resource_name}: {e}")

    def get_operation_parameters(
        self, resource_name: str, path: str, method: str
    ) -> List[Dict[str, Any]]:
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

        for api in schema.get("apis", []):
            if api.get("path") == path:
                for operation in api.get("operations", []):
                    if operation.get("method", "").upper() == method.upper():
                        return operation.get("parameters", [])

        return []

    def validate_parameters(
        self,
        resource_name: str,
        path: str,
        method: str,
        provided_params: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
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
            if param.get("required", False):
                param_name = param.get("name")
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

    def clear_cache(self) -> None:
        """Clear all cached schemas."""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Schema cache cleared")

        self._resource_list = None
        self._schemas = {}
