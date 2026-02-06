"""Main MCP server implementation for FortiMonitor."""

import logging
import asyncio
from typing import Any, List

from mcp.server.models import InitializationOptions
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, ServerCapabilities, ToolsCapability

from .config import get_settings
from .fortimonitor.client import FortiMonitorClient

# Phase 1 tools
from .tools.servers import (
    get_servers_tool_definition,
    handle_get_servers,
    get_server_details_tool_definition,
    handle_get_server_details,
)
from .tools.outages import (
    get_outages_tool_definition,
    handle_get_outages,
    check_server_health_tool_definition,
    handle_check_server_health,
)
from .tools.metrics import (
    get_server_metrics_tool_definition,
    handle_get_server_metrics,
)
from .tools.outage_management import (
    acknowledge_outage_tool_definition,
    handle_acknowledge_outage,
    add_outage_note_tool_definition,
    handle_add_outage_note,
    get_outage_details_tool_definition,
    handle_get_outage_details,
)
from .tools.server_management import (
    set_server_status_tool_definition,
    handle_set_server_status,
    create_maintenance_window_tool_definition,
    handle_create_maintenance_window,
    list_maintenance_windows_tool_definition,
    handle_list_maintenance_windows,
)
from .tools.bulk_operations import (
    bulk_acknowledge_outages_tool_definition,
    handle_bulk_acknowledge_outages,
    bulk_add_tags_tool_definition,
    handle_bulk_add_tags,
    bulk_remove_tags_tool_definition,
    handle_bulk_remove_tags,
    search_servers_advanced_tool_definition,
    handle_search_servers_advanced,
    get_servers_with_active_outages_tool_definition,
    handle_get_servers_with_active_outages,
)
from .tools.server_groups import (
    list_server_groups_tool_definition,
    handle_list_server_groups,
    get_server_group_details_tool_definition,
    handle_get_server_group_details,
    create_server_group_tool_definition,
    handle_create_server_group,
    add_servers_to_group_tool_definition,
    handle_add_servers_to_group,
    remove_servers_from_group_tool_definition,
    handle_remove_servers_from_group,
    delete_server_group_tool_definition,
    handle_delete_server_group,
    update_server_group_tool_definition,
    handle_update_server_group,
    get_server_network_services_tool_definition,
    handle_get_server_network_services,
)
from .tools.templates import (
    list_server_templates_tool_definition,
    handle_list_server_templates,
    get_server_template_details_tool_definition,
    handle_get_server_template_details,
    apply_template_to_server_tool_definition,
    handle_apply_template_to_server,
    apply_template_to_group_tool_definition,
    handle_apply_template_to_group,
)
from .tools.notifications import (
    list_notification_schedules_tool_definition,
    handle_list_notification_schedules,
    get_notification_schedule_details_tool_definition,
    handle_get_notification_schedule_details,
    list_contact_groups_tool_definition,
    handle_list_contact_groups,
    get_contact_group_details_tool_definition,
    handle_get_contact_group_details,
    list_contacts_tool_definition,
    handle_list_contacts,
)
from .tools.agent_resources import (
    list_agent_resource_types_tool_definition,
    handle_list_agent_resource_types,
    get_agent_resource_type_details_tool_definition,
    handle_get_agent_resource_type_details,
    list_server_resources_tool_definition,
    handle_list_server_resources,
    get_resource_details_tool_definition,
    handle_get_resource_details,
)
from .tools.reporting import (
    get_system_health_summary_tool_definition,
    handle_get_system_health_summary,
    get_outage_statistics_tool_definition,
    handle_get_outage_statistics,
    get_server_statistics_tool_definition,
    handle_get_server_statistics,
    get_top_alerting_servers_tool_definition,
    handle_get_top_alerting_servers,
    export_servers_list_tool_definition,
    handle_export_servers_list,
    export_outage_history_tool_definition,
    handle_export_outage_history,
    generate_availability_report_tool_definition,
    handle_generate_availability_report,
)

# Enhanced P1 tools
from .tools.outage_enhanced import (
    OUTAGE_ENHANCED_TOOL_DEFINITIONS,
    OUTAGE_ENHANCED_HANDLERS,
)
from .tools.maintenance_enhanced import (
    MAINTENANCE_ENHANCED_TOOL_DEFINITIONS,
    MAINTENANCE_ENHANCED_HANDLERS,
)
from .tools.server_enhanced import (
    SERVER_ENHANCED_TOOL_DEFINITIONS,
    SERVER_ENHANCED_HANDLERS,
)
from .tools.server_groups_enhanced import (
    SERVER_GROUPS_ENHANCED_TOOL_DEFINITIONS,
    SERVER_GROUPS_ENHANCED_HANDLERS,
)
from .tools.templates_enhanced import (
    TEMPLATES_ENHANCED_TOOL_DEFINITIONS,
    TEMPLATES_ENHANCED_HANDLERS,
)

# P2 tools
from .tools.cloud import (
    CLOUD_TOOL_DEFINITIONS,
    CLOUD_HANDLERS,
)
from .tools.dem import (
    DEM_TOOL_DEFINITIONS,
    DEM_HANDLERS,
)
from .tools.compound_services import (
    COMPOUND_SERVICES_TOOL_DEFINITIONS,
    COMPOUND_SERVICES_HANDLERS,
)

# P3 tools
from .tools.dashboards import (
    DASHBOARDS_TOOL_DEFINITIONS,
    DASHBOARDS_HANDLERS,
)
from .tools.status_pages import (
    STATUS_PAGES_TOOL_DEFINITIONS,
    STATUS_PAGES_HANDLERS,
)
from .tools.rotating_contacts import (
    ROTATING_CONTACTS_TOOL_DEFINITIONS,
    ROTATING_CONTACTS_HANDLERS,
)
from .tools.contacts_enhanced import (
    CONTACTS_ENHANCED_TOOL_DEFINITIONS,
    CONTACTS_ENHANCED_HANDLERS,
)
from .tools.notifications_enhanced import (
    NOTIFICATIONS_ENHANCED_TOOL_DEFINITIONS,
    NOTIFICATIONS_ENHANCED_HANDLERS,
)
from .tools.network_services import (
    NETWORK_SERVICES_TOOL_DEFINITIONS,
    NETWORK_SERVICES_HANDLERS,
)
from .tools.monitoring_nodes import (
    MONITORING_NODES_TOOL_DEFINITIONS,
    MONITORING_NODES_HANDLERS,
)
from .tools.network_service_types import (
    NETWORK_SERVICE_TYPES_TOOL_DEFINITIONS,
    NETWORK_SERVICE_TYPES_HANDLERS,
)
from .tools.snmp import (
    SNMP_TOOL_DEFINITIONS,
    SNMP_HANDLERS,
)
from .tools.fabric import (
    FABRIC_TOOL_DEFINITIONS,
    FABRIC_HANDLERS,
)
from .tools.countermeasures import (
    COUNTERMEASURES_TOOL_DEFINITIONS,
    COUNTERMEASURES_HANDLERS,
)

# P4 tools
from .tools.users import (
    USERS_TOOL_DEFINITIONS,
    USERS_HANDLERS,
)
from .tools.reference_data import (
    REFERENCE_DATA_TOOL_DEFINITIONS,
    REFERENCE_DATA_HANDLERS,
)
from .tools.onsight import (
    ONSIGHT_TOOL_DEFINITIONS,
    ONSIGHT_HANDLERS,
)

# Get settings
_settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, _settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Tool Registry - maps tool name -> (definition_func, handler_func)
# ============================================================================

# Original tools registry (definition_func, handler_func)
_ORIGINAL_TOOLS = [
    # Phase 1 tools
    (get_servers_tool_definition, handle_get_servers),
    (get_server_details_tool_definition, handle_get_server_details),
    (get_outages_tool_definition, handle_get_outages),
    (get_server_metrics_tool_definition, handle_get_server_metrics),
    (check_server_health_tool_definition, handle_check_server_health),
    # Phase 2 Priority 1 tools
    (acknowledge_outage_tool_definition, handle_acknowledge_outage),
    (add_outage_note_tool_definition, handle_add_outage_note),
    (get_outage_details_tool_definition, handle_get_outage_details),
    (set_server_status_tool_definition, handle_set_server_status),
    (create_maintenance_window_tool_definition, handle_create_maintenance_window),
    (list_maintenance_windows_tool_definition, handle_list_maintenance_windows),
    # Phase 2 Priority 2 tools
    (bulk_acknowledge_outages_tool_definition, handle_bulk_acknowledge_outages),
    (bulk_add_tags_tool_definition, handle_bulk_add_tags),
    (bulk_remove_tags_tool_definition, handle_bulk_remove_tags),
    (search_servers_advanced_tool_definition, handle_search_servers_advanced),
    (get_servers_with_active_outages_tool_definition, handle_get_servers_with_active_outages),
    # Phase 2 Priority 3 tools - Server Groups
    (list_server_groups_tool_definition, handle_list_server_groups),
    (get_server_group_details_tool_definition, handle_get_server_group_details),
    (create_server_group_tool_definition, handle_create_server_group),
    (add_servers_to_group_tool_definition, handle_add_servers_to_group),
    (remove_servers_from_group_tool_definition, handle_remove_servers_from_group),
    (delete_server_group_tool_definition, handle_delete_server_group),
    (update_server_group_tool_definition, handle_update_server_group),
    (get_server_network_services_tool_definition, handle_get_server_network_services),
    # Phase 2 Priority 3 tools - Templates
    (list_server_templates_tool_definition, handle_list_server_templates),
    (get_server_template_details_tool_definition, handle_get_server_template_details),
    (apply_template_to_server_tool_definition, handle_apply_template_to_server),
    (apply_template_to_group_tool_definition, handle_apply_template_to_group),
    # Phase 2 Priority 4 tools - Notifications
    (list_notification_schedules_tool_definition, handle_list_notification_schedules),
    (get_notification_schedule_details_tool_definition, handle_get_notification_schedule_details),
    (list_contact_groups_tool_definition, handle_list_contact_groups),
    (get_contact_group_details_tool_definition, handle_get_contact_group_details),
    (list_contacts_tool_definition, handle_list_contacts),
    # Phase 2 Priority 4 tools - Agent Resources
    (list_agent_resource_types_tool_definition, handle_list_agent_resource_types),
    (get_agent_resource_type_details_tool_definition, handle_get_agent_resource_type_details),
    (list_server_resources_tool_definition, handle_list_server_resources),
    (get_resource_details_tool_definition, handle_get_resource_details),
    # Phase 2 Priority 5 tools - Reporting & Analytics
    (get_system_health_summary_tool_definition, handle_get_system_health_summary),
    (get_outage_statistics_tool_definition, handle_get_outage_statistics),
    (get_server_statistics_tool_definition, handle_get_server_statistics),
    (get_top_alerting_servers_tool_definition, handle_get_top_alerting_servers),
    (export_servers_list_tool_definition, handle_export_servers_list),
    (export_outage_history_tool_definition, handle_export_outage_history),
    (generate_availability_report_tool_definition, handle_generate_availability_report),
]


def _build_registry():
    """Build the complete tool registry from all sources."""
    tool_definitions = []
    handler_map = {}

    # Register original tools
    for defn_func, handler_func in _ORIGINAL_TOOLS:
        tool = defn_func()
        tool_definitions.append(tool)
        handler_map[tool.name] = handler_func

    # Register enhanced P1 tools (dict-based modules)
    for defn_dict, handler_dict in [
        (OUTAGE_ENHANCED_TOOL_DEFINITIONS, OUTAGE_ENHANCED_HANDLERS),
        (MAINTENANCE_ENHANCED_TOOL_DEFINITIONS, MAINTENANCE_ENHANCED_HANDLERS),
        (SERVER_ENHANCED_TOOL_DEFINITIONS, SERVER_ENHANCED_HANDLERS),
        (SERVER_GROUPS_ENHANCED_TOOL_DEFINITIONS, SERVER_GROUPS_ENHANCED_HANDLERS),
        (TEMPLATES_ENHANCED_TOOL_DEFINITIONS, TEMPLATES_ENHANCED_HANDLERS),
        (CLOUD_TOOL_DEFINITIONS, CLOUD_HANDLERS),
        (DEM_TOOL_DEFINITIONS, DEM_HANDLERS),
        (COMPOUND_SERVICES_TOOL_DEFINITIONS, COMPOUND_SERVICES_HANDLERS),
        # P3 tools
        (DASHBOARDS_TOOL_DEFINITIONS, DASHBOARDS_HANDLERS),
        (STATUS_PAGES_TOOL_DEFINITIONS, STATUS_PAGES_HANDLERS),
        (ROTATING_CONTACTS_TOOL_DEFINITIONS, ROTATING_CONTACTS_HANDLERS),
        (CONTACTS_ENHANCED_TOOL_DEFINITIONS, CONTACTS_ENHANCED_HANDLERS),
        (NOTIFICATIONS_ENHANCED_TOOL_DEFINITIONS, NOTIFICATIONS_ENHANCED_HANDLERS),
        (NETWORK_SERVICES_TOOL_DEFINITIONS, NETWORK_SERVICES_HANDLERS),
        (MONITORING_NODES_TOOL_DEFINITIONS, MONITORING_NODES_HANDLERS),
        (NETWORK_SERVICE_TYPES_TOOL_DEFINITIONS, NETWORK_SERVICE_TYPES_HANDLERS),
        (SNMP_TOOL_DEFINITIONS, SNMP_HANDLERS),
        (FABRIC_TOOL_DEFINITIONS, FABRIC_HANDLERS),
        (COUNTERMEASURES_TOOL_DEFINITIONS, COUNTERMEASURES_HANDLERS),
        # P4 tools
        (USERS_TOOL_DEFINITIONS, USERS_HANDLERS),
        (REFERENCE_DATA_TOOL_DEFINITIONS, REFERENCE_DATA_HANDLERS),
        (ONSIGHT_TOOL_DEFINITIONS, ONSIGHT_HANDLERS),
    ]:
        for name, defn_func in defn_dict.items():
            tool = defn_func()
            tool_definitions.append(tool)
            handler_map[name] = handler_dict[name]

    return tool_definitions, handler_map


# Build at module level for fast access
_TOOL_DEFINITIONS, _HANDLER_MAP = _build_registry()


class FortiMonitorMCPServer:
    """MCP Server for FortiMonitor integration."""

    def __init__(self):
        """Initialize the FortiMonitor MCP server."""
        self.server = Server(_settings.mcp_server_name)
        self.client: FortiMonitorClient = None
        self._setup_handlers()

        logger.info(
            f"Initialized {_settings.mcp_server_name} v{_settings.mcp_server_version} "
            f"with {len(_TOOL_DEFINITIONS)} tools"
        )

    def _setup_handlers(self):
        """Set up MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return _TOOL_DEFINITIONS

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """Handle tool execution requests."""
            logger.info(f"Tool called: {name}")

            # Ensure client is initialized
            if not self.client:
                self.client = FortiMonitorClient()

            # Dispatch to handler
            handler = _HANDLER_MAP.get(name)
            if handler:
                return await handler(arguments, self.client)

            raise ValueError(f"Unknown tool: {name}")

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting FortiMonitor MCP server...")

        try:
            async with stdio_server() as (read_stream, write_stream):
                # Create capabilities using proper MCP types
                capabilities = ServerCapabilities(
                    tools=ToolsCapability(listChanged=False)
                )

                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=_settings.mcp_server_name,
                        server_version=_settings.mcp_server_version,
                        capabilities=capabilities,
                    ),
                )
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
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
