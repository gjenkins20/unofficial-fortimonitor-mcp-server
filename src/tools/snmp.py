"""SNMP credential and resource management tools for FortiMonitor."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _extract_id_from_url(url: str) -> str:
    """Extract the ID from the end of an API URL."""
    if url:
        parts = url.rstrip("/").split("/")
        if parts:
            return parts[-1]
    return "N/A"


def _normalize_tags(tags) -> list:
    """Normalize tags from API response to a list of strings.

    The API may return tags as a list of strings or a comma-separated string.
    This function normalizes both formats to a list.
    """
    if tags is None:
        return []
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]
    if isinstance(tags, str):
        return [t.strip() for t in tags.split(",") if t.strip()]
    return []


# Fields that must NEVER be included in SNMP resource PUT payloads.
# Including these causes HTTP 500 errors from the API.
_SNMP_RESOURCE_READONLY_FIELDS = frozenset({
    "template", "template_snmp_resource", "formatted_name",
    "id", "url", "resource_url", "status", "server_url", "thresholds",
})

# Fields that are safe to echo back from GET in a PUT payload when non-null.
_SNMP_RESOURCE_OPTIONAL_WRITABLE_FIELDS = (
    "port", "server_interface", "user",
    "auth_algorithm", "auth_key", "enc_algorithm", "enc_key",
)


def _build_safe_snmp_resource_put_payload(
    current: dict,
    overrides: dict,
    merged_tags: list | None = None,
) -> dict:
    """Build a safe PUT payload for an SNMP resource.

    Starts from the GET response (current), applies overrides from user input,
    and ensures all required fields are present while excluding read-only fields.
    """
    payload = {
        "name": current.get("name", ""),
        "frequency": current.get("frequency", 60),
        "type": current.get("type", "gauge"),
        "base_oid": current.get("base_oid", current.get("oid", "")),
    }

    # version and community are required non-null for template-inherited resources
    payload["version"] = current.get("version") or "2c"
    payload["community"] = current.get("community") or "public"

    # Include optional writable fields if non-null in current state
    for field in _SNMP_RESOURCE_OPTIONAL_WRITABLE_FIELDS:
        val = current.get(field)
        if val is not None:
            payload[field] = val

    # Include tags
    if merged_tags is not None:
        payload["tags"] = merged_tags

    # Apply user overrides (these take precedence)
    for key, value in overrides.items():
        if value is not None:
            payload[key] = value

    return payload


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_snmp_credentials_tool_definition() -> Tool:
    """Return tool definition for listing SNMP credentials."""
    return Tool(
        name="list_snmp_credentials",
        description=(
            "List all SNMP credentials configured in FortiMonitor. "
            "SNMP credentials are used for SNMP-based monitoring of servers and devices."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of credentials to return (default 50)"
                }
            }
        }
    )


def get_snmp_credential_details_tool_definition() -> Tool:
    """Return tool definition for getting SNMP credential details."""
    return Tool(
        name="get_snmp_credential_details",
        description=(
            "Get detailed information about a specific SNMP credential, "
            "including version, community string, and description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the SNMP credential"
                }
            },
            "required": ["credential_id"]
        }
    )


def create_snmp_credential_tool_definition() -> Tool:
    """Return tool definition for creating an SNMP credential."""
    return Tool(
        name="create_snmp_credential",
        description=(
            "Create a new SNMP credential for use with SNMP-based monitoring. "
            "Specify the name, and optionally the community string, version, and description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the SNMP credential"
                },
                "community_string": {
                    "type": "string",
                    "description": "SNMP community string (optional, e.g., 'public')"
                },
                "version": {
                    "type": "string",
                    "description": "SNMP version (optional, e.g., 'v2c', 'v3')"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the credential"
                }
            },
            "required": ["name"]
        }
    )


def update_snmp_credential_tool_definition() -> Tool:
    """Return tool definition for updating an SNMP credential."""
    return Tool(
        name="update_snmp_credential",
        description=(
            "Update an existing SNMP credential. "
            "Can change the name, community string, or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the SNMP credential to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the credential (optional)"
                },
                "community_string": {
                    "type": "string",
                    "description": "New SNMP community string (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the credential (optional)"
                }
            },
            "required": ["credential_id"]
        }
    )


def delete_snmp_credential_tool_definition() -> Tool:
    """Return tool definition for deleting an SNMP credential."""
    return Tool(
        name="delete_snmp_credential",
        description=(
            "Delete an SNMP credential. "
            "Servers using this credential will no longer be able to use it for SNMP monitoring."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the SNMP credential to delete"
                }
            },
            "required": ["credential_id"]
        }
    )


def request_snmp_discovery_tool_definition() -> Tool:
    """Return tool definition for requesting SNMP discovery on a server."""
    return Tool(
        name="request_snmp_discovery",
        description=(
            "Trigger an SNMP discovery scan on a server. "
            "This initiates a scan to automatically discover SNMP-monitorable resources on the server."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server to run SNMP discovery on"
                }
            },
            "required": ["server_id"]
        }
    )


def list_server_snmp_resources_tool_definition() -> Tool:
    """Return tool definition for listing SNMP resources on a server."""
    return Tool(
        name="list_server_snmp_resources",
        description=(
            "List SNMP resources being monitored on a specific server. "
            "Shows OIDs, names, and other SNMP resource details."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of resources to return (default 50)"
                }
            },
            "required": ["server_id"]
        }
    )


def get_snmp_resource_details_tool_definition() -> Tool:
    """Return tool definition for getting SNMP resource details."""
    return Tool(
        name="get_snmp_resource_details",
        description=(
            "Get detailed information about a specific SNMP resource on a server, "
            "including OID, name, current value, and thresholds."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "resource_id": {
                    "type": "integer",
                    "description": "ID of the SNMP resource"
                }
            },
            "required": ["server_id", "resource_id"]
        }
    )


def create_snmp_resource_tool_definition() -> Tool:
    """Return tool definition for creating an SNMP resource on a server."""
    return Tool(
        name="create_snmp_resource",
        description=(
            "Create a new SNMP resource (monitored OID) on a server. "
            "This adds an SNMP-based metric to monitor on the server."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server to add the SNMP resource to"
                },
                "name": {
                    "type": "string",
                    "description": "Name for the SNMP resource (optional)"
                },
                "oid": {
                    "type": "string",
                    "description": "SNMP OID to monitor (optional, e.g., '1.3.6.1.2.1.1.3.0')"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the SNMP resource"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to apply to the new resource (optional)"
                },
                "frequency": {
                    "type": "integer",
                    "description": "Polling frequency in seconds (optional)"
                },
                "type": {
                    "type": "string",
                    "enum": ["gauge", "counter", "gauge_ratio"],
                    "description": "SNMP resource type (optional)"
                },
                "version": {
                    "type": "string",
                    "description": "SNMP version, e.g. '2c' or '3' (optional)"
                },
                "community": {
                    "type": "string",
                    "description": "SNMP community string (optional)"
                }
            },
            "required": ["server_id"]
        }
    )


def update_snmp_resource_tool_definition() -> Tool:
    """Return tool definition for updating an SNMP resource on a server."""
    return Tool(
        name="update_snmp_resource",
        description=(
            "Update an existing SNMP resource on a server. "
            "Uses a pre-flight GET to fetch current state, then constructs a safe PUT payload "
            "that preserves all required fields. Tags are merged (set union) with existing tags — "
            "no duplicates. You can update any combination of fields; the pre-flight GET ensures "
            "all required API fields are always included."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "resource_id": {
                    "type": "integer",
                    "description": "ID of the SNMP resource to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the SNMP resource (optional)"
                },
                "oid": {
                    "type": "string",
                    "description": "New SNMP OID (maps to base_oid in API, optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to apply (merged with existing tags, no duplicates)"
                },
                "frequency": {
                    "type": "integer",
                    "description": "Polling frequency in seconds (optional)"
                },
                "type": {
                    "type": "string",
                    "enum": ["gauge", "counter", "gauge_ratio"],
                    "description": "SNMP resource type (optional)"
                },
                "version": {
                    "type": "string",
                    "description": "SNMP version, e.g. '2c' or '3' (optional)"
                },
                "community": {
                    "type": "string",
                    "description": "SNMP community string (optional)"
                },
                "port": {
                    "type": "integer",
                    "description": "SNMP port number (optional)"
                }
            },
            "required": ["server_id", "resource_id"]
        }
    )


def delete_snmp_resource_tool_definition() -> Tool:
    """Return tool definition for deleting an SNMP resource from a server."""
    return Tool(
        name="delete_snmp_resource",
        description=(
            "Delete an SNMP resource from a server. "
            "This permanently removes the SNMP-based metric and its monitoring data."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "resource_id": {
                    "type": "integer",
                    "description": "ID of the SNMP resource to delete"
                }
            },
            "required": ["server_id", "resource_id"]
        }
    )


def get_snmp_resource_metric_tool_definition() -> Tool:
    """Return tool definition for getting SNMP resource metric data."""
    return Tool(
        name="get_snmp_resource_metric",
        description=(
            "Get time-series metric data for an SNMP resource on a server. "
            "Returns data points for the specified timescale (e.g., hour, day, week, month)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server"
                },
                "resource_id": {
                    "type": "integer",
                    "description": "ID of the SNMP resource"
                },
                "timescale": {
                    "type": "string",
                    "default": "day",
                    "description": "Time scale for data (e.g., 'hour', 'day', 'week', 'month')"
                }
            },
            "required": ["server_id", "resource_id"]
        }
    )


def bulk_tag_snmp_resources_tool_definition() -> Tool:
    """Return tool definition for bulk-tagging SNMP resources on a server."""
    return Tool(
        name="bulk_tag_snmp_resources",
        description=(
            "Apply tags to multiple SNMP resources on a server in one operation. "
            "Uses pre-flight GET + safe PUT for each resource. Tags are merged with "
            "existing tags (set union, no duplicates). Resources that already have all "
            "specified tags are skipped. Maximum 100 resources per call."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "ID of the server containing the SNMP resources"
                },
                "resource_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of SNMP resource IDs to tag (max 100)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to apply to all specified resources"
                }
            },
            "required": ["server_id", "resource_ids", "tags"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


async def handle_list_snmp_credentials(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_snmp_credentials tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing SNMP credentials (limit={limit})")

        response = client._request("GET", "snmp_credential", params={"limit": limit})
        credentials = response.get("snmp_credential_list", [])
        meta = response.get("meta", {})

        if not credentials:
            return [TextContent(type="text", text="No SNMP credentials found.")]

        total_count = meta.get("total_count", len(credentials))

        output_lines = [
            "**SNMP Credentials**\n",
            f"Found {len(credentials)} credential(s):\n"
        ]

        for cred in credentials:
            name = cred.get("name", "Unknown")
            cred_id = _extract_id_from_url(cred.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {cred_id})")
            if cred.get("version"):
                output_lines.append(f"  Version: {cred['version']}")
            if cred.get("community_string"):
                output_lines.append(f"  Community String: {cred['community_string']}")
            if cred.get("description"):
                output_lines.append(f"  Description: {cred['description']}")

        if total_count > len(credentials):
            output_lines.append(f"\n(Showing {len(credentials)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing SNMP credentials: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing SNMP credentials")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_snmp_credential_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_snmp_credential_details tool execution."""
    try:
        credential_id = arguments["credential_id"]

        logger.info(f"Getting SNMP credential details for {credential_id}")

        response = client._request("GET", f"snmp_credential/{credential_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**SNMP Credential: {name}** (ID: {credential_id})\n"]

        if response.get("version"):
            output_lines.append(f"Version: {response['version']}")
        if response.get("community_string"):
            output_lines.append(f"Community String: {response['community_string']}")
        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "version", "community_string", "description",
                          "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: SNMP credential {arguments.get('credential_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting SNMP credential details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting SNMP credential details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_snmp_credential(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_snmp_credential tool execution."""
    try:
        name = arguments["name"]
        community_string = arguments.get("community_string")
        version = arguments.get("version")
        description = arguments.get("description")

        logger.info(f"Creating SNMP credential: {name}")

        data = {"name": name}
        if community_string:
            data["community_string"] = community_string
        if version:
            data["version"] = version
        if description:
            data["description"] = description

        response = client._request("POST", "snmp_credential", json_data=data)

        output_lines = [
            "**SNMP Credential Created**\n",
            f"Name: {name}"
        ]

        if community_string:
            output_lines.append(f"Community String: {community_string}")
        if version:
            output_lines.append(f"Version: {version}")
        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            cred_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Credential ID: {cred_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nCredential created. Use 'list_snmp_credentials' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating SNMP credential: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating SNMP credential")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_snmp_credential(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_snmp_credential tool execution."""
    try:
        credential_id = arguments["credential_id"]
        name = arguments.get("name")
        community_string = arguments.get("community_string")
        description = arguments.get("description")

        if name is None and community_string is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name', 'community_string', or 'description' must be provided."
            )]

        logger.info(f"Updating SNMP credential {credential_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if community_string is not None:
            data["community_string"] = community_string
        if description is not None:
            data["description"] = description

        client._request("PUT", f"snmp_credential/{credential_id}", json_data=data)

        output_lines = ["**SNMP Credential Updated**\n"]
        output_lines.append(f"Credential ID: {credential_id}")
        if name:
            output_lines.append(f"Name: {name}")
        if community_string is not None:
            output_lines.append(f"Community String: Updated")
        if description is not None:
            output_lines.append(f"Description: Updated")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: SNMP credential {arguments.get('credential_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating SNMP credential: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating SNMP credential")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_snmp_credential(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_snmp_credential tool execution."""
    try:
        credential_id = arguments["credential_id"]

        logger.info(f"Deleting SNMP credential {credential_id}")

        # Get name before deleting
        try:
            response = client._request("GET", f"snmp_credential/{credential_id}")
            cred_name = response.get("name", f"ID {credential_id}")
        except Exception:
            cred_name = f"ID {credential_id}"

        client._request("DELETE", f"snmp_credential/{credential_id}")

        return [TextContent(
            type="text",
            text=(
                f"**SNMP Credential Deleted**\n\n"
                f"Credential '{cred_name}' (ID: {credential_id}) has been deleted.\n\n"
                f"Note: Servers using this credential will no longer be able to use it "
                f"for SNMP monitoring."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: SNMP credential {arguments.get('credential_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting SNMP credential: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting SNMP credential")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_request_snmp_discovery(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle request_snmp_discovery tool execution."""
    try:
        server_id = arguments["server_id"]

        logger.info(f"Requesting SNMP discovery for server {server_id}")

        # Get server name for output
        try:
            server_response = client._request("GET", f"server/{server_id}")
            server_name = server_response.get("name", f"ID {server_id}")
        except Exception:
            server_name = f"ID {server_id}"

        client._request("PUT", f"server/{server_id}/snmp_discovery")

        return [TextContent(
            type="text",
            text=(
                f"**SNMP Discovery Requested**\n\n"
                f"SNMP discovery scan has been triggered for server '{server_name}' "
                f"(ID: {server_id}).\n\n"
                f"Use 'list_server_snmp_resources' to check discovered resources "
                f"once the scan completes."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error requesting SNMP discovery: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error requesting SNMP discovery")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_server_snmp_resources(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_server_snmp_resources tool execution."""
    try:
        server_id = arguments["server_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing SNMP resources for server {server_id} (limit={limit})")

        response = client._request(
            "GET",
            f"server/{server_id}/snmp_resource",
            params={"limit": limit}
        )
        resources = response.get("snmp_resource_list", [])
        meta = response.get("meta", {})

        if not resources:
            return [TextContent(
                type="text",
                text=f"No SNMP resources found for server {server_id}."
            )]

        total_count = meta.get("total_count", len(resources))

        output_lines = [
            f"**SNMP Resources for Server {server_id}**\n",
            f"Found {len(resources)} resource(s):\n"
        ]

        for res in resources:
            name = res.get("name", res.get("display_name", "Unknown"))
            res_id = _extract_id_from_url(res.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {res_id})")
            if res.get("oid"):
                output_lines.append(f"  OID: {res['oid']}")
            if res.get("description"):
                output_lines.append(f"  Description: {res['description']}")
            if res.get("value") is not None:
                output_lines.append(f"  Current Value: {res['value']}")
            if res.get("status"):
                output_lines.append(f"  Status: {res['status']}")
            tags = _normalize_tags(res.get("tags"))
            if tags:
                output_lines.append(f"  Tags: {', '.join(tags)}")

        if total_count > len(resources):
            output_lines.append(f"\n(Showing {len(resources)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing SNMP resources: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing SNMP resources")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_snmp_resource_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_snmp_resource_details tool execution."""
    try:
        server_id = arguments["server_id"]
        resource_id = arguments["resource_id"]

        logger.info(
            f"Getting SNMP resource {resource_id} details for server {server_id}"
        )

        response = client._request(
            "GET", f"server/{server_id}/snmp_resource/{resource_id}"
        )

        name = response.get("name", response.get("display_name", "Unknown"))
        output_lines = [
            f"**SNMP Resource: {name}** (ID: {resource_id})\n",
            f"Server ID: {server_id}"
        ]

        if response.get("oid"):
            output_lines.append(f"OID: {response['oid']}")
        if response.get("base_oid"):
            output_lines.append(f"Base OID: {response['base_oid']}")
        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("value") is not None:
            output_lines.append(f"Current Value: {response['value']}")
        if response.get("status"):
            output_lines.append(f"Status: {response['status']}")

        # Normalize and display tags
        tags = _normalize_tags(response.get("tags"))
        output_lines.append(f"Tags: {', '.join(tags) if tags else '(none)'}")

        # Display other fields
        _displayed = {
            "name", "display_name", "oid", "base_oid", "description",
            "value", "status", "url", "resource_uri", "tags",
        }
        for key, value in response.items():
            if key not in _displayed and value:
                output_lines.append(f"{key}: {value}")

        # Field writability reference
        output_lines.append("\n---")
        output_lines.append("**Writable Fields:** name, frequency, type, base_oid, "
                            "version, community, tags, port, description, "
                            "server_interface, user, auth_algorithm, auth_key, "
                            "enc_algorithm, enc_key")
        output_lines.append("**Read-Only Fields:** formatted_name, template, "
                            "template_snmp_resource, id, url, status, "
                            "server_url, thresholds")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: SNMP resource {arguments.get('resource_id')} not found "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error getting SNMP resource details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting SNMP resource details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_snmp_resource(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_snmp_resource tool execution."""
    try:
        server_id = arguments["server_id"]
        name = arguments.get("name")
        oid = arguments.get("oid")
        description = arguments.get("description")
        tags = arguments.get("tags")
        frequency = arguments.get("frequency")
        res_type = arguments.get("type")
        version = arguments.get("version")
        community = arguments.get("community")

        logger.info(f"Creating SNMP resource on server {server_id}")

        data = {}
        if name:
            data["name"] = name
        if oid:
            data["oid"] = oid
        if description:
            data["description"] = description
        if tags:
            data["tags"] = tags
        if frequency is not None:
            data["frequency"] = frequency
        if res_type:
            data["type"] = res_type
        if version:
            data["version"] = version
        if community:
            data["community"] = community

        response = client._request(
            "POST",
            f"server/{server_id}/snmp_resource",
            json_data=data
        )

        output_lines = [
            "**SNMP Resource Created**\n",
            f"Server ID: {server_id}"
        ]

        if name:
            output_lines.append(f"Name: {name}")
        if oid:
            output_lines.append(f"OID: {oid}")
        if description:
            output_lines.append(f"Description: {description}")
        if tags:
            output_lines.append(f"Tags: {', '.join(tags)}")
        if frequency is not None:
            output_lines.append(f"Frequency: {frequency}s")
        if res_type:
            output_lines.append(f"Type: {res_type}")

        if isinstance(response, dict) and response.get("url"):
            res_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Resource ID: {res_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Server {arguments.get('server_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error creating SNMP resource: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating SNMP resource")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_snmp_resource(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_snmp_resource tool execution.

    Uses a pre-flight GET to fetch current state, merges tags, and constructs
    a safe PUT payload that avoids API 500 errors from missing required fields
    or read-only field inclusion.
    """
    try:
        server_id = arguments["server_id"]
        resource_id = arguments["resource_id"]

        logger.info(
            f"Updating SNMP resource {resource_id} on server {server_id}"
        )

        # Pre-flight GET: fetch current resource state
        endpoint = f"server/{server_id}/snmp_resource/{resource_id}"
        current = client._request("GET", endpoint)

        # Merge tags (set union, no duplicates)
        new_tags = arguments.get("tags")
        existing_tags = _normalize_tags(current.get("tags"))
        if new_tags is not None:
            merged_tags = list(dict.fromkeys(existing_tags + new_tags))
        else:
            merged_tags = existing_tags if existing_tags else None

        # Build user overrides (only fields the user explicitly provided)
        overrides = {}
        if arguments.get("name") is not None:
            overrides["name"] = arguments["name"]
        if arguments.get("oid") is not None:
            overrides["base_oid"] = arguments["oid"]
        if arguments.get("frequency") is not None:
            overrides["frequency"] = arguments["frequency"]
        if arguments.get("type") is not None:
            overrides["type"] = arguments["type"]
        if arguments.get("version") is not None:
            overrides["version"] = arguments["version"]
        if arguments.get("community") is not None:
            overrides["community"] = arguments["community"]
        if arguments.get("port") is not None:
            overrides["port"] = arguments["port"]
        if arguments.get("description") is not None:
            overrides["description"] = arguments["description"]

        # Build safe PUT payload
        data = _build_safe_snmp_resource_put_payload(
            current, overrides, merged_tags
        )

        client._request("PUT", endpoint, json_data=data)

        output_lines = ["**SNMP Resource Updated**\n"]
        output_lines.append(f"Server ID: {server_id}")
        output_lines.append(f"Resource ID: {resource_id}")
        if arguments.get("name") is not None:
            output_lines.append(f"Name: {arguments['name']}")
        if arguments.get("oid") is not None:
            output_lines.append(f"OID: {arguments['oid']}")
        if arguments.get("description") is not None:
            output_lines.append(f"Description: Updated")
        if new_tags is not None:
            output_lines.append(f"Tags: {', '.join(merged_tags or [])}")
        if arguments.get("frequency") is not None:
            output_lines.append(f"Frequency: {arguments['frequency']}s")
        if arguments.get("type") is not None:
            output_lines.append(f"Type: {arguments['type']}")
        if arguments.get("version") is not None:
            output_lines.append(f"Version: {arguments['version']}")
        if arguments.get("community") is not None:
            output_lines.append(f"Community: Updated")
        if arguments.get("port") is not None:
            output_lines.append(f"Port: {arguments['port']}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: SNMP resource {arguments.get('resource_id')} not found "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error updating SNMP resource: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating SNMP resource")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_snmp_resource(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_snmp_resource tool execution."""
    try:
        server_id = arguments["server_id"]
        resource_id = arguments["resource_id"]

        logger.info(
            f"Deleting SNMP resource {resource_id} from server {server_id}"
        )

        client._request(
            "DELETE", f"server/{server_id}/snmp_resource/{resource_id}"
        )

        return [TextContent(
            type="text",
            text=(
                f"**SNMP Resource Deleted**\n\n"
                f"SNMP resource {resource_id} has been removed from server {server_id}.\n\n"
                f"Note: Historical monitoring data for this resource has been removed."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: SNMP resource {arguments.get('resource_id')} not found "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error deleting SNMP resource: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting SNMP resource")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_snmp_resource_metric(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_snmp_resource_metric tool execution."""
    try:
        server_id = arguments["server_id"]
        resource_id = arguments["resource_id"]
        timescale = arguments.get("timescale", "day")

        logger.info(
            f"Getting metric for SNMP resource {resource_id} "
            f"on server {server_id} (timescale={timescale})"
        )

        response = client._request(
            "GET",
            f"server/{server_id}/snmp_resource/{resource_id}/metric/{timescale}"
        )

        output_lines = [
            f"**SNMP Resource Metric: Resource {resource_id} on Server {server_id}**\n",
            f"Timescale: {timescale}\n"
        ]

        if isinstance(response, dict):
            data_points = response.get(
                "data", response.get("metric_list", [])
            )
            if isinstance(data_points, list) and data_points:
                output_lines.append(f"Data Points: {len(data_points)}\n")
                for point in data_points[:20]:
                    if isinstance(point, dict):
                        time_val = point.get(
                            "time", point.get("timestamp", "")
                        )
                        value = point.get(
                            "value", point.get("metric", "")
                        )
                        output_lines.append(f"  {time_val}: {value}")
                if len(data_points) > 20:
                    output_lines.append(
                        f"  ... and {len(data_points) - 20} more data points"
                    )
            else:
                # Fallback: dump other fields from the response
                for key, value in response.items():
                    if key not in ("url", "resource_uri", "success",
                                  "status_code") and value:
                        output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=(
                f"Error: SNMP resource {arguments.get('resource_id')} not found "
                f"on server {arguments.get('server_id')}."
            )
        )]
    except APIError as e:
        logger.error(f"API error getting SNMP resource metric: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting SNMP resource metric")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_bulk_tag_snmp_resources(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle bulk_tag_snmp_resources tool execution.

    Applies tags to multiple SNMP resources using the safe PUT payload pattern.
    Skips resources that already have all specified tags (idempotent).
    """
    try:
        server_id = arguments["server_id"]
        resource_ids = arguments["resource_ids"]
        new_tags = arguments["tags"]

        if len(resource_ids) > 100:
            return [TextContent(
                type="text",
                text="Error: Maximum 100 resources per call. Please split into smaller batches."
            )]

        if not new_tags:
            return [TextContent(
                type="text",
                text="Error: At least one tag must be provided."
            )]

        logger.info(
            f"Bulk tagging {len(resource_ids)} SNMP resources on server {server_id} "
            f"with tags: {new_tags}"
        )

        succeeded = []
        skipped = []
        failed = []

        for resource_id in resource_ids:
            try:
                endpoint = f"server/{server_id}/snmp_resource/{resource_id}"

                # Pre-flight GET
                current = client._request("GET", endpoint)

                # Merge tags
                existing_tags = _normalize_tags(current.get("tags"))
                new_tag_set = set(new_tags)
                if new_tag_set.issubset(set(existing_tags)):
                    skipped.append(resource_id)
                    continue

                merged_tags = list(dict.fromkeys(existing_tags + new_tags))

                # Build safe PUT payload (no user overrides, just tag merge)
                data = _build_safe_snmp_resource_put_payload(
                    current, {}, merged_tags
                )

                client._request("PUT", endpoint, json_data=data)
                succeeded.append(resource_id)

            except (APIError, NotFoundError) as e:
                logger.warning(
                    f"Failed to tag SNMP resource {resource_id}: {e}"
                )
                failed.append((resource_id, str(e)))
            except Exception as e:
                logger.warning(
                    f"Unexpected error tagging SNMP resource {resource_id}: {e}"
                )
                failed.append((resource_id, str(e)))

        output_lines = [
            f"**Bulk Tag SNMP Resources — Server {server_id}**\n",
            f"Tags applied: {', '.join(new_tags)}",
            f"Total requested: {len(resource_ids)}",
            f"Succeeded: {len(succeeded)}",
            f"Skipped (already tagged): {len(skipped)}",
            f"Failed: {len(failed)}",
        ]

        if failed:
            output_lines.append("\nFailures:")
            for res_id, err in failed:
                output_lines.append(f"  Resource {res_id}: {err}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error in bulk tag operation: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in bulk tag operation")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

SNMP_TOOL_DEFINITIONS = {
    "list_snmp_credentials": list_snmp_credentials_tool_definition,
    "get_snmp_credential_details": get_snmp_credential_details_tool_definition,
    "create_snmp_credential": create_snmp_credential_tool_definition,
    "update_snmp_credential": update_snmp_credential_tool_definition,
    "delete_snmp_credential": delete_snmp_credential_tool_definition,
    "request_snmp_discovery": request_snmp_discovery_tool_definition,
    "list_server_snmp_resources": list_server_snmp_resources_tool_definition,
    "get_snmp_resource_details": get_snmp_resource_details_tool_definition,
    "create_snmp_resource": create_snmp_resource_tool_definition,
    "update_snmp_resource": update_snmp_resource_tool_definition,
    "delete_snmp_resource": delete_snmp_resource_tool_definition,
    "get_snmp_resource_metric": get_snmp_resource_metric_tool_definition,
    "bulk_tag_snmp_resources": bulk_tag_snmp_resources_tool_definition,
}

SNMP_HANDLERS = {
    "list_snmp_credentials": handle_list_snmp_credentials,
    "get_snmp_credential_details": handle_get_snmp_credential_details,
    "create_snmp_credential": handle_create_snmp_credential,
    "update_snmp_credential": handle_update_snmp_credential,
    "delete_snmp_credential": handle_delete_snmp_credential,
    "request_snmp_discovery": handle_request_snmp_discovery,
    "list_server_snmp_resources": handle_list_server_snmp_resources,
    "get_snmp_resource_details": handle_get_snmp_resource_details,
    "create_snmp_resource": handle_create_snmp_resource,
    "update_snmp_resource": handle_update_snmp_resource,
    "delete_snmp_resource": handle_delete_snmp_resource,
    "get_snmp_resource_metric": handle_get_snmp_resource_metric,
    "bulk_tag_snmp_resources": handle_bulk_tag_snmp_resources,
}
