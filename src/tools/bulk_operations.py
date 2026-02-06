"""Bulk operations and advanced search tools - Phase 2 Priority 2."""

import logging
import asyncio
import re
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# BULK OPERATION FRAMEWORK
# ============================================================================


@dataclass
class BulkOperationResult:
    """Result of a single operation in a bulk request."""

    item_id: Any
    status: str  # 'success' or 'failed'
    result: Any = None
    error: str = None


class BulkOperationExecutor:
    """Execute operations in bulk with progress tracking."""

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize bulk executor.

        Args:
            max_concurrent: Maximum number of concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_single(
        self,
        operation: Callable,
        item_id: Any,
        *args,
        **kwargs
    ) -> BulkOperationResult:
        """
        Execute a single operation with error handling.

        Args:
            operation: Function to execute
            item_id: Identifier for this item (for tracking)
            *args, **kwargs: Arguments for the operation

        Returns:
            BulkOperationResult
        """
        async with self.semaphore:
            try:
                logger.debug(f"Executing operation for item {item_id}")

                # Execute the operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    # Run sync function in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, lambda: operation(*args, **kwargs)
                    )

                return BulkOperationResult(
                    item_id=item_id,
                    status='success',
                    result=result
                )

            except Exception as e:
                logger.error(f"Operation failed for item {item_id}: {e}")
                return BulkOperationResult(
                    item_id=item_id,
                    status='failed',
                    error=str(e)
                )

    async def execute_bulk(
        self,
        operation: Callable,
        items: List[Any],
        get_id: Callable[[Any], Any] = None,
        **operation_kwargs
    ) -> List[BulkOperationResult]:
        """
        Execute operation for multiple items.

        Args:
            operation: Function to execute for each item
            items: List of items to process
            get_id: Function to extract ID from item (default: use item itself)
            **operation_kwargs: Additional kwargs for operation

        Returns:
            List of BulkOperationResult
        """
        if get_id is None:
            get_id = lambda x: x

        logger.info(f"Starting bulk operation for {len(items)} items")

        # Create tasks for all items
        tasks = [
            self.execute_single(
                operation,
                get_id(item),
                item,
                **operation_kwargs
            )
            for item in items
        ]

        # Execute all tasks
        results = await asyncio.gather(*tasks)

        # Log summary
        success_count = sum(1 for r in results if r.status == 'success')
        failed_count = len(results) - success_count

        logger.info(
            f"Bulk operation complete: {success_count} succeeded, {failed_count} failed"
        )

        return results


def format_bulk_results(
    results: List[BulkOperationResult],
    operation_name: str
) -> str:
    """
    Format bulk operation results for display.

    Args:
        results: List of operation results
        operation_name: Name of the operation (for display)

    Returns:
        Formatted string
    """
    success_count = sum(1 for r in results if r.status == 'success')
    failed_count = len(results) - success_count

    lines = [
        f"**Bulk {operation_name} Results**\n",
        f"Total: {len(results)} items",
        f"Succeeded: {success_count}",
        f"Failed: {failed_count}\n"
    ]

    # Show first few successes
    successes = [r for r in results if r.status == 'success']
    if successes:
        lines.append("**Successful Operations:**")
        for r in successes[:5]:  # Show first 5
            lines.append(f"  - Item {r.item_id}")
        if len(successes) > 5:
            lines.append(f"  ... and {len(successes) - 5} more")

    # Show all failures
    failures = [r for r in results if r.status == 'failed']
    if failures:
        lines.append("\n**Failed Operations:**")
        for r in failures:
            lines.append(f"  - Item {r.item_id}: {r.error}")

    return "\n".join(lines)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def bulk_acknowledge_outages_tool_definition() -> Tool:
    """Return tool definition for bulk outage acknowledgment."""
    return Tool(
        name="bulk_acknowledge_outages",
        description=(
            "Acknowledge multiple outages at once. "
            "Useful for acknowledging all outages for a specific server, "
            "severity level, or group of related issues."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "outage_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description":"List of outage IDs to acknowledge"
                },
                "note": {
                    "type": "string",
                    "description":"Optional note to add to all acknowledged outages"
                }
            },
            "required": ["outage_ids"]
        }
    )


def bulk_add_tags_tool_definition() -> Tool:
    """Return tool definition for bulk tag addition."""
    return Tool(
        name="bulk_add_tags",
        description=(
            "Add tags to multiple servers at once. "
            "Tags help organize and filter servers. "
            "New tags are added without removing existing ones."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description":"List of server IDs to tag"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description":"List of tags to add to each server"
                }
            },
            "required": ["server_ids", "tags"]
        }
    )


def bulk_remove_tags_tool_definition() -> Tool:
    """Return tool definition for bulk tag removal."""
    return Tool(
        name="bulk_remove_tags",
        description=(
            "Remove tags from multiple servers at once. "
            "Only the specified tags are removed; other tags remain."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description":"List of server IDs"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description":"List of tags to remove from each server"
                }
            },
            "required": ["server_ids", "tags"]
        }
    )


def search_servers_advanced_tool_definition() -> Tool:
    """Return tool definition for advanced server search."""
    return Tool(
        name="search_servers_advanced",
        description=(
            "Search servers with multiple criteria. "
            "Supports filtering by name pattern, status, tags, and whether server has active outages. "
            "All filters are combined with AND logic."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name_contains": {
                    "type": "string",
                    "description":"Filter by servers whose name contains this string (case-insensitive)"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "paused"],
                    "description":"Filter by monitoring status"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description":"Filter by tags (servers must have ALL specified tags)"
                },
                "has_active_outages": {
                    "type": "boolean",
                    "description":"If true, only return servers with active outages"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description":"Maximum number of results (default 50)"
                }
            }
        }
    )


def get_servers_with_active_outages_tool_definition() -> Tool:
    """Return tool definition for getting servers with active outages."""
    return Tool(
        name="get_servers_with_active_outages",
        description=(
            "Get all servers that currently have active outages. "
            "Useful for quickly identifying problematic servers. "
            "Returns server details along with their active outage count and severity."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["critical", "warning", "info"],
                    "description":"Optional filter by outage severity"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description":"Maximum number of servers to return (default 50)"
                }
            }
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_bulk_acknowledge_outages(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle bulk_acknowledge_outages tool execution."""
    try:
        outage_ids = arguments.get("outage_ids", [])
        note = arguments.get("note")

        if not outage_ids:
            return [TextContent(
                type="text",
                text="Error: No outage IDs provided"
            )]

        if len(outage_ids) > 50:
            return [TextContent(
                type="text",
                text="Error: Too many outages. Please limit to 50 at a time."
            )]

        logger.info(f"Bulk acknowledging {len(outage_ids)} outages")

        # Create bulk executor
        executor = BulkOperationExecutor(max_concurrent=5)

        # Define operation for single acknowledgment
        def acknowledge_single(outage_id: int) -> Dict[str, Any]:
            result = client.acknowledge_outage(outage_id=outage_id)
            if note:
                try:
                    client.add_outage_log(outage_id=outage_id, entry=note)
                except Exception as e:
                    logger.warning(f"Failed to add note to outage {outage_id}: {e}")
            return result

        # Execute bulk operation
        results = await executor.execute_bulk(
            operation=acknowledge_single,
            items=outage_ids
        )

        # Format results
        formatted = format_bulk_results(results, "Acknowledge Outages")

        if note:
            formatted += f"\n\nNote added to successful acknowledgments: \"{note}\""

        return [TextContent(type="text", text=formatted)]

    except Exception as e:
        logger.exception("Error in bulk acknowledge")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_bulk_add_tags(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle bulk_add_tags tool execution."""
    try:
        server_ids = arguments.get("server_ids", [])
        tags = arguments.get("tags", [])

        if not server_ids:
            return [TextContent(
                type="text",
                text="Error: No server IDs provided"
            )]

        if not tags:
            return [TextContent(
                type="text",
                text="Error: No tags provided"
            )]

        if len(server_ids) > 100:
            return [TextContent(
                type="text",
                text="Error: Too many servers. Please limit to 100 at a time."
            )]

        logger.info(f"Bulk adding {len(tags)} tags to {len(server_ids)} servers")

        executor = BulkOperationExecutor(max_concurrent=10)

        # Define operation for single tag addition
        # Note: FortiMonitor API requires ALL fields when updating
        def add_tags_single(server_id: int) -> Dict[str, Any]:
            # Get current server details
            server = client.get_server_details(server_id)

            # Get current tags
            current_tags = []
            if server.tags:
                if isinstance(server.tags, list):
                    current_tags = server.tags
                elif isinstance(server.tags, str):
                    current_tags = [t.strip() for t in server.tags.split(',') if t.strip()]

            # Add new tags (avoid duplicates)
            new_tags = list(set(current_tags + tags))

            # Build update data with ALL required fields
            endpoint = f"server/{server_id}"
            data = {
                'name': server.name,
                'fqdn': server.fqdn or server.name,  # Use name as fallback
                'tags': new_tags
            }

            # Add server_group if it exists
            if hasattr(server, 'server_group') and server.server_group:
                data['server_group'] = server.server_group

            # Make direct API request with all required fields
            response = client._request('PUT', endpoint, json_data=data)
            return response

        # Execute bulk operation
        results = await executor.execute_bulk(
            operation=add_tags_single,
            items=server_ids
        )

        # Format results
        formatted = format_bulk_results(results, "Add Tags")
        formatted += f"\n\nTags added: {', '.join(tags)}"

        return [TextContent(type="text", text=formatted)]

    except Exception as e:
        logger.exception("Error in bulk add tags")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_bulk_remove_tags(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle bulk_remove_tags tool execution."""
    try:
        server_ids = arguments.get("server_ids", [])
        tags = arguments.get("tags", [])

        if not server_ids:
            return [TextContent(
                type="text",
                text="Error: No server IDs provided"
            )]

        if not tags:
            return [TextContent(
                type="text",
                text="Error: No tags provided"
            )]

        if len(server_ids) > 100:
            return [TextContent(
                type="text",
                text="Error: Too many servers. Please limit to 100 at a time."
            )]

        logger.info(f"Bulk removing {len(tags)} tags from {len(server_ids)} servers")

        executor = BulkOperationExecutor(max_concurrent=10)

        # Define operation for single tag removal
        # Note: FortiMonitor API requires ALL fields when updating
        def remove_tags_single(server_id: int) -> Dict[str, Any]:
            # Get current server details
            server = client.get_server_details(server_id)

            # Get current tags
            current_tags = []
            if server.tags:
                if isinstance(server.tags, list):
                    current_tags = server.tags
                elif isinstance(server.tags, str):
                    current_tags = [t.strip() for t in server.tags.split(',') if t.strip()]

            # Remove specified tags
            new_tags = [t for t in current_tags if t not in tags]

            # Build update data with ALL required fields
            endpoint = f"server/{server_id}"
            data = {
                'name': server.name,
                'fqdn': server.fqdn or server.name,  # Use name as fallback
                'tags': new_tags
            }

            # Add server_group if it exists
            if hasattr(server, 'server_group') and server.server_group:
                data['server_group'] = server.server_group

            # Make direct API request with all required fields
            response = client._request('PUT', endpoint, json_data=data)
            return response

        # Execute bulk operation
        results = await executor.execute_bulk(
            operation=remove_tags_single,
            items=server_ids
        )

        # Format results
        formatted = format_bulk_results(results, "Remove Tags")
        formatted += f"\n\nTags removed: {', '.join(tags)}"

        return [TextContent(type="text", text=formatted)]

    except Exception as e:
        logger.exception("Error in bulk remove tags")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_search_servers_advanced(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle search_servers_advanced tool execution."""
    try:
        name_contains = arguments.get("name_contains")
        status = arguments.get("status")
        tags = arguments.get("tags", [])
        has_active_outages = arguments.get("has_active_outages", False)
        limit = arguments.get("limit", 50)

        logger.info(f"Advanced server search with criteria: {arguments}")

        # Build API-level filters where possible
        api_params = {"limit": 500}  # Get more to filter client-side
        if status:
            api_params["status"] = status
        if tags:
            api_params["tags"] = tags

        # Get servers with API filters
        all_servers_response = client.get_servers(**api_params)
        servers = all_servers_response.server_list

        # Apply client-side filters
        filtered_servers = servers

        # Filter by name (case-insensitive contains)
        if name_contains:
            name_lower = name_contains.lower()
            filtered_servers = [
                s for s in filtered_servers
                if name_lower in s.name.lower()
            ]

        # Filter by active outages if requested
        if has_active_outages:
            # Get all active outages
            outages_response = client.get_active_outages(limit=500)
            outage_server_ids = set()

            for outage in outages_response.outage_list:
                server_url = outage.server
                if server_url:
                    # Extract server ID from URL
                    match = re.search(r'/server/(\d+)', server_url)
                    if match:
                        outage_server_ids.add(int(match.group(1)))

            # Filter servers that have outages
            filtered_servers = [
                s for s in filtered_servers
                if s.id in outage_server_ids
            ]

        # Apply limit
        filtered_servers = filtered_servers[:limit]

        # Format results
        if not filtered_servers:
            return [TextContent(
                type="text",
                text="No servers found matching the specified criteria."
            )]

        output_lines = [
            f"**Advanced Search Results**\n",
            f"Found {len(filtered_servers)} server(s):\n"
        ]

        for server in filtered_servers:
            output_lines.append(f"\n**{server.name}** (ID: {server.id})")
            output_lines.append(f"  Status: {server.status}")
            if server.fqdn:
                output_lines.append(f"  FQDN: {server.fqdn}")
            if server.tags:
                tags_str = ', '.join(server.tags) if isinstance(server.tags, list) else server.tags
                output_lines.append(f"  Tags: {tags_str}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.exception("Error in advanced search")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_get_servers_with_active_outages(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_servers_with_active_outages tool execution."""
    try:
        severity = arguments.get("severity")
        limit = arguments.get("limit", 50)

        logger.info("Getting servers with active outages")

        # Get all active outages
        outages_response = client.get_active_outages(limit=500)
        outages = outages_response.outage_list

        # Filter by severity if specified
        if severity:
            outages = [o for o in outages if o.severity == severity]

        # Group outages by server
        server_outages: Dict[int, List] = {}
        for outage in outages:
            server_url = outage.server
            if server_url:
                # Extract server ID from URL
                match = re.search(r'/server/(\d+)', server_url)
                if match:
                    server_id = int(match.group(1))
                    if server_id not in server_outages:
                        server_outages[server_id] = []
                    server_outages[server_id].append(outage)

        # Get server details for each
        servers_with_issues = []
        servers_not_found = []

        for server_id, outage_list in list(server_outages.items())[:limit]:
            try:
                server = client.get_server_details(server_id)
                servers_with_issues.append({
                    'server': server,
                    'outages': outage_list
                })
            except NotFoundError:
                servers_not_found.append(server_id)
                logger.warning(f"Server {server_id} not found (may be deleted)")
            except Exception as e:
                logger.warning(f"Error getting server {server_id}: {e}")

        # Format results
        if not servers_with_issues and not servers_not_found:
            severity_str = f" (severity: {severity})" if severity else ""
            return [TextContent(
                type="text",
                text=f"No servers with active outages{severity_str} found."
            )]

        output_lines = [
            f"**Servers with Active Outages**\n",
            f"Found {len(servers_with_issues)} server(s) with issues:\n"
        ]

        for item in servers_with_issues:
            server = item['server']
            outage_list = item['outages']

            # Count by severity
            severity_counts = {}
            for outage in outage_list:
                sev = outage.severity
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            output_lines.append(f"\n**{server.name}** (ID: {server.id})")
            output_lines.append(f"  Status: {server.status}")
            output_lines.append(f"  Active Outages: {len(outage_list)}")

            if severity_counts:
                counts_str = ", ".join(f"{k}: {v}" for k, v in severity_counts.items())
                output_lines.append(f"  Severity Breakdown: {counts_str}")

            # Show first few outages
            for outage in outage_list[:3]:
                start_str = outage.start_time.strftime('%Y-%m-%d %H:%M') if outage.start_time else 'Unknown'
                output_lines.append(f"    - [{outage.severity}] {outage.status} (started: {start_str})")

            if len(outage_list) > 3:
                output_lines.append(f"    ... and {len(outage_list) - 3} more outages")

        # Add note about servers not found
        if servers_not_found:
            output_lines.append(f"\n**Note**: {len(servers_not_found)} server(s) not accessible via API:")
            output_lines.append(f"  IDs: {', '.join(map(str, servers_not_found))}")
            output_lines.append(f"  These servers may have been deleted or are not accessible with current API key.")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.exception("Error getting servers with outages")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
