"""
FortiMonitor MCP Tools - Guided Sessions

Copyright (c) 2026 Gregori Jenkins
https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server

Stateful guided session system that walks users through interactive
multi-step workflows. The server drives the conversation by presenting
menus, fetching relevant candidates, and advancing through steps based
on user choices.
"""

import json
import time
import uuid
from typing import Any, Optional
import mcp.types


# ── Session State ─────────────────────────────────────────────────

_sessions: dict[str, dict] = {}

def _cleanup_expired():
    """No-op. Sessions persist for the lifetime of the server process."""
    pass


# ── Workflow Definitions ─────────────────────────────────────────

WORKFLOWS = {
    "investigate-outage": {
        "title": "Investigate an Outage",
        "description": "Find servers with active outages and perform a deep investigation.",
        "steps": ["select_server", "investigate"],
    },
    "change-impact": {
        "title": "Change Impact Assessment",
        "description": "Assess the impact of planned maintenance on a server.",
        "steps": ["select_server", "assess_impact"],
    },
    "capacity-review": {
        "title": "Capacity Planning Review",
        "description": "Review resource utilization for servers approaching thresholds.",
        "steps": ["select_group_or_all", "review_capacity"],
    },
    "alert-tuning": {
        "title": "Alert Noise Audit",
        "description": "Find flapping servers and get tuning recommendations.",
        "steps": ["select_timeframe", "analyze_noise"],
    },
    "monitoring-audit": {
        "title": "Monitoring Coverage Audit",
        "description": "Find servers with monitoring gaps.",
        "steps": ["select_group_or_all", "run_audit"],
    },
}


# ── Step Handlers ─────────────────────────────────────────────────

async def _step_present_menu(session: dict, client) -> str:
    """Present the main workflow menu."""
    lines = [
        "Welcome to the FortiMonitor Guided Session.",
        "",
        "Available workflows:",
        "",
    ]
    for i, (wf_id, wf) in enumerate(WORKFLOWS.items(), 1):
        lines.append(f"  {i}. **{wf['title']}** — {wf['description']}")

    lines.extend([
        "",
        "Reply with the number or name of the workflow you'd like to start.",
        "",
        f"Session ID: `{session['id']}`",
    ])
    return "\n".join(lines)


async def _step_select_server(session: dict, choice: str, client) -> str:
    """Fetch active outages and present server candidates."""
    # Fetch servers with active outages
    outages = client._request("GET", "/outage", params={"limit": 10, "status": "active"})
    outage_list = outages.get("outage_list", [])

    if not outage_list:
        session["step"] = "complete"
        return "No active outages found. Your environment looks healthy!"

    # Also fetch all servers for non-outage workflows
    servers = client._request("GET", "/server", params={"limit": 10})
    server_list = servers.get("server_list", [])

    # Build candidate list from outages
    candidates = []
    for outage in outage_list:
        server_name = outage.get("server_name", outage.get("fqdn", "Unknown"))
        server_url = outage.get("server_url", "")
        sid = server_url.rstrip("/").split("/")[-1] if server_url else "?"
        severity = outage.get("severity", outage.get("type", "unknown"))
        started = outage.get("start_time", "unknown")
        candidates.append({
            "name": server_name,
            "server_id": sid,
            "severity": severity,
            "started": started,
        })

    session["candidates"] = candidates

    lines = [
        f"**{WORKFLOWS[session['workflow']]['title']}**",
        "",
        "Here are servers currently experiencing outages:",
        "",
    ]
    for i, c in enumerate(candidates, 1):
        lines.append(f"  {i}. **{c['name']}** (ID: {c['server_id']}) — {c['severity']}, since {c['started']}")

    lines.extend([
        "",
        "Reply with the number of the server you'd like to investigate,",
        "or provide a server ID directly.",
    ])
    return "\n".join(lines)


async def _step_investigate(session: dict, choice: str, client) -> str:
    """Perform deep investigation on the selected server."""
    server_id = _resolve_choice(session, choice)
    if not server_id:
        return f"Invalid selection: '{choice}'. Please reply with a number from the list or a server ID."

    # Gather investigation data
    details = _safe_request(client, "GET", f"/server/{server_id}")
    outages = _safe_request(client, "GET", f"/server/{server_id}/outage", params={"limit": 5})
    net_services = _safe_request(client, "GET", f"/server/{server_id}/network_service", params={"limit": 20})
    resources = _safe_request(client, "GET", f"/server/{server_id}/agent_resource", params={"limit": 10})

    session["step"] = "complete"
    session["result"] = {
        "server_id": server_id,
        "details": details,
        "outages": outages,
        "network_services": net_services,
        "agent_resources": resources,
    }

    result = json.dumps(session["result"], indent=2, default=str)
    server_name = details.get("name", server_id) if details else server_id

    return (
        f"**Investigation Report: {server_name}**\n\n"
        f"Here is the full investigation data for server {server_id}. "
        f"Please analyze this data and provide:\n"
        f"- Current health assessment\n"
        f"- Root cause hypotheses based on outage patterns and metrics\n"
        f"- Recommended next steps\n\n"
        f"```json\n{result}\n```"
    )


async def _step_assess_impact(session: dict, choice: str, client) -> str:
    """Perform change impact assessment on the selected server."""
    server_id = _resolve_choice(session, choice)
    if not server_id:
        return f"Invalid selection: '{choice}'. Please reply with a number from the list or a server ID."

    details = _safe_request(client, "GET", f"/server/{server_id}")
    net_services = _safe_request(client, "GET", f"/server/{server_id}/network_service", params={"limit": 50})
    outages = _safe_request(client, "GET", f"/server/{server_id}/outage", params={"limit": 5, "status": "active"})

    session["step"] = "complete"
    server_name = details.get("name", server_id) if details else server_id

    result = {
        "server_id": server_id,
        "server_details": details,
        "network_services": net_services,
        "active_outages": outages,
    }

    return (
        f"**Change Impact Assessment: {server_name}**\n\n"
        f"```json\n{json.dumps(result, indent=2, default=str)}\n```\n\n"
        f"Please analyze this data and summarize:\n"
        f"- Services that will be affected during maintenance\n"
        f"- Current active issues to be aware of\n"
        f"- Recommended maintenance window timing"
    )


async def _step_select_group_or_all(session: dict, choice: str, client) -> str:
    """Present server group options or proceed with all servers."""
    groups = _safe_request(client, "GET", "/server_group", params={"limit": 20})
    group_list = groups.get("server_group_list", []) if groups else []

    candidates = [{"name": "All Servers", "id": "all"}]
    for g in group_list:
        url = g.get("url", "")
        gid = url.rstrip("/").split("/")[-1] if url else "?"
        candidates.append({"name": g.get("name", "Unknown"), "id": gid})

    session["candidates"] = [{"name": c["name"], "server_id": c["id"]} for c in candidates]

    lines = [
        f"**{WORKFLOWS[session['workflow']]['title']}**",
        "",
        "Select scope:",
        "",
    ]
    for i, c in enumerate(candidates, 1):
        lines.append(f"  {i}. **{c['name']}**" + (f" (Group ID: {c['id']})" if c['id'] != 'all' else ""))

    lines.extend(["", "Reply with a number to select."])
    return "\n".join(lines)


async def _step_review_capacity(session: dict, choice: str, client) -> str:
    """Review capacity for selected scope."""
    scope_id = _resolve_choice(session, choice)
    if not scope_id:
        return f"Invalid selection: '{choice}'. Please reply with a number from the list."

    params = {"limit": 20}
    if scope_id == "all":
        servers = _safe_request(client, "GET", "/server", params=params)
    else:
        servers = _safe_request(client, "GET", f"/server_group/{scope_id}/server", params=params)

    session["step"] = "complete"
    return (
        f"**Capacity Planning Data**\n\n"
        f"```json\n{json.dumps(servers, indent=2, default=str)}\n```\n\n"
        f"Please analyze server resource utilization and identify:\n"
        f"- Servers approaching capacity thresholds\n"
        f"- Trending resource consumption\n"
        f"- Scale-up or rebalance recommendations"
    )


async def _step_run_audit(session: dict, choice: str, client) -> str:
    """Run monitoring coverage audit for selected scope."""
    scope_id = _resolve_choice(session, choice)
    if not scope_id:
        return f"Invalid selection: '{choice}'. Please reply with a number from the list."

    params = {"limit": 30}
    if scope_id == "all":
        servers = _safe_request(client, "GET", "/server", params=params)
    else:
        servers = _safe_request(client, "GET", f"/server_group/{scope_id}/server", params=params)

    server_list = servers.get("server_list", []) if servers else []
    audit_results = []
    for server in server_list[:15]:
        server_url = server.get("url", "")
        sid = server_url.rstrip("/").split("/")[-1] if server_url else None
        if not sid:
            continue
        ns = _safe_request(client, "GET", f"/server/{sid}/network_service", params={"limit": 50})
        ns_count = len(ns.get("network_service_list", [])) if ns else 0
        audit_results.append({
            "name": server.get("name", server.get("fqdn", "unknown")),
            "server_id": sid,
            "network_service_count": ns_count,
        })

    session["step"] = "complete"
    return (
        f"**Monitoring Coverage Audit**\n\n"
        f"```json\n{json.dumps(audit_results, indent=2, default=str)}\n```\n\n"
        f"Please analyze and identify:\n"
        f"- Servers with zero or minimal monitoring checks\n"
        f"- Gaps in coverage\n"
        f"- Recommended checks to add"
    )


async def _step_select_timeframe(session: dict, choice: str, client) -> str:
    """Present timeframe options for alert analysis."""
    session["candidates"] = [
        {"name": "Last 24 hours", "server_id": "1"},
        {"name": "Last 7 days", "server_id": "7"},
        {"name": "Last 30 days", "server_id": "30"},
    ]

    lines = [
        f"**{WORKFLOWS[session['workflow']]['title']}**",
        "",
        "Select the analysis timeframe:",
        "",
        "  1. **Last 24 hours**",
        "  2. **Last 7 days**",
        "  3. **Last 30 days**",
        "",
        "Reply with a number.",
    ]
    return "\n".join(lines)


async def _step_analyze_noise(session: dict, choice: str, client) -> str:
    """Analyze alert noise for selected timeframe."""
    days = _resolve_choice(session, choice)
    if not days:
        return f"Invalid selection: '{choice}'. Please reply with 1, 2, or 3."

    # Fetch top alerting servers and recent outages
    top_alerting = _safe_request(client, "GET", "/server", params={
        "limit": 10,
        "sort_by": "outage_count",
        "sort_order": "desc",
    })
    outages = _safe_request(client, "GET", "/outage", params={"limit": 25})

    session["step"] = "complete"
    result = {
        "timeframe_days": int(days),
        "top_alerting_servers": top_alerting,
        "recent_outages": outages,
    }
    return (
        f"**Alert Noise Analysis ({days} days)**\n\n"
        f"```json\n{json.dumps(result, indent=2, default=str)}\n```\n\n"
        f"Please analyze for:\n"
        f"- Flapping servers with repeated short outages\n"
        f"- High-volume alerters\n"
        f"- Threshold tuning recommendations"
    )


# ── Step Router ───────────────────────────────────────────────────

STEP_HANDLERS = {
    "select_server": _step_select_server,
    "investigate": _step_investigate,
    "assess_impact": _step_assess_impact,
    "select_group_or_all": _step_select_group_or_all,
    "review_capacity": _step_review_capacity,
    "run_audit": _step_run_audit,
    "select_timeframe": _step_select_timeframe,
    "analyze_noise": _step_analyze_noise,
}


# ── Helpers ───────────────────────────────────────────────────────

def _safe_request(client, method, path, **kwargs):
    try:
        return client._request(method, path, **kwargs)
    except Exception:
        return None


def _resolve_choice(session: dict, choice: str) -> Optional[str]:
    """Resolve a user's choice (number or direct ID) to a server_id."""
    candidates = session.get("candidates", [])
    choice = choice.strip()

    # Try as a number index
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx].get("server_id", candidates[idx].get("id"))
    except ValueError:
        pass

    # Try as a direct ID
    if choice:
        return choice

    return None


def _text(content: str) -> list:
    return [mcp.types.TextContent(type="text", text=content)]


# ── Tool Definitions ──────────────────────────────────────────────

GUIDED_SESSION_TOOL_DEFINITIONS = {

    "start_guided_session": lambda: mcp.types.Tool(
        name="start_guided_session",
        description=(
            "Start an interactive guided session for FortiMonitor workflows. "
            "Presents a menu of available workflows and walks the user through "
            "multi-step processes with choices at each step. Returns a session ID "
            "for continuing the session with continue_guided_session."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "description": (
                        "Optional: skip the menu and start a specific workflow directly. "
                        "Options: investigate-outage, change-impact, capacity-review, "
                        "alert-tuning, monitoring-audit"
                    ),
                },
            },
        },
    ),

    "continue_guided_session": lambda: mcp.types.Tool(
        name="continue_guided_session",
        description=(
            "Continue an active guided session by providing the user's choice "
            "for the current step. The server advances the workflow and returns "
            "the next step or final results."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID returned by start_guided_session.",
                },
                "choice": {
                    "type": "string",
                    "description": "The user's selection (number from the presented options, or a direct ID).",
                },
            },
            "required": ["session_id", "choice"],
        },
    ),

}


# ── Tool Handlers ─────────────────────────────────────────────────


async def handle_start_guided_session(arguments: dict, client) -> list:
    _cleanup_expired()

    session_id = str(uuid.uuid4())[:8]
    workflow = arguments.get("workflow")

    session = {
        "id": session_id,
        "workflow": workflow,
        "step_index": 0,
        "step": "menu" if not workflow else None,
        "candidates": [],
        "result": None,
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    if workflow and workflow in WORKFLOWS:
        # Skip menu, go to first step
        steps = WORKFLOWS[workflow]["steps"]
        session["step"] = steps[0]
        session["step_index"] = 0
        _sessions[session_id] = session

        handler = STEP_HANDLERS.get(session["step"])
        if handler:
            output = await handler(session, "", client)
            session["updated_at"] = time.time()
            # Advance to next step
            if session["step"] != "complete":
                session["step_index"] += 1
                if session["step_index"] < len(steps):
                    session["step"] = steps[session["step_index"]]
            return _text(output)
    else:
        _sessions[session_id] = session
        output = await _step_present_menu(session, client)
        return _text(output)

    return _text(f"Unknown workflow: '{workflow}'. Use start_guided_session without arguments to see available options.")


async def handle_continue_guided_session(arguments: dict, client) -> list:
    session_id = arguments["session_id"]
    choice = arguments["choice"]

    session = _sessions.get(session_id)
    if not session:
        return _text(
            f"Session '{session_id}' not found or expired. "
            f"Start a new session with `start_guided_session`."
        )

    if session["step"] == "complete":
        return _text("This session is complete. Start a new session with `start_guided_session`.")

    # Handle menu selection
    if session["step"] == "menu":
        choice_clean = choice.strip().lower()
        # Try by number
        try:
            idx = int(choice_clean) - 1
            wf_ids = list(WORKFLOWS.keys())
            if 0 <= idx < len(wf_ids):
                session["workflow"] = wf_ids[idx]
            else:
                return _text(f"Invalid choice '{choice}'. Please pick a number 1-{len(WORKFLOWS)}.")
        except ValueError:
            # Try by name
            if choice_clean in WORKFLOWS:
                session["workflow"] = choice_clean
            else:
                return _text(f"Unknown workflow '{choice}'. Please pick a number or workflow name.")

        steps = WORKFLOWS[session["workflow"]]["steps"]
        session["step"] = steps[0]
        session["step_index"] = 0

        handler = STEP_HANDLERS.get(session["step"])
        if handler:
            output = await handler(session, choice, client)
            session["updated_at"] = time.time()
            if session["step"] != "complete":
                session["step_index"] += 1
                if session["step_index"] < len(steps):
                    session["step"] = steps[session["step_index"]]
            return _text(output)

    # Handle workflow step
    handler = STEP_HANDLERS.get(session["step"])
    if handler:
        output = await handler(session, choice, client)
        session["updated_at"] = time.time()

        if session["step"] != "complete":
            steps = WORKFLOWS[session["workflow"]]["steps"]
            session["step_index"] += 1
            if session["step_index"] < len(steps):
                session["step"] = steps[session["step_index"]]
            else:
                session["step"] = "complete"

        return _text(output)

    return _text(f"Internal error: unknown step '{session['step']}'.")


GUIDED_SESSION_HANDLERS = {
    "start_guided_session": handle_start_guided_session,
    "continue_guided_session": handle_continue_guided_session,
}
