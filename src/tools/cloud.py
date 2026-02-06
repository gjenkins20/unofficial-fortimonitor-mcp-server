"""Cloud provider and credential management tools for FortiMonitor."""

import logging
from typing import List

from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def list_cloud_providers_tool_definition() -> Tool:
    """Return tool definition for listing cloud providers."""
    return Tool(
        name="list_cloud_providers",
        description=(
            "List available cloud providers (AWS, Azure, GCP, etc.) "
            "that can be used for cloud monitoring integration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of providers to return (default 50)"
                }
            }
        }
    )


def get_cloud_provider_details_tool_definition() -> Tool:
    """Return tool definition for getting cloud provider details."""
    return Tool(
        name="get_cloud_provider_details",
        description=(
            "Get detailed information about a specific cloud provider."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "provider_id": {
                    "type": "integer",
                    "description": "ID of the cloud provider"
                }
            },
            "required": ["provider_id"]
        }
    )


def list_cloud_credentials_tool_definition() -> Tool:
    """Return tool definition for listing cloud credentials."""
    return Tool(
        name="list_cloud_credentials",
        description=(
            "List all cloud credentials configured for monitoring. "
            "Credentials are used to authenticate with cloud providers for auto-discovery."
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


def create_cloud_credential_tool_definition() -> Tool:
    """Return tool definition for creating a cloud credential."""
    return Tool(
        name="create_cloud_credential",
        description=(
            "Create a new cloud credential for cloud provider integration. "
            "Used to authenticate with cloud providers for auto-discovery of resources."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the cloud credential"
                },
                "cloud_provider_id": {
                    "type": "integer",
                    "description": "ID of the cloud provider this credential is for"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the credential"
                }
            },
            "required": ["name", "cloud_provider_id"]
        }
    )


def get_cloud_credential_details_tool_definition() -> Tool:
    """Return tool definition for getting cloud credential details."""
    return Tool(
        name="get_cloud_credential_details",
        description=(
            "Get detailed information about a specific cloud credential."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the cloud credential"
                }
            },
            "required": ["credential_id"]
        }
    )


def update_cloud_credential_tool_definition() -> Tool:
    """Return tool definition for updating a cloud credential."""
    return Tool(
        name="update_cloud_credential",
        description=(
            "Update an existing cloud credential's name or description."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the cloud credential to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name for the credential (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the credential (optional)"
                }
            },
            "required": ["credential_id"]
        }
    )


def delete_cloud_credential_tool_definition() -> Tool:
    """Return tool definition for deleting a cloud credential."""
    return Tool(
        name="delete_cloud_credential",
        description=(
            "Delete a cloud credential. "
            "This will stop any associated cloud discovery processes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the cloud credential to delete"
                }
            },
            "required": ["credential_id"]
        }
    )


def run_cloud_discovery_tool_definition() -> Tool:
    """Return tool definition for running cloud discovery."""
    return Tool(
        name="run_cloud_discovery",
        description=(
            "Trigger a cloud discovery run using the specified credential. "
            "This will scan the cloud provider for resources to monitor."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the cloud credential to use for discovery"
                }
            },
            "required": ["credential_id"]
        }
    )


def list_cloud_discoveries_tool_definition() -> Tool:
    """Return tool definition for listing cloud discoveries."""
    return Tool(
        name="list_cloud_discoveries",
        description=(
            "List cloud discovery results for a specific credential. "
            "Shows resources found during cloud discovery runs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the cloud credential"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of discoveries to return (default 50)"
                }
            },
            "required": ["credential_id"]
        }
    )


def get_cloud_discovery_details_tool_definition() -> Tool:
    """Return tool definition for getting cloud discovery details."""
    return Tool(
        name="get_cloud_discovery_details",
        description=(
            "Get detailed information about a specific cloud discovery result."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the cloud credential"
                },
                "discovery_id": {
                    "type": "integer",
                    "description": "ID of the cloud discovery"
                }
            },
            "required": ["credential_id", "discovery_id"]
        }
    )


def update_cloud_discovery_tool_definition() -> Tool:
    """Return tool definition for updating a cloud discovery."""
    return Tool(
        name="update_cloud_discovery",
        description=(
            "Update settings for a specific cloud discovery configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "credential_id": {
                    "type": "integer",
                    "description": "ID of the cloud credential"
                },
                "discovery_id": {
                    "type": "integer",
                    "description": "ID of the cloud discovery to update"
                },
                "name": {
                    "type": "string",
                    "description": "New name (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional)"
                }
            },
            "required": ["credential_id", "discovery_id"]
        }
    )


def list_cloud_regions_tool_definition() -> Tool:
    """Return tool definition for listing cloud regions."""
    return Tool(
        name="list_cloud_regions",
        description=(
            "List available cloud regions across all providers. "
            "Regions represent geographic locations where cloud resources are hosted."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of regions to return (default 50)"
                }
            }
        }
    )


def get_cloud_region_details_tool_definition() -> Tool:
    """Return tool definition for getting cloud region details."""
    return Tool(
        name="get_cloud_region_details",
        description=(
            "Get detailed information about a specific cloud region."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "region_id": {
                    "type": "integer",
                    "description": "ID of the cloud region"
                }
            },
            "required": ["region_id"]
        }
    )


def list_cloud_services_tool_definition() -> Tool:
    """Return tool definition for listing cloud services."""
    return Tool(
        name="list_cloud_services",
        description=(
            "List available cloud services that can be monitored "
            "(e.g., EC2, S3, RDS, Lambda, etc.)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of services to return (default 50)"
                }
            }
        }
    )


def get_cloud_service_details_tool_definition() -> Tool:
    """Return tool definition for getting cloud service details."""
    return Tool(
        name="get_cloud_service_details",
        description=(
            "Get detailed information about a specific cloud service type."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "service_id": {
                    "type": "integer",
                    "description": "ID of the cloud service"
                }
            },
            "required": ["service_id"]
        }
    )


# ============================================================================
# TOOL HANDLERS
# ============================================================================


def _extract_id_from_url(url: str) -> str:
    """Extract the ID from the end of an API URL."""
    if url:
        parts = url.rstrip("/").split("/")
        if parts:
            return parts[-1]
    return "N/A"


def _format_resource(resource: dict, resource_type: str) -> List[str]:
    """Format a single API resource dict into output lines."""
    lines = []
    name = resource.get("name", "Unknown")
    url = resource.get("url", "")
    res_id = _extract_id_from_url(url)

    lines.append(f"\n**{name}** (ID: {res_id})")

    if resource.get("description"):
        lines.append(f"  Description: {resource['description']}")

    return lines


async def handle_list_cloud_providers(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_cloud_providers tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing cloud providers (limit={limit})")

        response = client._request("GET", "cloud_provider", params={"limit": limit})
        providers = response.get("cloud_provider_list", [])
        meta = response.get("meta", {})

        if not providers:
            return [TextContent(type="text", text="No cloud providers found.")]

        total_count = meta.get("total_count", len(providers))

        output_lines = [
            "**Cloud Providers**\n",
            f"Found {len(providers)} provider(s):\n"
        ]

        for provider in providers:
            output_lines.extend(_format_resource(provider, "cloud_provider"))

        if total_count > len(providers):
            output_lines.append(f"\n(Showing {len(providers)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing cloud providers: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing cloud providers")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_cloud_provider_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_cloud_provider_details tool execution."""
    try:
        provider_id = arguments["provider_id"]

        logger.info(f"Getting cloud provider details for {provider_id}")

        response = client._request("GET", f"cloud_provider/{provider_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Cloud Provider: {name}** (ID: {provider_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        # Include any other fields from the response
        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud provider {arguments.get('provider_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting cloud provider details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting cloud provider details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_cloud_credentials(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_cloud_credentials tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing cloud credentials (limit={limit})")

        response = client._request("GET", "cloud_credential", params={"limit": limit})
        credentials = response.get("cloud_credential_list", [])
        meta = response.get("meta", {})

        if not credentials:
            return [TextContent(type="text", text="No cloud credentials found.")]

        total_count = meta.get("total_count", len(credentials))

        output_lines = [
            "**Cloud Credentials**\n",
            f"Found {len(credentials)} credential(s):\n"
        ]

        for cred in credentials:
            name = cred.get("name", "Unknown")
            cred_id = _extract_id_from_url(cred.get("url", ""))
            provider = cred.get("cloud_provider", "N/A")
            provider_id = _extract_id_from_url(provider) if provider else "N/A"

            output_lines.append(f"\n**{name}** (ID: {cred_id})")
            output_lines.append(f"  Cloud Provider ID: {provider_id}")
            if cred.get("description"):
                output_lines.append(f"  Description: {cred['description']}")

        if total_count > len(credentials):
            output_lines.append(f"\n(Showing {len(credentials)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing cloud credentials: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing cloud credentials")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_create_cloud_credential(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle create_cloud_credential tool execution."""
    try:
        name = arguments["name"]
        cloud_provider_id = arguments["cloud_provider_id"]
        description = arguments.get("description")

        logger.info(f"Creating cloud credential: {name}")

        data = {
            "name": name,
            "cloud_provider": f"{client.base_url}/cloud_provider/{cloud_provider_id}"
        }
        if description:
            data["description"] = description

        response = client._request("POST", "cloud_credential", json_data=data)

        output_lines = [
            "**Cloud Credential Created**\n",
            f"Name: {name}",
            f"Cloud Provider ID: {cloud_provider_id}"
        ]

        if description:
            output_lines.append(f"Description: {description}")

        if isinstance(response, dict) and response.get("url"):
            cred_id = _extract_id_from_url(response["url"])
            output_lines.append(f"Credential ID: {cred_id}")
        elif isinstance(response, dict) and response.get("success"):
            output_lines.append(
                "\nCredential created. Use 'list_cloud_credentials' to find the ID."
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error creating cloud credential: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error creating cloud credential")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_cloud_credential_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_cloud_credential_details tool execution."""
    try:
        credential_id = arguments["credential_id"]

        logger.info(f"Getting cloud credential details for {credential_id}")

        response = client._request("GET", f"cloud_credential/{credential_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Cloud Credential: {name}** (ID: {credential_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        provider = response.get("cloud_provider", "")
        if provider:
            output_lines.append(f"Cloud Provider: {_extract_id_from_url(provider)}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri", "cloud_provider") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud credential {arguments.get('credential_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting cloud credential details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting cloud credential details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_cloud_credential(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_cloud_credential tool execution."""
    try:
        credential_id = arguments["credential_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating cloud credential {credential_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request("PUT", f"cloud_credential/{credential_id}", json_data=data)

        output_lines = ["**Cloud Credential Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Credential ID: {credential_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud credential {arguments.get('credential_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating cloud credential: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating cloud credential")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_delete_cloud_credential(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle delete_cloud_credential tool execution."""
    try:
        credential_id = arguments["credential_id"]

        logger.info(f"Deleting cloud credential {credential_id}")

        # Get name before deleting
        try:
            response = client._request("GET", f"cloud_credential/{credential_id}")
            cred_name = response.get("name", f"ID {credential_id}")
        except Exception:
            cred_name = f"ID {credential_id}"

        client._request("DELETE", f"cloud_credential/{credential_id}")

        return [TextContent(
            type="text",
            text=(
                f"**Cloud Credential Deleted**\n\n"
                f"Credential '{cred_name}' (ID: {credential_id}) has been deleted.\n\n"
                f"Note: Any associated cloud discovery processes have been stopped."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud credential {arguments.get('credential_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error deleting cloud credential: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error deleting cloud credential")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_run_cloud_discovery(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle run_cloud_discovery tool execution."""
    try:
        credential_id = arguments["credential_id"]

        logger.info(f"Running cloud discovery for credential {credential_id}")

        # Get credential name for output
        try:
            cred_response = client._request("GET", f"cloud_credential/{credential_id}")
            cred_name = cred_response.get("name", f"ID {credential_id}")
        except Exception:
            cred_name = f"ID {credential_id}"

        client._request("POST", f"cloud_credential/{credential_id}/run")

        return [TextContent(
            type="text",
            text=(
                f"**Cloud Discovery Started**\n\n"
                f"Discovery has been triggered for credential '{cred_name}' "
                f"(ID: {credential_id}).\n\n"
                f"Use 'list_cloud_discoveries' to check the results once the scan completes."
            )
        )]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud credential {arguments.get('credential_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error running cloud discovery: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error running cloud discovery")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_cloud_discoveries(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_cloud_discoveries tool execution."""
    try:
        credential_id = arguments["credential_id"]
        limit = arguments.get("limit", 50)

        logger.info(f"Listing cloud discoveries for credential {credential_id}")

        response = client._request(
            "GET",
            f"cloud_credential/{credential_id}/cloud_discovery",
            params={"limit": limit}
        )
        discoveries = response.get("cloud_discovery_list", [])
        meta = response.get("meta", {})

        if not discoveries:
            return [TextContent(
                type="text",
                text=f"No cloud discoveries found for credential {credential_id}."
            )]

        total_count = meta.get("total_count", len(discoveries))

        output_lines = [
            f"**Cloud Discoveries for Credential {credential_id}**\n",
            f"Found {len(discoveries)} discovery(ies):\n"
        ]

        for disc in discoveries:
            name = disc.get("name", "Unknown")
            disc_id = _extract_id_from_url(disc.get("url", ""))

            output_lines.append(f"\n**{name}** (ID: {disc_id})")
            if disc.get("description"):
                output_lines.append(f"  Description: {disc['description']}")
            if disc.get("status"):
                output_lines.append(f"  Status: {disc['status']}")

        if total_count > len(discoveries):
            output_lines.append(f"\n(Showing {len(discoveries)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud credential {arguments.get('credential_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error listing cloud discoveries: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing cloud discoveries")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_cloud_discovery_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_cloud_discovery_details tool execution."""
    try:
        credential_id = arguments["credential_id"]
        discovery_id = arguments["discovery_id"]

        logger.info(f"Getting cloud discovery {discovery_id} for credential {credential_id}")

        response = client._request(
            "GET",
            f"cloud_credential/{credential_id}/cloud_discovery/{discovery_id}"
        )

        name = response.get("name", "Unknown")
        output_lines = [
            f"**Cloud Discovery: {name}** (ID: {discovery_id})\n",
            f"Credential ID: {credential_id}"
        ]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")
        if response.get("status"):
            output_lines.append(f"Status: {response['status']}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri", "status") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud discovery {arguments.get('discovery_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting cloud discovery details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting cloud discovery details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_update_cloud_discovery(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle update_cloud_discovery tool execution."""
    try:
        credential_id = arguments["credential_id"]
        discovery_id = arguments["discovery_id"]
        name = arguments.get("name")
        description = arguments.get("description")

        if name is None and description is None:
            return [TextContent(
                type="text",
                text="Error: At least one of 'name' or 'description' must be provided."
            )]

        logger.info(f"Updating cloud discovery {discovery_id} for credential {credential_id}")

        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        client._request(
            "PUT",
            f"cloud_credential/{credential_id}/cloud_discovery/{discovery_id}",
            json_data=data
        )

        output_lines = ["**Cloud Discovery Updated**\n"]
        if name:
            output_lines.append(f"Name: {name}")
        if description is not None:
            output_lines.append(f"Description: Updated")
        output_lines.append(f"Discovery ID: {discovery_id}")
        output_lines.append(f"Credential ID: {credential_id}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud discovery {arguments.get('discovery_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error updating cloud discovery: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error updating cloud discovery")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_cloud_regions(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_cloud_regions tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing cloud regions (limit={limit})")

        response = client._request("GET", "cloud_region", params={"limit": limit})
        regions = response.get("cloud_region_list", [])
        meta = response.get("meta", {})

        if not regions:
            return [TextContent(type="text", text="No cloud regions found.")]

        total_count = meta.get("total_count", len(regions))

        output_lines = [
            "**Cloud Regions**\n",
            f"Found {len(regions)} region(s):\n"
        ]

        for region in regions:
            output_lines.extend(_format_resource(region, "cloud_region"))

        if total_count > len(regions):
            output_lines.append(f"\n(Showing {len(regions)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing cloud regions: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing cloud regions")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_cloud_region_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_cloud_region_details tool execution."""
    try:
        region_id = arguments["region_id"]

        logger.info(f"Getting cloud region details for {region_id}")

        response = client._request("GET", f"cloud_region/{region_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Cloud Region: {name}** (ID: {region_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud region {arguments.get('region_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting cloud region details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting cloud region details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_list_cloud_services(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle list_cloud_services tool execution."""
    try:
        limit = arguments.get("limit", 50)

        logger.info(f"Listing cloud services (limit={limit})")

        response = client._request("GET", "cloud_service", params={"limit": limit})
        services = response.get("cloud_service_list", [])
        meta = response.get("meta", {})

        if not services:
            return [TextContent(type="text", text="No cloud services found.")]

        total_count = meta.get("total_count", len(services))

        output_lines = [
            "**Cloud Services**\n",
            f"Found {len(services)} service(s):\n"
        ]

        for svc in services:
            output_lines.extend(_format_resource(svc, "cloud_service"))

        if total_count > len(services):
            output_lines.append(f"\n(Showing {len(services)} of {total_count} total)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error listing cloud services: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error listing cloud services")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_get_cloud_service_details(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_cloud_service_details tool execution."""
    try:
        service_id = arguments["service_id"]

        logger.info(f"Getting cloud service details for {service_id}")

        response = client._request("GET", f"cloud_service/{service_id}")

        name = response.get("name", "Unknown")
        output_lines = [f"**Cloud Service: {name}** (ID: {service_id})\n"]

        if response.get("description"):
            output_lines.append(f"Description: {response['description']}")

        for key, value in response.items():
            if key not in ("name", "description", "url", "resource_uri") and value:
                output_lines.append(f"{key}: {value}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except NotFoundError:
        return [TextContent(
            type="text",
            text=f"Error: Cloud service {arguments.get('service_id')} not found."
        )]
    except APIError as e:
        logger.error(f"API error getting cloud service details: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error getting cloud service details")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


# ============================================================================
# EXPORT DICTS
# ============================================================================

CLOUD_TOOL_DEFINITIONS = {
    "list_cloud_providers": list_cloud_providers_tool_definition,
    "get_cloud_provider_details": get_cloud_provider_details_tool_definition,
    "list_cloud_credentials": list_cloud_credentials_tool_definition,
    "create_cloud_credential": create_cloud_credential_tool_definition,
    "get_cloud_credential_details": get_cloud_credential_details_tool_definition,
    "update_cloud_credential": update_cloud_credential_tool_definition,
    "delete_cloud_credential": delete_cloud_credential_tool_definition,
    "run_cloud_discovery": run_cloud_discovery_tool_definition,
    "list_cloud_discoveries": list_cloud_discoveries_tool_definition,
    "get_cloud_discovery_details": get_cloud_discovery_details_tool_definition,
    "update_cloud_discovery": update_cloud_discovery_tool_definition,
    "list_cloud_regions": list_cloud_regions_tool_definition,
    "get_cloud_region_details": get_cloud_region_details_tool_definition,
    "list_cloud_services": list_cloud_services_tool_definition,
    "get_cloud_service_details": get_cloud_service_details_tool_definition,
}

CLOUD_HANDLERS = {
    "list_cloud_providers": handle_list_cloud_providers,
    "get_cloud_provider_details": handle_get_cloud_provider_details,
    "list_cloud_credentials": handle_list_cloud_credentials,
    "create_cloud_credential": handle_create_cloud_credential,
    "get_cloud_credential_details": handle_get_cloud_credential_details,
    "update_cloud_credential": handle_update_cloud_credential,
    "delete_cloud_credential": handle_delete_cloud_credential,
    "run_cloud_discovery": handle_run_cloud_discovery,
    "list_cloud_discoveries": handle_list_cloud_discoveries,
    "get_cloud_discovery_details": handle_get_cloud_discovery_details,
    "update_cloud_discovery": handle_update_cloud_discovery,
    "list_cloud_regions": handle_list_cloud_regions,
    "get_cloud_region_details": handle_get_cloud_region_details,
    "list_cloud_services": handle_list_cloud_services,
    "get_cloud_service_details": handle_get_cloud_service_details,
}
