"""
FortiMonitor MCP Prompts - Pre-built Workflow Templates

Copyright (c) 2026 Gregori Jenkins
https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server

Provides ready-made prompt templates that appear in Claude Desktop's UI,
giving users one-click access to common monitoring workflows.
"""

from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent


# ── Prompt Definitions ───────────────────────────────────────────────

PROMPTS = {
    "morning-situation-report": Prompt(
        name="morning-situation-report",
        description=(
            "Generate a prioritized morning briefing: active outages, "
            "maintenance windows, server health summary, and top alerting servers."
        ),
        arguments=[
            PromptArgument(
                name="limit",
                description="Maximum number of items per section (default: 10)",
                required=False,
            ),
        ],
    ),
    "investigate-outage": Prompt(
        name="investigate-outage",
        description=(
            "Deep investigation of a server or outage: pull outage details, "
            "timeline, metrics, maintenance history, and notification config."
        ),
        arguments=[
            PromptArgument(
                name="server_id",
                description="The server ID or FQDN to investigate",
                required=True,
            ),
        ],
    ),
    "capacity-planning-review": Prompt(
        name="capacity-planning-review",
        description=(
            "Review server resource utilization trends and threshold proximity "
            "to identify capacity risks before they cause outages."
        ),
        arguments=[
            PromptArgument(
                name="server_group_id",
                description="Optional server group ID to scope the review",
                required=False,
            ),
        ],
    ),
    "change-impact-assessment": Prompt(
        name="change-impact-assessment",
        description=(
            "Before maintenance, assess impact: affected servers, dependent "
            "compound services, notification groups, and active outages."
        ),
        arguments=[
            PromptArgument(
                name="server_id",
                description="The server ID to assess for maintenance impact",
                required=True,
            ),
        ],
    ),
    "weekly-executive-summary": Prompt(
        name="weekly-executive-summary",
        description=(
            "Generate a weekly executive summary: outage count, MTTR, "
            "availability percentage, top offenders, and trend analysis."
        ),
        arguments=[
            PromptArgument(
                name="days",
                description="Number of days to cover (default: 7)",
                required=False,
            ),
        ],
    ),
    "alert-noise-audit": Prompt(
        name="alert-noise-audit",
        description=(
            "Find servers with frequent short outages (flapping) and suggest "
            "alert tuning to reduce noise and improve signal-to-noise ratio."
        ),
        arguments=[
            PromptArgument(
                name="days",
                description="Number of days to analyze (default: 7)",
                required=False,
            ),
        ],
    ),
    "monitoring-coverage-check": Prompt(
        name="monitoring-coverage-check",
        description=(
            "Audit monitoring coverage: find servers with missing network "
            "service checks, no notification schedules, or stale configurations."
        ),
        arguments=[
            PromptArgument(
                name="server_group_id",
                description="Optional server group ID to scope the audit",
                required=False,
            ),
        ],
    ),
}


# ── Prompt Message Builders ──────────────────────────────────────────

def _build_morning_situation_report(arguments: dict) -> list:
    limit = arguments.get("limit", "10")
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Generate a morning situation report for our FortiMonitor environment. "
                    f"Use the following tools to gather data, limiting each to {limit} results:\n\n"
                    "1. Use `get_servers_with_active_outages` to list all servers currently in outage\n"
                    "2. Use `list_active_or_pending_maintenance` to show upcoming and active maintenance windows\n"
                    "3. Use `get_system_health_summary` to get overall health metrics\n"
                    "4. Use `get_top_alerting_servers` to find the noisiest servers\n"
                    "5. Use `get_outage_statistics` to get recent outage trends\n\n"
                    "Synthesize the results into a prioritized briefing with:\n"
                    "- **Critical**: Active outages requiring immediate attention\n"
                    "- **Awareness**: Maintenance windows and scheduled changes\n"
                    "- **Trends**: Notable patterns in alerting or health metrics\n"
                    "- **Action Items**: Recommended follow-ups"
                ),
            ),
        ),
    ]


def _build_investigate_outage(arguments: dict) -> list:
    server_id = arguments.get("server_id", "")
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Investigate server {server_id} in FortiMonitor. "
                    "Perform a thorough investigation using these tools:\n\n"
                    f"1. Use `get_server_details` with server_id={server_id} to get server configuration\n"
                    f"2. Use `check_server_health` with server_id={server_id} for current health status\n"
                    f"3. Use `get_outages` filtered to this server to find recent outage history\n"
                    f"4. Use `get_server_metrics` with server_id={server_id} for resource utilization\n"
                    f"5. Use `list_maintenance_windows` to check if maintenance is scheduled\n"
                    f"6. Use `get_server_network_services` with server_id={server_id} for monitored services\n\n"
                    "Build an investigation report with:\n"
                    "- **Server Profile**: Name, FQDN, group, template, status\n"
                    "- **Current Health**: Up/down status, active outages with duration\n"
                    "- **Outage History**: Recent outages with timeline and resolution\n"
                    "- **Resource Metrics**: CPU, memory, disk trends\n"
                    "- **Monitored Services**: What's being checked and current response times\n"
                    "- **Root Cause Hypotheses**: Based on the data, what's likely causing issues\n"
                    "- **Recommended Actions**: Next steps to investigate or resolve"
                ),
            ),
        ),
    ]


def _build_capacity_planning_review(arguments: dict) -> list:
    group_scope = ""
    group_id = arguments.get("server_group_id")
    if group_id:
        group_scope = f" within server group {group_id}"
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Perform a capacity planning review{group_scope} using FortiMonitor data.\n\n"
                    "1. Use `get_servers` to list servers" + (f" (filter by group {group_id})" if group_id else "") + "\n"
                    "2. For each server (or top 10 by utilization), use `get_server_metrics` to get resource data\n"
                    "3. Use `list_server_resources` for agent resource details on high-utilization servers\n"
                    "4. Use `get_outage_statistics` to correlate capacity with outage frequency\n\n"
                    "Produce a capacity planning report with:\n"
                    "- **At Risk**: Servers approaching thresholds (>80% utilization)\n"
                    "- **Trending Up**: Servers with growing resource consumption\n"
                    "- **Healthy**: Servers with comfortable headroom\n"
                    "- **Recommendations**: Scale-up, rebalance, or threshold adjustment suggestions"
                ),
            ),
        ),
    ]


def _build_change_impact_assessment(arguments: dict) -> list:
    server_id = arguments.get("server_id", "")
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Perform a change impact assessment for server {server_id} before maintenance.\n\n"
                    f"1. Use `get_server_details` with server_id={server_id} to get server config and group membership\n"
                    f"2. Use `get_server_network_services` with server_id={server_id} to find dependent services\n"
                    "3. Use `list_compound_services` to find compound services that include this server\n"
                    f"4. Use `get_outages` for this server to check if there are active outages\n"
                    "5. Use `list_notification_schedules` to identify who gets alerted\n"
                    "6. Use `list_contact_groups` to see notification routing\n\n"
                    "Produce an impact assessment with:\n"
                    "- **Server Details**: Name, role, group, template\n"
                    "- **Service Dependencies**: Compound services and network services affected\n"
                    "- **Notification Impact**: Who will be alerted during maintenance\n"
                    "- **Current State**: Any active outages or issues\n"
                    "- **Maintenance Recommendation**: Suggested maintenance window timing and pre-flight checks"
                ),
            ),
        ),
    ]


def _build_weekly_executive_summary(arguments: dict) -> list:
    days = arguments.get("days", "7")
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Generate a weekly executive summary covering the last {days} days.\n\n"
                    "1. Use `get_outage_statistics` to get outage counts and trends\n"
                    "2. Use `get_system_health_summary` for current infrastructure health\n"
                    "3. Use `get_top_alerting_servers` to identify top offenders\n"
                    "4. Use `generate_availability_report` for availability percentages\n"
                    "5. Use `get_server_statistics` for fleet overview\n\n"
                    "Produce an executive summary with:\n"
                    "- **Availability**: Overall and per-group availability percentages\n"
                    "- **Incidents**: Total outage count, MTTR, comparison to prior period\n"
                    "- **Top Offenders**: Servers causing the most alerts\n"
                    "- **Improvements**: What got better this week\n"
                    "- **Concerns**: Emerging risks or degradation trends\n"
                    "- **Action Items**: Recommended priorities for the coming week"
                ),
            ),
        ),
    ]


def _build_alert_noise_audit(arguments: dict) -> list:
    days = arguments.get("days", "7")
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Perform an alert noise audit over the last {days} days to identify flapping and noisy alerts.\n\n"
                    "1. Use `get_top_alerting_servers` to find the noisiest servers\n"
                    f"2. Use `get_outages` to pull outage history for the last {days} days\n"
                    "3. For top alerting servers, use `get_server_network_services` to see check configurations\n"
                    "4. Use `get_outage_statistics` for overall alert volume trends\n\n"
                    "Analyze the data for:\n"
                    "- **Flapping**: Servers with repeated short outages (<5 min) suggesting threshold issues\n"
                    "- **High Volume**: Servers generating disproportionate alert counts\n"
                    "- **Correlation**: Multiple alerts that may share a root cause\n"
                    "- **Tuning Recommendations**: Specific threshold adjustments, check interval changes, "
                    "or notification delay additions to reduce noise without missing real incidents"
                ),
            ),
        ),
    ]


def _build_monitoring_coverage_check(arguments: dict) -> list:
    group_scope = ""
    group_id = arguments.get("server_group_id")
    if group_id:
        group_scope = f" in server group {group_id}"
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Audit monitoring coverage{group_scope} to find gaps and stale configurations.\n\n"
                    "1. Use `get_servers` to list all servers" + (f" in group {group_id}" if group_id else "") + "\n"
                    "2. For each server (or a representative sample), use `get_server_network_services` to check what's monitored\n"
                    "3. Use `list_notification_schedules` to verify alerting is configured\n"
                    "4. Use `list_contact_groups` to check notification routing\n"
                    "5. Use `list_server_templates` to identify template coverage\n\n"
                    "Produce a coverage audit with:\n"
                    "- **Uncovered Servers**: Servers with no or minimal network service checks\n"
                    "- **No Notifications**: Servers not associated with any notification schedule\n"
                    "- **No Template**: Servers not using a monitoring template (one-off configs)\n"
                    "- **Stale Checks**: Services with no recent data or disabled checks\n"
                    "- **Recommendations**: Templates to apply, checks to add, notification gaps to close"
                ),
            ),
        ),
    ]


# Map prompt name -> message builder
PROMPT_HANDLERS = {
    "morning-situation-report": _build_morning_situation_report,
    "investigate-outage": _build_investigate_outage,
    "capacity-planning-review": _build_capacity_planning_review,
    "change-impact-assessment": _build_change_impact_assessment,
    "weekly-executive-summary": _build_weekly_executive_summary,
    "alert-noise-audit": _build_alert_noise_audit,
    "monitoring-coverage-check": _build_monitoring_coverage_check,
}
