#!/usr/bin/env python3
"""Generate PROJECT_DETAIL.pdf from structured content using fpdf2."""

import re
from fpdf import FPDF


class ProjectDetailPDF(FPDF):
    """Custom PDF with headers, footers, and styled content."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "FortiMonitor MCP Server - Project Detail", align="L")
            self.ln(4)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_page(self):
        self.add_page()
        self.ln(60)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(25, 60, 120)
        self.cell(0, 14, "FortiMonitor MCP Server", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, "Project Detail", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(12)
        self.set_draw_color(25, 60, 120)
        self.set_line_width(0.8)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(12)
        self.set_font("Helvetica", "I", 11)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 6, "A comprehensive technical overview of the project's\narchitecture, major components, novel features,\nand operational design.", align="C")
        self.ln(30)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, "Version 0.1.0 (Alpha)  |  MIT License", align="C", new_x="LMARGIN", new_y="NEXT")

    def section_heading(self, number, title):
        self.ln(6)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(25, 60, 120)
        text = f"{number}. {title}" if number else title
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(25, 60, 120)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def subsection_heading(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(50, 85, 140)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def sub_subsection_heading(self, title):
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(70, 70, 70)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bold_body_text(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet_item(self, text, indent=10):
        x = self.get_x()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(indent, 5.5, "")
        self.set_font("Helvetica", "B", 10)
        self.cell(4, 5.5, "- ")
        # Handle bold markers in bullet text
        self.set_font("Helvetica", "", 10)
        effective_width = self.w - self.r_margin - self.get_x()
        self.multi_cell(effective_width, 5.5, text)
        self.ln(1)

    def code_block(self, text, font_size=7):
        self.ln(2)
        self.set_fill_color(245, 245, 248)
        self.set_draw_color(210, 210, 215)
        lines = text.split("\n")
        # Calculate height needed
        line_h = font_size * 0.5 + 1.2
        block_h = len(lines) * line_h + 6
        # Check if we need a page break
        if self.get_y() + block_h > self.h - 25:
            self.add_page()
        start_y = self.get_y()
        self.set_font("Courier", "", font_size)
        self.set_text_color(50, 50, 50)
        # Draw background
        self.rect(10, start_y, 190, block_h, style="DF")
        self.set_y(start_y + 3)
        for line in lines:
            # Replace tabs with spaces
            line = line.replace("\t", "    ")
            self.set_x(13)
            self.cell(0, line_h, line)
            self.ln(line_h)
        self.ln(4)

    def table_header(self, cols, widths):
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(25, 60, 120)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, border=1, fill=True, align="C")
        self.ln()

    def table_row(self, cols, widths, fill=False):
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(40, 40, 40)
        if fill:
            self.set_fill_color(240, 243, 248)
        else:
            self.set_fill_color(255, 255, 255)
        max_h = 7
        for i, col in enumerate(cols):
            align = "R" if i == 2 and col.strip().isdigit() else "L"
            self.cell(widths[i], max_h, col, border=1, fill=True, align=align)
        self.ln()


def build_pdf():
    pdf = ProjectDetailPDF()
    pdf.alias_nb_pages()

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    pdf.title_page()

    # =========================================================================
    # TABLE OF CONTENTS
    # =========================================================================
    pdf.add_page()
    pdf.section_heading(None, "Table of Contents")
    toc_items = [
        ("1", "Project Overview"),
        ("2", "High-Level Architecture"),
        ("3", "Data Flow Diagram"),
        ("4", "Major Components"),
        ("", "    4.1  MCP Server Core"),
        ("", "    4.2  Configuration Manager"),
        ("", "    4.3  FortiMonitor API Client"),
        ("", "    4.4  Data Models"),
        ("", "    4.5  Schema Manager"),
        ("", "    4.6  Exception Hierarchy"),
        ("", "    4.7  Tool Modules"),
        ("", "    4.8  Docker Infrastructure"),
        ("5", "Tool Registry Architecture"),
        ("6", "Complete Tool Inventory"),
        ("7", "Novel Features"),
        ("8", "Security & Resilience Design"),
        ("9", "Deployment Architecture"),
        ("10", "Technology Stack"),
    ]
    for num, title in toc_items:
        pdf.set_font("Helvetica", "" if not num else "B", 10)
        pdf.set_text_color(40, 40, 40)
        prefix = f"{num}.  " if num else "      "
        pdf.cell(0, 7, f"{prefix}{title}", new_x="LMARGIN", new_y="NEXT")

    # =========================================================================
    # 1. PROJECT OVERVIEW
    # =========================================================================
    pdf.add_page()
    pdf.section_heading("1", "Project Overview")
    pdf.body_text(
        "The FortiMonitor MCP Server is a Python application that implements the Model Context Protocol (MCP) "
        "to bridge the FortiMonitor/Panopta infrastructure monitoring platform with Claude AI. It wraps the "
        "entire FortiMonitor REST API (200+ endpoints) into 241 conversational tools organized across 33 "
        "modules, enabling DevOps and SRE teams to manage their monitoring infrastructure through natural language."
    )

    # =========================================================================
    # 2. HIGH-LEVEL ARCHITECTURE
    # =========================================================================
    pdf.section_heading("2", "High-Level Architecture")
    pdf.body_text(
        "The system consists of three tiers: the MCP client (Claude Desktop or any MCP-compatible client), "
        "the FortiMonitor MCP Server (Python 3.9+), and the FortiMonitor/Panopta Cloud Platform. "
        "Communication between the client and server uses JSON-RPC over stdio. The server communicates "
        "with the FortiMonitor API over HTTPS using API key authentication via query parameters."
    )
    pdf.code_block(
        "+----------------------------------------------------------------------+\n"
        "|                        USER'S ENVIRONMENT                            |\n"
        "|                                                                      |\n"
        "|  +------------------+       MCP (stdio)       +-------------------+  |\n"
        "|  |                  | <---------------------> |                   |  |\n"
        "|  |  Claude Desktop  |   JSON-RPC over stdin   |  FortiMonitor     |  |\n"
        "|  |  (or any MCP     |       / stdout          |  MCP Server       |  |\n"
        "|  |   client)        |                         |  (Python 3.9+)    |  |\n"
        "|  +------------------+                         +--------+----------+  |\n"
        "|                                                        |             |\n"
        "+--------------------------------------------------------|-------------+\n"
        "                                                         |\n"
        "                                               HTTPS REST API\n"
        "                                             (api_key auth via\n"
        "                                              query parameter)\n"
        "                                                         |\n"
        "                                                         v\n"
        "                                          +------------------------------+\n"
        "                                          |  FortiMonitor / Panopta      |\n"
        "                                          |  Cloud Platform              |\n"
        "                                          |  https://api2.panopta.com/v2 |\n"
        "                                          +------------------------------+",
        font_size=6.5,
    )

    # =========================================================================
    # 3. DATA FLOW DIAGRAM
    # =========================================================================
    pdf.add_page()
    pdf.section_heading("3", "Data Flow Diagram")
    pdf.body_text(
        "The following illustrates the lifecycle of a single user request from natural language to API response. "
        "A request such as \"Show me all servers with active outages\" passes through 15 steps across 7 components:"
    )
    steps = [
        ("1.", "User speaks in natural language to Claude Desktop (MCP Client)."),
        ("2.", "Claude invokes call_tool(\"get_servers_with_active_outages\", {...}) via JSON-RPC over stdio."),
        ("3.", "MCP Server Core dispatches to the matching handler via _HANDLER_MAP lookup."),
        ("4.", "The tool handler (e.g., in bulk_operations.py) is invoked."),
        ("5.", "Handler validates arguments and transforms parameters."),
        ("6.", "Handler calls FortiMonitorClient methods (get_active_outages, get_servers, etc.)."),
        ("7.", "The API Client builds the HTTP request with retry logic, adds the API key, and sets JSON headers."),
        ("8.", "HTTPS GET request sent to https://api2.panopta.com/v2/outage/active?api_key=..."),
        ("9.", "FortiMonitor Cloud API returns a JSON response."),
        ("10.", "Raw JSON response received by the client."),
        ("11.", "Pydantic Models parse the response: URL-based ID extraction, RFC 2822 date parsing, field aliasing."),
        ("12.", "Structured data objects returned to the tool handler."),
        ("13.", "Tool handler formats results as MCP TextContent."),
        ("14.", "MCP response (List[TextContent]) sent back over stdio."),
        ("15.", "Claude presents a natural language summary to the user."),
    ]
    for num, text in steps:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(12, 5.5, num)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        effective_w = pdf.w - pdf.r_margin - pdf.get_x()
        pdf.multi_cell(effective_w, 5.5, text)
        pdf.ln(1)

    # =========================================================================
    # 4. MAJOR COMPONENTS
    # =========================================================================
    pdf.add_page()
    pdf.section_heading("4", "Major Components")

    # 4.1 MCP Server Core
    pdf.subsection_heading("4.1  MCP Server Core (src/server.py)")
    pdf.body_text(
        "The central orchestrator that wires together the MCP protocol, tool registry, and API client. "
        "The FortiMonitorMCPServer class creates an MCP Server instance, registers protocol handlers for "
        "list_tools() and call_tool(), and manages the server lifecycle."
    )
    pdf.sub_subsection_heading("Key Design Decisions")
    pdf.bullet_item(
        "Lazy client initialization - The FortiMonitorClient is not instantiated until the first tool call, "
        "avoiding startup failures if the API key is missing or the API is unreachable."
    )
    pdf.bullet_item(
        "Module-level registry build - _build_registry() runs once at import time, producing a flat list "
        "and lookup dictionary for O(1) tool dispatch."
    )
    pdf.sub_subsection_heading("Registry Build Process")
    pdf.body_text(
        "The _build_registry() function aggregates tools from two registration patterns:"
    )
    pdf.bullet_item("Pattern A (Tuple): 44 tools from 11 original modules via (definition_func, handler_func) pairs.")
    pdf.bullet_item("Pattern B (Dict): 197 tools from 22 enhanced modules via {name: func} dictionaries.")
    pdf.body_text(
        "Output: _TOOL_DEFINITIONS (List[Tool], 241 entries) and _HANDLER_MAP (Dict[str, Callable], 241 entries)."
    )

    # 4.2 Configuration Manager
    pdf.subsection_heading("4.2  Configuration Manager (src/config.py)")
    pdf.body_text(
        "Centralized configuration using Pydantic Settings with environment variable and .env file support. "
        "The Settings class (BaseSettings) loads configuration from three sources in priority order: "
        "environment variables, .env file, and default values."
    )
    config_items = [
        ("FortiMonitor API", "fortimonitor_base_url (HttpUrl), fortimonitor_api_key (str, required)"),
        ("MCP Server", "mcp_server_name (str), mcp_server_version (str), log_level (str)"),
        ("Schema Caching", "enable_schema_cache (bool), schema_cache_dir (Path), schema_cache_ttl (int, 86400s)"),
        ("Rate Limiting", "rate_limit_requests (int, 100), rate_limit_period (int, 60s)"),
    ]
    for group, fields in config_items:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(50, 85, 140)
        pdf.cell(0, 6, group, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(10, 5, "")
        pdf.cell(0, 5, fields, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # 4.3 API Client
    pdf.add_page()
    pdf.subsection_heading("4.3  FortiMonitor API Client (src/fortimonitor/client.py)")
    pdf.body_text(
        "The HTTP client that handles all communication with the FortiMonitor REST API. Built on "
        "requests.Session with automatic retry logic, the client provides ~40 typed methods organized by domain."
    )
    client_domains = [
        ("Server Operations (6 methods)", "get_servers, get_server_details, update_server_status, update_server, etc."),
        ("Outage Operations (5 methods)", "get_outages, get_active_outages, acknowledge_outage, add_outage_log, get_outage_details"),
        ("Maintenance Operations (5 methods)", "create/list/get/update/delete_maintenance_schedule"),
        ("Server Group Operations (8 methods)", "CRUD + add/remove_servers_from_group, get_group_members_complete"),
        ("Template Operations (3 methods)", "list/get_server_templates, apply_template_to_server"),
        ("Notification Operations (5 methods)", "list/get notification_schedules, contact_groups, contacts"),
        ("Agent Resource Operations (3 methods)", "list_agent_resource_types, get details, list_server_agent_resources"),
    ]
    for domain, methods in client_domains:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(50, 85, 140)
        pdf.cell(0, 6, domain, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 7.5)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(10, 5, "")
        pdf.multi_cell(0, 5, methods)
        pdf.ln(1)

    pdf.sub_subsection_heading("Retry Architecture")
    pdf.body_text(
        "The client implements dual-layer retry with exponential backoff:"
    )
    pdf.bullet_item("Application-level: Custom retry loop in _request() with 3 attempts and exponential backoff (1s, 2s, 4s) for 500 errors and connection failures.")
    pdf.bullet_item("Transport-level: requests.HTTPAdapter with urllib3.Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]).")
    pdf.ln(2)
    pdf.body_text("HTTP status code mapping:")
    status_maps = [
        ("2xx", "Return parsed JSON"),
        ("401", "Raise AuthenticationError"),
        ("404", "Raise NotFoundError"),
        ("429", "Raise RateLimitError"),
        ("500", "Retry with backoff; raise APIError after 3 failures"),
        ("Other 4xx", "Raise APIError"),
        ("ConnectionError", "Retry with backoff"),
    ]
    for code, action in status_maps:
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(30, 5.5, code)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 5.5, action, new_x="LMARGIN", new_y="NEXT")

    # 4.4 Data Models
    pdf.add_page()
    pdf.subsection_heading("4.4  Data Models (src/fortimonitor/models.py)")
    pdf.body_text(
        "Approximately 50 Pydantic models that parse and validate FortiMonitor API responses. Models are "
        "organized into domain groups:"
    )
    model_groups = [
        "Core: Server, Outage, AgentResource, PaginationMeta",
        "Scheduling: MaintenanceWindow",
        "Organization: ServerGroup, ServerTemplate",
        "Alerting: NotificationSchedule, ContactGroup, Contact",
        "Cloud: CloudProvider, CloudCredential, CloudDiscovery, CloudRegion, CloudService",
        "DEM: DEMApplication, DEMInstance",
        "Dependencies: CompoundService, AgentResourceThreshold",
        "Network: NetworkService",
        "Detail: OutageLog, OutageAction, OutageNote, ServerAttribute, ServerLog",
        "Each model has a corresponding *ListResponse wrapper with PaginationMeta",
    ]
    for g in model_groups:
        pdf.bullet_item(g)

    pdf.sub_subsection_heading("URL-Based ID Extraction Pattern")
    pdf.body_text(
        "The FortiMonitor API returns resource identifiers as full URL strings "
        "(e.g., https://api2.panopta.com/v2/server/12345). Every Pydantic model provides an @property "
        "method that extracts the integer ID from the URL tail. This pattern is applied uniformly across "
        "Server.id, Outage.id, ServerGroup.id, Contact.id, CloudProvider.id, DEMApplication.id, "
        "NetworkService.id, and all other resource models."
    )
    pdf.sub_subsection_heading("RFC 2822 Date Normalization")
    pdf.body_text(
        "The API uses RFC 2822 date format (e.g., \"Thu, 12 Dec 2024 01:33:48 -0000\"). All datetime "
        "fields use a @field_validator that calls email.utils.parsedate_to_datetime() to convert these "
        "into standard Python datetime objects with timezone awareness."
    )

    # 4.5 Schema Manager
    pdf.subsection_heading("4.5  Schema Manager (src/fortimonitor/schema.py)")
    pdf.body_text(
        "Runtime API schema discovery with a two-tier caching strategy. The SchemaManager fetches live "
        "schema definitions from FortiMonitor's /schema/resources endpoint and provides parameter validation "
        "against the actual API contract."
    )
    pdf.sub_subsection_heading("Caching Strategy (3 tiers)")
    pdf.bullet_item("Tier 1 - In-memory cache: Checked first. Instant return if populated.")
    pdf.bullet_item("Tier 2 - File cache: JSON files in cache/schemas/ with configurable TTL (default 24h). Loaded into memory on hit.")
    pdf.bullet_item("Tier 3 - API fetch: GET /schema/resources/{name}. Result saved to both file and memory caches.")

    # 4.6 Exception Hierarchy
    pdf.ln(2)
    pdf.subsection_heading("4.6  Exception Hierarchy (src/fortimonitor/exceptions.py)")
    pdf.body_text("Custom exceptions for granular error handling:")
    pdf.code_block(
        "FortiMonitorError (base)\n"
        "    |\n"
        "    +-- AuthenticationError      HTTP 401\n"
        "    |\n"
        "    +-- APIError                 HTTP 4xx/5xx (generic)\n"
        "    |     |\n"
        "    |     +-- NotFoundError      HTTP 404\n"
        "    |     |\n"
        "    |     +-- RateLimitError     HTTP 429\n"
        "    |\n"
        "    +-- ValidationError          Invalid request parameters\n"
        "    |\n"
        "    +-- SchemaError              Schema fetch/parse failures",
        font_size=8,
    )

    # 4.7 Tool Modules
    pdf.add_page()
    pdf.subsection_heading("4.7  Tool Modules (src/tools/)")
    pdf.body_text(
        "The largest part of the codebase: 33 Python files containing 241 tool definitions and their "
        "async handler functions. Tools are organized into 4 implementation phases:"
    )

    phases = [
        ("Phase 1: Core Monitoring (Tuple Pattern) - 44 tools", [
            "servers.py (2), outages.py (2), metrics.py (1), outage_management.py (3)",
            "server_management.py (3), bulk_operations.py (5), server_groups.py (8)",
            "templates.py (4), notifications.py (5), agent_resources.py (4), reporting.py (7)",
        ]),
        ("Phase 1 Enhanced (Dict Pattern) - 49 tools", [
            "outage_enhanced.py (13), server_enhanced.py (19), maintenance_enhanced.py (9)",
            "server_groups_enhanced.py (4), templates_enhanced.py (4)",
        ]),
        ("Phase 2: Extended Monitoring (Dict Pattern) - 36 tools", [
            "cloud.py (15), dem.py (10), compound_services.py (11)",
        ]),
        ("Phase 3: Platform Management (Dict Pattern) - 67 tools", [
            "dashboards.py (5), status_pages.py (5), rotating_contacts.py (6)",
            "contacts_enhanced.py (12), notifications_enhanced.py (8), network_services.py (5)",
            "monitoring_nodes.py (2), network_service_types.py (2), snmp.py (12)",
            "fabric.py (4), countermeasures.py (20)",
        ]),
        ("Phase 4: Administration (Dict Pattern) - 31 tools", [
            "users.py (6), reference_data.py (13), onsight.py (12)",
        ]),
    ]
    for phase_title, modules in phases:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(0, 7, phase_title, new_x="LMARGIN", new_y="NEXT")
        for mod_line in modules:
            pdf.set_font("Courier", "", 7.5)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(10, 5, "")
            pdf.cell(0, 5, mod_line, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.sub_subsection_heading("Tool Handler Pattern")
    pdf.body_text("Every tool handler follows the same async signature and pattern:")
    pdf.code_block(
        "async def handle_tool_name(arguments: dict, client: FortiMonitorClient) -> List[TextContent]:\n"
        "    # 1. Extract and validate arguments\n"
        "    # 2. Call client method(s)\n"
        "    # 3. Format response as human-readable text\n"
        "    # 4. Return [TextContent(type=\"text\", text=formatted_result)]",
        font_size=8,
    )

    # 4.8 Docker Infrastructure
    pdf.subsection_heading("4.8  Docker Infrastructure")
    pdf.sub_subsection_heading("Multi-Stage Build")
    pdf.bullet_item("Stage 1 (builder): python:3.11-slim with gcc. Filters dev dependencies, installs production deps only.")
    pdf.bullet_item("Stage 2 (runtime): python:3.11-slim with ca-certificates. Non-root user mcpuser (UID 1000). CMD: tail -f /dev/null (keep-alive pattern).")

    pdf.sub_subsection_heading("Docker Compose Configuration")
    pdf.bullet_item("Named volume: fortimonitor-cache for schema persistence across restarts.")
    pdf.bullet_item("Resource limits: 1 CPU, 512MB RAM. Reservations: 0.25 CPU, 128MB RAM.")
    pdf.bullet_item("Security: no-new-privileges, restart unless-stopped.")
    pdf.bullet_item("Logging: json-file driver, 10MB max size, 3 file rotation.")
    pdf.bullet_item("Health check: every 60s, 10s timeout, verifies configuration loads.")
    pdf.bullet_item("stdin_open: true (required for MCP stdio protocol).")

    pdf.sub_subsection_heading("Invocation Pattern")
    pdf.body_text(
        "The container stays alive via tail -f /dev/null. The MCP server is invoked on-demand per Claude "
        "session via: docker exec -i unofficial-fortimonitor-mcp python -m src.server. This enables instant session "
        "startup without container restart overhead."
    )

    # =========================================================================
    # 5. TOOL REGISTRY ARCHITECTURE
    # =========================================================================
    pdf.add_page()
    pdf.section_heading("5", "Tool Registry Architecture")
    pdf.body_text(
        "The registry unifies two registration patterns into a single dispatch table. The _build_registry() "
        "function runs at module load time and processes both the Tuple pattern (11 original modules, 44 tools) "
        "and the Dict pattern (22 enhanced modules, 197 tools) to produce:"
    )
    pdf.bullet_item("_TOOL_DEFINITIONS: List[Tool] with 241 entries for MCP list_tools() responses.")
    pdf.bullet_item("_HANDLER_MAP: Dict[str, Callable] with 241 entries for O(1) tool dispatch.")
    pdf.ln(2)
    pdf.body_text("At runtime, @server.call_tool() performs a simple dictionary lookup: handler = _HANDLER_MAP.get(name), then awaits the handler with arguments and the client instance.")

    # =========================================================================
    # 6. COMPLETE TOOL INVENTORY
    # =========================================================================
    pdf.add_page()
    pdf.section_heading("6", "Complete Tool Inventory")
    pdf.body_text("All 241 tools organized by category:")
    pdf.ln(2)

    widths = [32, 55, 12, 91]
    pdf.table_header(["Category", "Module(s)", "Count", "Key Operations"], widths)

    inventory = [
        ("Servers", "servers, server_enhanced", "21", "List, detail, CRUD, attributes, logs, DNS"),
        ("Outages", "outages, outage_mgmt, outage_enh", "18", "List, acknowledge, escalate, broadcast, delay"),
        ("Maintenance", "server_mgmt, maintenance_enh", "12", "Create, update, extend, pause, active/pending"),
        ("Server Groups", "server_groups, groups_enh", "12", "CRUD, member mgmt, policy, compound svcs"),
        ("Templates", "templates, templates_enh", "8", "List, detail, create, update, delete, apply"),
        ("Notifications", "notifications, notif_enh", "13", "Schedule CRUD, sub-resource queries"),
        ("Contacts", "contacts_enh, rotating_contacts", "18", "Contact CRUD, contact_info, on-call"),
        ("Agent Resources", "agent_resources", "4", "Types, server resources, details"),
        ("Metrics/Reports", "metrics, reporting", "8", "Health summary, stats, exports, availability"),
        ("Cloud", "cloud", "15", "Providers, credentials, discovery, regions"),
        ("DEM", "dem", "10", "Applications, instances, locations, paths"),
        ("Compound Svcs", "compound_services", "11", "CRUD, thresholds, availability"),
        ("Dashboards", "dashboards", "5", "Dashboard CRUD"),
        ("Status Pages", "status_pages", "5", "Status page CRUD"),
        ("Network Svcs", "network_services, nst", "7", "Server network service CRUD, types"),
        ("Monitor Nodes", "monitoring_nodes", "2", "List, detail"),
        ("SNMP", "snmp", "12", "Credentials, discovery, resources"),
        ("OnSight", "onsight", "12", "OnSight CRUD, groups, countermeasures"),
        ("Fabric", "fabric", "4", "Fabric connection CRUD"),
        ("Countermeasures", "countermeasures", "20", "Countermeasures, thresholds, metadata"),
        ("Users", "users", "6", "User CRUD, addons"),
        ("Reference Data", "reference_data", "13", "Account history, types, roles, timezones"),
        ("Bulk Operations", "bulk_operations", "5", "Bulk acknowledge, tags, advanced search"),
        ("TOTAL", "", "241", ""),
    ]
    for i, (cat, mod, count, ops) in enumerate(inventory):
        is_last = i == len(inventory) - 1
        if is_last:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(230, 235, 245)
            pdf.set_text_color(25, 60, 120)
            pdf.cell(widths[0], 7, cat, border=1, fill=True, align="L")
            pdf.cell(widths[1], 7, mod, border=1, fill=True, align="C")
            pdf.cell(widths[2], 7, count, border=1, fill=True, align="R")
            pdf.cell(widths[3], 7, ops, border=1, fill=True, align="C")
            pdf.ln()
        else:
            pdf.table_row([cat, mod, count, ops], widths, fill=(i % 2 == 0))

    # =========================================================================
    # 7. NOVEL FEATURES
    # =========================================================================
    pdf.add_page()
    pdf.section_heading("7", "Novel Features")
    pdf.body_text(
        "These are capabilities newly provided by this project that did not previously exist:"
    )

    novel_features = [
        ("1. Conversational Infrastructure Monitoring",
         "No prior tool allowed an operator to ask, in plain English, something like \"Show me the top 5 "
         "servers by outage count this month, then create a maintenance window for the worst one.\" This "
         "project makes the entire FortiMonitor API surface available through natural language."),
        ("2. Transparent URL-ID Abstraction",
         "FortiMonitor's API returns resource identifiers as full URL strings. This project transparently "
         "extracts integer IDs via @property methods on every model, so users and tool handlers work with "
         "simple numbers while the client constructs URLs automatically."),
        ("3. RFC 2822 Date Normalization",
         "The FortiMonitor API uses RFC 2822 date format which is uncommon in modern REST APIs. The project's "
         "Pydantic validators automatically parse these into standard Python datetime objects."),
        ("4. Runtime API Schema Discovery",
         "The SchemaManager fetches live schema definitions from FortiMonitor's /schema/resources endpoint "
         "and caches them locally, enabling parameter validation against the actual API contract at runtime."),
        ("5. Dual-Layer Retry with Exponential Backoff",
         "Two independent retry mechanisms: application-level (custom loop with 1s/2s/4s backoff) and "
         "transport-level (requests.HTTPAdapter with urllib3.Retry for 429/5xx)."),
        ("6. Keep-Alive Container Pattern",
         "The Dockerfile uses tail -f /dev/null to keep the container alive as a persistent sidecar. The MCP "
         "server is invoked on-demand via docker exec, enabling instant session startup."),
        ("7. Complete API Coverage in a Single MCP Server",
         "With 241 tools across 33 modules, this covers virtually 100% of the FortiMonitor v2 API surface. "
         "Most MCP servers expose a handful of tools; this demonstrates enterprise-scale coverage."),
        ("8. Composite Operations",
         "Several tools compose multiple API calls into higher-level operations: "
         "get_servers_with_active_outages correlates outages with server details; "
         "get_group_members_complete combines 3+ API calls; reporting tools aggregate across endpoints."),
    ]
    for title, desc in novel_features:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        pdf.body_text(desc)

    # =========================================================================
    # 8. SECURITY & RESILIENCE DESIGN
    # =========================================================================
    pdf.add_page()
    pdf.section_heading("8", "Security & Resilience Design")

    security_layers = [
        ("Container Level", [
            "Non-root user (mcpuser, UID 1000)",
            "no-new-privileges security option",
            "Resource limits (1 CPU, 512MB RAM)",
            "JSON file logging with rotation (10MB x 3 files)",
        ]),
        ("Network Level", [
            "HTTPS only for API communication",
            "API key passed as query parameter (per FortiMonitor specification)",
            "No ports exposed by container",
            "stdio transport only (no HTTP server exposed)",
        ]),
        ("Application Level", [
            "Pydantic validation on all inputs and outputs",
            "Custom exception hierarchy with HTTP status code mapping",
            "Rate limiting configuration (100 requests/60 seconds default)",
            "Structured logging via structlog for audit trail",
        ]),
        ("Resilience", [
            "Dual-layer retry (application + transport)",
            "Exponential backoff (1s, 2s, 4s)",
            "30-second request timeout",
            "Graceful shutdown (client.close() in finally block)",
            "Health checks every 60 seconds",
            "Schema cache with configurable TTL",
        ]),
    ]
    for layer_name, items in security_layers:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(0, 8, layer_name, new_x="LMARGIN", new_y="NEXT")
        for item in items:
            pdf.bullet_item(item, indent=6)
        pdf.ln(2)

    # =========================================================================
    # 9. DEPLOYMENT ARCHITECTURE
    # =========================================================================
    pdf.add_page()
    pdf.section_heading("9", "Deployment Architecture")

    pdf.subsection_heading("Option A: Docker (Recommended)")
    pdf.body_text(
        "Claude Desktop communicates with the MCP server running inside a Docker container via "
        "docker exec -i. The container stays alive as a persistent sidecar."
    )
    pdf.code_block(
        'claude_desktop_config.json:\n'
        '{\n'
        '  "mcpServers": {\n'
        '    "fortimonitor": {\n'
        '      "command": "docker",\n'
        '      "args": ["exec", "-i", "unofficial-fortimonitor-mcp",\n'
        '               "python", "-m", "src.server"]\n'
        '    }\n'
        '  }\n'
        '}',
        font_size=8,
    )

    pdf.subsection_heading("Option B: Local Python")
    pdf.body_text(
        "Claude Desktop spawns the MCP server as a direct child process. Simpler setup but "
        "lacks container isolation and resource limits."
    )
    pdf.code_block(
        'claude_desktop_config.json:\n'
        '{\n'
        '  "mcpServers": {\n'
        '    "fortimonitor": {\n'
        '      "command": "python",\n'
        '      "args": ["-m", "src.server"],\n'
        '      "cwd": "/path/to/unofficial-fortimonitor-mcp-server",\n'
        '      "env": {\n'
        '        "FORTIMONITOR_API_KEY": "your_key_here"\n'
        '      }\n'
        '    }\n'
        '  }\n'
        '}',
        font_size=8,
    )

    # =========================================================================
    # 10. TECHNOLOGY STACK
    # =========================================================================
    pdf.section_heading("10", "Technology Stack")

    widths_ts = [40, 62, 88]
    pdf.table_header(["Layer", "Technology", "Purpose"], widths_ts)

    tech_stack = [
        ("Runtime", "Python 3.9+", "Primary language"),
        ("MCP Protocol", "mcp >= 0.9.0", "Claude AI integration via Model Context Protocol"),
        ("Data Validation", "Pydantic >= 2.5.0", "Request/response models, environment config"),
        ("HTTP Client", "requests >= 2.31.0", "FortiMonitor API communication"),
        ("Date Parsing", "python-dateutil >= 2.8.2", "RFC 2822 datetime handling"),
        ("Logging", "structlog >= 23.2.0", "Structured logging"),
        ("Environment", "python-dotenv >= 1.0.0", ".env file loading"),
        ("Containerization", "Docker, Docker Compose", "Production deployment"),
        ("CI/CD", "GitHub Actions", "Multi-arch builds to Docker Hub and GHCR"),
        ("Testing", "pytest, pytest-asyncio", "Unit and integration tests"),
        ("Quality", "black, flake8, mypy", "Formatting, linting, type checking"),
    ]
    for i, (layer, tech, purpose) in enumerate(tech_stack):
        pdf.table_row([layer, tech, purpose], widths_ts, fill=(i % 2 == 0))

    # =========================================================================
    # OUTPUT
    # =========================================================================
    output_path = "/Users/gregorijenkins/Programming/unofficial-fortimonitor-mcp-server/docs/PROJECT_DETAIL.pdf"
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    build_pdf()
