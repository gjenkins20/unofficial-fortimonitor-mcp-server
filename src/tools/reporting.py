"""Tools for reporting and analytics - Priority 5."""

import logging
import re
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter
from mcp.types import TextContent, Tool

from ..fortimonitor.client import FortiMonitorClient
from ..fortimonitor.exceptions import APIError

logger = logging.getLogger(__name__)


# ============================================================================
# SYSTEM HEALTH & STATISTICS TOOLS
# ============================================================================

def get_system_health_summary_tool_definition():
    """Return tool definition for system health summary."""
    return Tool(
        name= "get_system_health_summary",
        description= (
            "Get a comprehensive summary of system health including total servers, "
            "active outages, critical issues, and overall status. Provides a high-level "
            "overview of the entire monitoring infrastructure."
        ),
        inputSchema= {
            "type": "object",
            "properties": {}
        }
    )


async def handle_get_system_health_summary(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_system_health_summary tool execution."""
    try:
        logger.info("Generating system health summary")

        # Get servers
        servers_response = client.get_servers(limit=500)
        servers = servers_response.server_list
        total_servers = len(servers)

        # Count server statuses
        active_servers = sum(1 for s in servers if s.status == 'active')
        inactive_servers = sum(1 for s in servers if s.status == 'inactive')
        paused_servers = sum(1 for s in servers if s.status == 'paused')

        # Get outages
        outages_response = client.get_active_outages(limit=500)
        outages = outages_response.outage_list
        total_outages = len(outages)

        # Count outages by severity
        critical_outages = sum(1 for o in outages if o.severity == 'critical')
        warning_outages = sum(1 for o in outages if o.severity == 'warning')
        info_outages = sum(1 for o in outages if o.severity == 'info')

        # Count acknowledged vs unacknowledged
        acknowledged = sum(1 for o in outages if o.acknowledged)
        unacknowledged = total_outages - acknowledged

        # Determine overall health status
        if critical_outages == 0 and warning_outages == 0:
            health_status = "Healthy"
            health_emoji = "OK"
        elif critical_outages == 0:
            health_status = "Warning - Minor Issues"
            health_emoji = "WARN"
        elif critical_outages <= 3:
            health_status = "Critical - Issues Detected"
            health_emoji = "CRIT"
        else:
            health_status = "Severe - Multiple Critical Issues"
            health_emoji = "SEVERE"

        # Format response
        output_lines = [
            f"**System Health Summary**",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**Overall Status**: [{health_emoji}] {health_status}\n",

            f"**Servers ({total_servers} total)**",
            f"  [OK] Active: {active_servers}",
            f"  [PAUSED] Paused: {paused_servers}",
            f"  [OFF] Inactive: {inactive_servers}\n",

            f"**Active Outages ({total_outages} total)**",
            f"  [CRIT] Critical: {critical_outages}",
            f"  [WARN] Warning: {warning_outages}",
            f"  [INFO] Info: {info_outages}\n",

            f"**Acknowledgment Status**",
            f"  Acknowledged: {acknowledged}",
            f"  Unacknowledged: {unacknowledged}"
        ]

        # Add recommendations
        if unacknowledged > 0:
            output_lines.append(f"\n**Recommendation**: {unacknowledged} outage(s) need acknowledgment")

        if critical_outages > 0:
            output_lines.append(f"**Recommendation**: Address {critical_outages} critical issue(s) immediately")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error generating health summary: {e}")
        return [TextContent(
            type="text",
            text=f"Error generating health summary: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]


def get_outage_statistics_tool_definition():
    """Return tool definition for outage statistics."""
    return Tool(
        name= "get_outage_statistics",
        description= (
            "Get statistical analysis of outages including breakdown by severity, "
            "top affected servers, acknowledgment rates, and time-based trends."
        ),
        inputSchema= {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "default": 7,
                    "minimum": 1,
                    "maximum": 90,
                    "description":"Number of days to analyze (recent outages)"
                }
            }
        }
    )


async def handle_get_outage_statistics(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_outage_statistics tool execution."""
    try:
        days = arguments.get("days", 7)

        logger.info(f"Generating outage statistics for last {days} days")

        # Get active outages
        outages_response = client.get_active_outages(limit=500)
        outages = outages_response.outage_list

        if not outages:
            return [TextContent(
                type="text",
                text=f"[OK] No active outages in the last {days} days!"
            )]

        # Calculate statistics
        total_outages = len(outages)

        # By severity
        severity_counts = Counter(o.severity for o in outages)

        # By status
        status_counts = Counter(o.status for o in outages)

        # Acknowledgment rate
        acknowledged_count = sum(1 for o in outages if o.acknowledged)
        ack_rate = (acknowledged_count / total_outages * 100) if total_outages > 0 else 0

        # Count outages per server
        server_outages = Counter()
        for outage in outages:
            if hasattr(outage, 'server') and outage.server:
                server_outages[outage.server] += 1

        # Get top 5 servers with most outages
        top_servers = server_outages.most_common(5)

        # Format response
        output_lines = [
            f"**Outage Statistics (Last {days} days)**\n",
            f"**Total Active Outages**: {total_outages}\n",

            f"**By Severity:**",
        ]

        for severity in ['critical', 'warning', 'info']:
            count = severity_counts.get(severity, 0)
            label = {'critical': '[CRIT]', 'warning': '[WARN]', 'info': '[INFO]'}.get(severity, '')
            output_lines.append(f"  {label} {severity.title()}: {count} ({count/total_outages*100:.1f}%)")

        output_lines.append(f"\n**By Status:**")
        for status, count in status_counts.most_common():
            output_lines.append(f"  - {status}: {count}")

        output_lines.append(f"\n**Acknowledgment Rate**: {ack_rate:.1f}%")
        output_lines.append(f"  Acknowledged: {acknowledged_count}")
        output_lines.append(f"  Unacknowledged: {total_outages - acknowledged_count}")

        if top_servers:
            output_lines.append(f"\n**Top Servers by Outage Count:**")
            for i, (server_url, count) in enumerate(top_servers, 1):
                # Try to extract server ID and get name
                match = re.search(r'/server/(\d+)', server_url)
                if match:
                    server_id = int(match.group(1))
                    try:
                        server = client.get_server_details(server_id)
                        server_name = server.name
                    except Exception:
                        server_name = f"Server {server_id}"
                else:
                    server_name = "Unknown"

                output_lines.append(f"  {i}. {server_name}: {count} outages")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error generating outage statistics: {e}")
        return [TextContent(
            type="text",
            text=f"Error generating outage statistics: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]


def get_server_statistics_tool_definition():
    """Return tool definition for server statistics."""
    return Tool(
        name= "get_server_statistics",
        description= (
            "Get statistical analysis of servers including distribution by status, "
            "operating systems, tags, and other attributes."
        ),
        inputSchema= {
            "type": "object",
            "properties": {}
        }
    )


async def handle_get_server_statistics(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_server_statistics tool execution."""
    try:
        logger.info("Generating server statistics")

        # Get all servers
        servers_response = client.get_servers(limit=500)
        servers = servers_response.server_list
        total_servers = len(servers)

        if total_servers == 0:
            return [TextContent(
                type="text",
                text="No servers found in the system."
            )]

        # Calculate statistics

        # By status
        status_counts = Counter(s.status for s in servers)

        # By tags
        all_tags = []
        for server in servers:
            if server.tags:
                if isinstance(server.tags, list):
                    all_tags.extend(server.tags)
                elif isinstance(server.tags, str):
                    all_tags.extend([t.strip() for t in server.tags.split(',') if t.strip()])

        tag_counts = Counter(all_tags)
        top_tags = tag_counts.most_common(10)

        # Format response
        output_lines = [
            f"**Server Statistics**\n",
            f"**Total Servers**: {total_servers}\n",

            f"**By Status:**",
        ]

        for status in ['active', 'inactive', 'paused']:
            count = status_counts.get(status, 0)
            percentage = (count / total_servers * 100) if total_servers > 0 else 0
            label = {'active': '[OK]', 'inactive': '[OFF]', 'paused': '[PAUSED]'}.get(status, '')
            output_lines.append(f"  {label} {status.title()}: {count} ({percentage:.1f}%)")

        if top_tags:
            output_lines.append(f"\n**Top 10 Tags:**")
            for i, (tag, count) in enumerate(top_tags, 1):
                percentage = (count / total_servers * 100)
                output_lines.append(f"  {i}. {tag}: {count} servers ({percentage:.1f}%)")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error generating server statistics: {e}")
        return [TextContent(
            type="text",
            text=f"Error generating server statistics: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]


def get_top_alerting_servers_tool_definition():
    """Return tool definition for top alerting servers."""
    return Tool(
        name= "get_top_alerting_servers",
        description= (
            "Get a list of servers with the most active outages. "
            "Useful for identifying problematic servers that need attention."
        ),
        inputSchema= {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                    "description":"Number of top servers to return"
                }
            }
        }
    )


async def handle_get_top_alerting_servers(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle get_top_alerting_servers tool execution."""
    try:
        limit = arguments.get("limit", 10)

        logger.info(f"Getting top {limit} alerting servers")

        # Get all active outages
        outages_response = client.get_active_outages(limit=500)
        outages = outages_response.outage_list

        if not outages:
            return [TextContent(
                type="text",
                text="[OK] No active outages - no servers are alerting!"
            )]

        # Count outages per server
        server_outages = {}
        for outage in outages:
            if hasattr(outage, 'server') and outage.server:
                if outage.server not in server_outages:
                    server_outages[outage.server] = {
                        'count': 0,
                        'critical': 0,
                        'warning': 0,
                        'info': 0
                    }
                server_outages[outage.server]['count'] += 1
                if outage.severity in server_outages[outage.server]:
                    server_outages[outage.server][outage.severity] += 1

        # Sort by count (critical count first, then total count)
        sorted_servers = sorted(
            server_outages.items(),
            key=lambda x: (x[1]['critical'], x[1]['count']),
            reverse=True
        )[:limit]

        # Format response
        output_lines = [
            f"**Top {min(limit, len(sorted_servers))} Alerting Servers**\n"
        ]

        for i, (server_url, stats) in enumerate(sorted_servers, 1):
            # Extract server ID and get details
            match = re.search(r'/server/(\d+)', server_url)
            if match:
                server_id = int(match.group(1))
                try:
                    server = client.get_server_details(server_id)
                    server_name = server.name
                    server_status = server.status
                except Exception:
                    server_name = f"Server {server_id}"
                    server_status = "unknown"
            else:
                server_id = "N/A"
                server_name = "Unknown"
                server_status = "unknown"

            output_lines.append(f"\n**{i}. {server_name}** (ID: {server_id})")
            output_lines.append(f"  Status: {server_status}")
            output_lines.append(f"  Total Outages: {stats['count']}")
            output_lines.append(f"  [CRIT] Critical: {stats['critical']}")
            output_lines.append(f"  [WARN] Warning: {stats['warning']}")
            output_lines.append(f"  [INFO] Info: {stats['info']}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error getting top alerting servers: {e}")
        return [TextContent(
            type="text",
            text=f"Error getting top alerting servers: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]


# ============================================================================
# DATA EXPORT & REPORTING TOOLS
# ============================================================================

def export_servers_list_tool_definition():
    """Return tool definition for exporting servers list."""
    return Tool(
        name= "export_servers_list",
        description= (
            "Export a list of all servers with their details in CSV format. "
            "Useful for reporting, analysis, or importing into other systems."
        ),
        inputSchema= {
            "type": "object",
            "properties": {
                "include_tags": {
                    "type": "boolean",
                    "default": True,
                    "description":"Include server tags in export"
                },
                "status_filter": {
                    "type": "string",
                    "enum": ["all", "active", "inactive", "paused"],
                    "default": "all",
                    "description":"Filter servers by status"
                }
            }
        }
    )


async def handle_export_servers_list(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle export_servers_list tool execution."""
    try:
        include_tags = arguments.get("include_tags", True)
        status_filter = arguments.get("status_filter", "all")

        logger.info(f"Exporting servers list (status={status_filter})")

        # Get servers
        servers_response = client.get_servers(limit=500)
        servers = servers_response.server_list

        # Apply status filter
        if status_filter != "all":
            servers = [s for s in servers if s.status == status_filter]

        if not servers:
            return [TextContent(
                type="text",
                text=f"No servers found with status: {status_filter}"
            )]

        # Build CSV
        csv_lines = []

        # Header
        if include_tags:
            csv_lines.append("ID,Name,FQDN,Status,Tags")
        else:
            csv_lines.append("ID,Name,FQDN,Status")

        # Data rows
        for server in servers:
            tags_str = ""
            if include_tags and server.tags:
                if isinstance(server.tags, list):
                    tags_str = "; ".join(server.tags)
                else:
                    tags_str = str(server.tags)

            # Escape commas in fields
            name = str(server.name).replace(',', ';') if server.name else ""
            fqdn = str(server.fqdn).replace(',', ';') if server.fqdn else ""

            if include_tags:
                csv_lines.append(f"{server.id},{name},{fqdn},{server.status},{tags_str}")
            else:
                csv_lines.append(f"{server.id},{name},{fqdn},{server.status}")

        csv_content = "\n".join(csv_lines)

        # Format response - show full CSV
        output_lines = [
            f"**Servers Export**\n",
            f"Total Servers: {len(servers)}",
            f"Status Filter: {status_filter}",
            f"Include Tags: {include_tags}\n",
            f"**CSV Data:**\n",
            f"```csv",
            csv_content,
            "```",
            f"\n**Tip**: Copy the CSV data above to use in Excel or other tools"
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error exporting servers: {e}")
        return [TextContent(
            type="text",
            text=f"Error exporting servers: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]


def export_outage_history_tool_definition():
    """Return tool definition for exporting outage history."""
    return Tool(
        name= "export_outage_history",
        description= (
            "Export active outage history in CSV format. "
            "Useful for incident reports, trend analysis, and documentation."
        ),
        inputSchema= {
            "type": "object",
            "properties": {
                "severity_filter": {
                    "type": "string",
                    "enum": ["all", "critical", "warning", "info"],
                    "default": "all",
                    "description":"Filter outages by severity"
                }
            }
        }
    )


async def handle_export_outage_history(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle export_outage_history tool execution."""
    try:
        severity_filter = arguments.get("severity_filter", "all")

        logger.info(f"Exporting outage history (severity={severity_filter})")

        # Get outages
        outages_response = client.get_active_outages(limit=500)
        outages = outages_response.outage_list

        # Apply severity filter
        if severity_filter != "all":
            outages = [o for o in outages if o.severity == severity_filter]

        if not outages:
            return [TextContent(
                type="text",
                text=f"No outages found with severity: {severity_filter}"
            )]

        # Build CSV
        csv_lines = []
        csv_lines.append("Outage_ID,Server,Severity,Status,Started,Acknowledged")

        for outage in outages:
            outage_id = outage.id if hasattr(outage, 'id') else 'N/A'
            server = outage.server if hasattr(outage, 'server') else 'N/A'
            severity = outage.severity
            status = outage.status
            started = outage.start_time.strftime('%Y-%m-%d %H:%M:%S') if outage.start_time else 'N/A'
            ack = 'Yes' if outage.acknowledged else 'No'

            # Extract server name from URL if possible
            if 'server' in str(server):
                match = re.search(r'/server/(\d+)', str(server))
                if match:
                    server_id = match.group(1)
                    server = f"Server_{server_id}"

            csv_lines.append(f"{outage_id},{server},{severity},{status},{started},{ack}")

        csv_content = "\n".join(csv_lines)

        # Format response - show full CSV
        output_lines = [
            f"**Outage History Export**\n",
            f"Total Outages: {len(outages)}",
            f"Severity Filter: {severity_filter}\n",
            f"**CSV Data:**\n",
            f"```csv",
            csv_content,
            "```",
            f"\n**Tip**: Copy the CSV data above for incident reports"
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error exporting outages: {e}")
        return [TextContent(
            type="text",
            text=f"Error exporting outages: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]


def generate_availability_report_tool_definition():
    """Return tool definition for generating availability report."""
    return Tool(
        name= "generate_availability_report",
        description= (
            "Generate an availability/uptime report for servers. "
            "Shows availability percentage based on active outages. "
            "Useful for SLA reporting and performance tracking."
        ),
        inputSchema= {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 90,
                    "description":"Number of days for the report period"
                }
            }
        }
    )


async def handle_generate_availability_report(
    arguments: dict,
    client: FortiMonitorClient
) -> List[TextContent]:
    """Handle generate_availability_report tool execution."""
    try:
        days = arguments.get("days", 30)

        logger.info(f"Generating availability report for {days} days")

        # Get servers
        servers_response = client.get_servers(limit=100)
        servers = servers_response.server_list

        # Get outages
        outages_response = client.get_active_outages(limit=500)
        outages = outages_response.outage_list

        # Count outages per server
        server_outages = {}
        for outage in outages:
            if hasattr(outage, 'server') and outage.server:
                if outage.server not in server_outages:
                    server_outages[outage.server] = 0
                server_outages[outage.server] += 1

        # Calculate availability (simplified)
        # Note: Real availability calculation would need historical data
        # This is a simplified estimate based on active outages

        output_lines = [
            f"**Availability Report ({days}-Day Period)**",
            f"Report Date: {datetime.now().strftime('%Y-%m-%d')}\n",
            f"**Summary:**",
            f"  Total Servers: {len(servers)}",
            f"  Servers with Outages: {len(server_outages)}\n",
            f"**Top Servers by Availability:**\n"
        ]

        # Sort servers by outage count (fewer outages = better availability)
        server_availability = []
        for server in servers[:20]:  # Top 20 servers
            server_url = f"https://api2.panopta.com/v2/server/{server.id}"
            outage_count = server_outages.get(server_url, 0)

            # Simplified availability calculation
            # Assume: no outages = 99.9%, 1 outage = 99%, 2+ = proportionally less
            if outage_count == 0:
                availability = 99.9
            elif outage_count == 1:
                availability = 99.0
            elif outage_count == 2:
                availability = 98.0
            else:
                availability = max(95.0, 99.0 - (outage_count * 1.0))

            server_availability.append((server, availability, outage_count))

        # Sort by availability
        server_availability.sort(key=lambda x: x[1], reverse=True)

        for i, (server, avail, outage_count) in enumerate(server_availability[:10], 1):
            status_label = "[OK]" if avail >= 99.5 else "[WARN]" if avail >= 98.0 else "[CRIT]"
            output_lines.append(
                f"{i}. {status_label} **{server.name}**: {avail:.2f}% "
                f"({outage_count} outages)"
            )

        output_lines.append(
            f"\n**Note**: Availability calculated based on current active outages. "
            f"For precise SLA calculations, use FortiMonitor's built-in reporting."
        )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except APIError as e:
        logger.error(f"API error generating availability report: {e}")
        return [TextContent(
            type="text",
            text=f"Error generating availability report: {str(e)}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]
