"""License utilization and addon catalog tools for FortiMonitor."""

import json
import logging
import os
from collections import defaultdict
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def get_license_utilization_tool_definition() -> Tool:
    """Return tool definition for license utilization report."""
    return Tool(
        name="get_license_utilization",
        description=(
            "Generate a license utilization report showing instance counts by addon/billing type. "
            "Aggregates all servers by billing_type and device_sub_type to show current usage. "
            "If LICENSE_ENTITLEMENTS is configured in .env, also shows licensed counts and "
            "utilization percentages with warnings for high usage. "
            "Users can find their licensed counts at https://support.fortinet.com/ "
            "under Asset Management > Product List."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    )


def list_addon_catalog_tool_definition() -> Tool:
    """Return tool definition for listing the addon catalog."""
    return Tool(
        name="list_addon_catalog",
        description=(
            "List all available addon types from the FortiMonitor addon catalog. "
            "Useful for seeing valid textkeys when configuring LICENSE_ENTITLEMENTS in .env."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum number of addons to return (default 100)",
                }
            },
        },
    )


# ============================================================================
# HELPERS
# ============================================================================


def _load_entitlements() -> dict | None:
    """Load license entitlements from environment variable."""
    raw = os.environ.get("LICENSE_ENTITLEMENTS")
    if not raw:
        return None
    try:
        entitlements = json.loads(raw)
        if isinstance(entitlements, dict):
            return entitlements
        logger.warning("LICENSE_ENTITLEMENTS is not a JSON object, ignoring")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LICENSE_ENTITLEMENTS: {e}")
        return None


def _fetch_all_servers(client: FortiMonitorClient) -> list:
    """Fetch all servers, paginating if necessary."""
    all_servers = []
    limit = 500
    offset = 0

    while True:
        response = client._request(
            "GET", "server", params={"limit": limit, "offset": offset}
        )
        servers = response.get("server_list", [])
        all_servers.extend(servers)

        meta = response.get("meta", {})
        total_count = meta.get("total_count", len(all_servers))

        if len(all_servers) >= total_count or not servers:
            break
        offset += limit

    return all_servers


def _build_addon_name_map(client: FortiMonitorClient) -> dict:
    """Fetch addon catalog and build textkey -> name mapping."""
    try:
        response = client._request("GET", "addon", params={"limit": 200})
        addons = response.get("addon_list", [])
        return {
            addon.get("textkey", ""): addon.get("name", addon.get("textkey", ""))
            for addon in addons
            if addon.get("textkey")
        }
    except (APIError, Exception):
        return {}


def _aggregate_servers(servers: list) -> dict:
    """Aggregate servers by billing_type, with device_sub_type breakdown.

    Returns:
        {
            "instance.basic": {
                "count": 33,
                "subtypes": {"server": 33}
            },
            "instance.advanced": {
                "count": 18,
                "subtypes": {"server": 8, "network_device (fortinet.fortigate)": 3, ...}
            }
        }
    """
    aggregation = defaultdict(lambda: {"count": 0, "subtypes": defaultdict(int)})

    for server in servers:
        billing_type = server.get("billing_type", "unknown")
        device_type = server.get("device_type", "")
        device_sub_type = server.get("device_sub_type", "")

        aggregation[billing_type]["count"] += 1

        if device_sub_type:
            subtype_key = f"{device_type} ({device_sub_type})" if device_type else device_sub_type
        elif device_type:
            subtype_key = device_type
        else:
            subtype_key = "unknown"

        aggregation[billing_type]["subtypes"][subtype_key] += 1

    return dict(aggregation)


# ============================================================================
# HANDLERS
# ============================================================================


async def handle_get_license_utilization(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_license_utilization tool execution."""
    try:
        servers = _fetch_all_servers(client)
        addon_names = _build_addon_name_map(client)
        entitlements = _load_entitlements()
        aggregation = _aggregate_servers(servers)

        total_instances = sum(data["count"] for data in aggregation.values())

        output_lines = ["**License Utilization Report**\n"]

        # Sort by count descending
        sorted_types = sorted(
            aggregation.items(), key=lambda x: x[1]["count"], reverse=True
        )

        warnings = []

        for billing_type, data in sorted_types:
            display_name = addon_names.get(billing_type, billing_type)
            count = data["count"]

            if entitlements and billing_type in entitlements:
                licensed = entitlements[billing_type]
                if licensed > 0:
                    pct = (count / licensed) * 100
                    output_lines.append(
                        f"{display_name}: {count} / {licensed} used ({pct:.1f}%)"
                    )
                    if pct >= 100:
                        warnings.append(
                            f"OVER LIMIT: {display_name} at {pct:.1f}% utilization"
                        )
                    elif pct >= 80:
                        warnings.append(
                            f"HIGH USAGE: {display_name} at {pct:.1f}% utilization"
                        )
                else:
                    output_lines.append(f"{display_name}: {count} used (licensed: {licensed})")
            else:
                output_lines.append(f"{display_name}: {count} active")

            # Subtype breakdown
            sorted_subtypes = sorted(
                data["subtypes"].items(), key=lambda x: x[1], reverse=True
            )
            for subtype, sub_count in sorted_subtypes:
                output_lines.append(f"  - {subtype}: {sub_count}")

            output_lines.append("")

        output_lines.append(f"**Total Instances: {total_instances}**")

        if warnings:
            output_lines.append("")
            output_lines.append("---")
            output_lines.append("**Warnings:**")
            for w in warnings:
                output_lines.append(f"- {w}")

        if not entitlements:
            output_lines.append("")
            output_lines.append("---")
            output_lines.append(
                "Note: Configure LICENSE_ENTITLEMENTS in .env to see usage vs. licensed counts."
            )
            output_lines.append(
                "Find your licensed counts at https://support.fortinet.com/ "
                "under Asset Management > Product List."
            )
            output_lines.append(
                "Use the list_addon_catalog tool to see valid addon textkeys."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error getting license utilization: {e}")
        return [
            TextContent(type="text", text=f"Error generating license utilization report: {e}")
        ]
    except Exception as e:
        logger.error(f"Error getting license utilization: {e}")
        return [
            TextContent(type="text", text=f"Error generating license utilization report: {e}")
        ]


async def handle_list_addon_catalog(
    arguments: dict, client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_addon_catalog tool execution."""
    try:
        limit = arguments.get("limit", 100)

        response = client._request("GET", "addon", params={"limit": limit})
        addons = response.get("addon_list", [])
        meta = response.get("meta", {})

        if not addons:
            return [TextContent(type="text", text="No addons found in catalog.")]

        total_count = meta.get("total_count", len(addons))

        output_lines = [
            "**Addon Catalog**\n",
            f"Found {len(addons)} addon(s):\n",
        ]

        for addon in addons:
            name = addon.get("name", "Unknown")
            textkey = addon.get("textkey", "N/A")
            description = addon.get("description", "")

            output_lines.append(f"- **{name}**")
            output_lines.append(f"  Textkey: `{textkey}`")
            if description:
                output_lines.append(f"  Description: {description}")
            output_lines.append("")

        if total_count > len(addons):
            output_lines.append(
                f"\n(Showing {len(addons)} of {total_count} total)"
            )

        output_lines.append("\n---")
        output_lines.append(
            "Use these textkeys in LICENSE_ENTITLEMENTS .env config, e.g.:"
        )
        output_lines.append(
            'LICENSE_ENTITLEMENTS={"instance.basic": 100, "instance.advanced": 50}'
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing addon catalog: {e}")
        return [TextContent(type="text", text=f"Error listing addon catalog: {e}")]
    except Exception as e:
        logger.error(f"Error listing addon catalog: {e}")
        return [TextContent(type="text", text=f"Error listing addon catalog: {e}")]


# ============================================================================
# MODULE EXPORTS (dict pattern)
# ============================================================================

LICENSE_UTILIZATION_TOOL_DEFINITIONS = {
    "get_license_utilization": get_license_utilization_tool_definition,
    "list_addon_catalog": list_addon_catalog_tool_definition,
}

LICENSE_UTILIZATION_HANDLERS = {
    "get_license_utilization": handle_get_license_utilization,
    "list_addon_catalog": handle_list_addon_catalog,
}
