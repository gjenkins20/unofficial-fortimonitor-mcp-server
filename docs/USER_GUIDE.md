# FortiMonitor MCP Server - End-User Guide

## Table of Contents

1. [Installation and Setup](#1-installation-and-setup)
2. [Configuration](#2-configuration)
3. [Tool Reference Catalog](#3-tool-reference-catalog)
4. [Common Workflows](#4-common-workflows)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Installation and Setup

The FortiMonitor MCP Server connects Claude Desktop (or any MCP-compatible client) to the FortiMonitor (Panopta) monitoring platform. There are two installation methods: Docker (recommended) and local Python.

### 1.1 Prerequisites

- A FortiMonitor account with an API key
- One of the following:
  - **Docker**: Docker Engine 20+ and Docker Compose v2+
  - **Local**: Python 3.11+ and pip

### 1.2 Docker Installation (Recommended)

Docker provides isolated, reproducible deployments with no dependency conflicts.

**Step 1: Clone the repository**

```bash
git clone <repository-url> fortimonitor-mcp-server
cd fortimonitor-mcp-server
```

**Step 2: Create environment file**

Copy the example environment file and fill in your API key:

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```
FORTIMONITOR_API_KEY=your_api_key_here
```

**Step 3: Build and start the container**

```bash
docker-compose up -d --build
```

This builds the image (Python 3.11-slim base, non-root user) and starts the container in the background.

**Step 4: Verify the container is running**

```bash
docker-compose ps
```

You should see the `fortimonitor-mcp` service with status "Up" and health "healthy".

**Step 5: Configure your MCP client**

In your Claude Desktop configuration (typically `claude_desktop_config.json`), add:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "docker",
      "args": [
        "exec", "-i", "fortimonitor-mcp",
        "python", "-m", "src.server"
      ]
    }
  }
}
```

### 1.3 Local Installation

**Step 1: Clone and enter the repository**

```bash
git clone <repository-url> fortimonitor-mcp-server
cd fortimonitor-mcp-server
```

**Step 2: Create and activate a virtual environment**

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 4: Create environment file**

```bash
cp .env.example .env
```

Edit `.env` and set your API key (see [Configuration](#2-configuration) for all options).

**Step 5: Test the server**

```bash
python -m src.server
```

The server communicates over stdio. If it starts without errors, it is working correctly. Press Ctrl+C to stop.

**Step 6: Configure your MCP client**

In your Claude Desktop configuration, add:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/fortimonitor-mcp-server"
    }
  }
}
```

### 1.4 Updating

**Docker:**
```bash
git pull
docker-compose up -d --build
```

**Local:**
```bash
git pull
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Restart your MCP client after updating.

---

## 2. Configuration

All configuration is done through environment variables, typically set in a `.env` file in the project root.

### 2.1 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FORTIMONITOR_API_KEY` | **Yes** | *(none)* | Your FortiMonitor/Panopta API key |
| `FORTIMONITOR_BASE_URL` | No | `https://api2.panopta.com/v2` | FortiMonitor API base URL |
| `MCP_SERVER_NAME` | No | `fortimonitor-mcp` | Server name reported to MCP clients |
| `MCP_SERVER_VERSION` | No | `1.0.0` | Server version reported to MCP clients |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENABLE_SCHEMA_CACHE` | No | `true` | Enable caching of API schema data |
| `SCHEMA_CACHE_DIR` | No | `cache` | Directory for cached schema files |
| `SCHEMA_CACHE_TTL` | No | `3600` | Cache time-to-live in seconds |
| `RATE_LIMIT_REQUESTS` | No | `100` | Maximum API requests per rate limit period |
| `RATE_LIMIT_PERIOD` | No | `60` | Rate limit period in seconds |

### 2.2 Example .env File

```env
# Required
FORTIMONITOR_API_KEY=your_api_key_here

# Optional overrides
FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

### 2.3 Obtaining an API Key

1. Log into your FortiMonitor dashboard
2. Navigate to Settings > API Keys
3. Generate a new API key with appropriate permissions
4. Copy the key into your `.env` file

### 2.4 Docker-Specific Configuration

When using Docker, the `.env` file is loaded automatically by docker-compose. The container includes:

- **Resource limits**: 1 CPU, 512 MB memory
- **Cache volume**: `fortimonitor-cache` mounted at `/app/cache`
- **Health check**: Automatic container health monitoring
- **Security**: Runs as non-root user `mcpuser` (UID 1000)

---

## 3. Tool Reference Catalog

The FortiMonitor MCP Server provides **241 tools** organized into the following categories. Each tool listing shows the tool name, a brief description, and its parameters. Required parameters are marked with **(required)**.

### 3.1 Server Monitoring (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_servers` | List all monitored servers. Supports filtering. | `name`, `fqdn`, `server_group`, `status`, `tags`, `limit`, `offset` |
| `get_server_details` | Get detailed information about a specific server. | `server_id` **(required)**, `full` |

### 3.2 Server Management (19 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `set_server_status` | Update a server's monitoring status (active/inactive/paused). | `server_id` **(required)**, `status` **(required)** |
| `create_server` | Create a new monitored server. | `name` **(required)**, `fqdn` **(required)**, `server_group`, `server_template`, `tags` |
| `update_server` | Update properties of an existing server. | `server_id` **(required)**, `name`, `description`, `status`, `tags` |
| `delete_server` | Delete a monitored server permanently. | `server_id` **(required)** |
| `get_server_availability` | Get server uptime data for a time range. | `server_id` **(required)**, `start_time` **(required)**, `end_time` **(required)** |
| `get_server_outages` | Get outages for a specific server. | `server_id` **(required)**, `limit` |
| `list_server_attributes` | List custom key-value attributes on a server. | `server_id` **(required)** |
| `create_server_attribute` | Create a custom attribute on a server. | `server_id` **(required)**, `name` **(required)**, `value` **(required)** |
| `update_server_attribute` | Update value of an existing server attribute. | `server_id` **(required)**, `attribute_id` **(required)**, `value` **(required)** |
| `delete_server_attribute` | Delete a custom attribute from a server. | `server_id` **(required)**, `attribute_id` **(required)** |
| `list_server_logs` | List recent log entries for a server. | `server_id` **(required)**, `limit` |
| `create_server_log` | Add a log entry to a server. | `server_id` **(required)**, `entry` **(required)** |
| `create_custom_incident` | Manually create an incident on a server. | `server_id` **(required)**, `description` **(required)**, `severity` |
| `flush_server_dns` | Flush the DNS cache for a server. | `server_id` **(required)** |
| `list_server_path_monitoring` | List path monitoring configurations for a server. | `server_id` **(required)**, `limit` |
| `create_server_path_monitoring` | Create a new path monitoring configuration. | `server_id` **(required)**, `name` |
| `delete_server_path_monitoring` | Delete a path monitoring configuration. | `server_id` **(required)**, `path_monitoring_id` **(required)** |
| `get_path_monitoring_results` | Get results for a path monitoring configuration. | `server_id` **(required)**, `path_monitoring_id` **(required)** |
| `get_server_network_services` | List network services monitored on a server. | `server_id` **(required)**, `limit` |

### 3.3 Server Search and Bulk Operations (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_servers_advanced` | Search servers with multiple criteria. | `name_contains`, `status`, `tags`, `has_active_outages`, `limit` |
| `get_servers_with_active_outages` | Get servers currently experiencing outages. | `severity`, `limit` |
| `bulk_acknowledge_outages` | Acknowledge multiple outages at once. | `outage_ids` **(required)**, `note` |
| `bulk_add_tags` | Add tags to multiple servers at once. | `server_ids` **(required)**, `tags` **(required)** |
| `bulk_remove_tags` | Remove tags from multiple servers at once. | `server_ids` **(required)**, `tags` **(required)** |

### 3.4 Outage Monitoring (4 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_outages` | Query outages with filters. | `server_id`, `severity`, `status`, `active_only`, `hours_back`, `limit` |
| `check_server_health` | Check if a server is currently experiencing issues. | `server_id` **(required)** |
| `list_active_outages` | List only currently active outages. | `server_id`, `limit` |
| `list_resolved_outages` | List resolved (no longer active) outages. | `server_id`, `limit` |

### 3.5 Outage Management (13 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `acknowledge_outage` | Acknowledge an active outage. | `outage_id` **(required)**, `note` |
| `add_outage_note` | Add a note to an outage. | `outage_id` **(required)**, `note` **(required)** |
| `get_outage_details` | Get detailed information about an outage. | `outage_id` **(required)** |
| `broadcast_outage` | Broadcast a message about an outage to all contacts. | `outage_id` **(required)**, `message` **(required)** |
| `escalate_outage` | Escalate an outage to the next notification level. | `outage_id` **(required)** |
| `delay_outage` | Delay outage notifications by specified minutes. | `outage_id` **(required)**, `minutes` **(required)** |
| `force_resolve_outage` | Force resolve a manual or custom incident. | `outage_id` **(required)** |
| `set_outage_lead` | Set the lead person on an outage. | `outage_id` **(required)**, `user_url` **(required)** |
| `add_outage_summary` | Add a summary to an outage for reporting. | `outage_id` **(required)**, `summary` **(required)** |
| `set_outage_tags` | Set incident tags on an outage. | `outage_id` **(required)**, `tags` **(required)** |
| `get_outage_actions` | Get notification actions taken for an outage. | `outage_id` **(required)** |
| `list_outage_logs` | List timeline of events for an outage. | `outage_id` **(required)**, `limit` |
| `update_outage_description` | Update the description of a custom incident. | `outage_id` **(required)**, `description` **(required)** |

### 3.6 Historical Outages (1 tool)

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_historical_outage` | Create a historical outage record for reporting. | `server_id` **(required)**, `start_time` **(required)**, `end_time` **(required)**, `description`, `severity` |

### 3.7 Metrics and Agent Resources (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_server_metrics` | Retrieve agent resource metrics for a server. | `server_id` **(required)**, `limit` |
| `list_agent_resource_types` | List all available metric types (CPU, memory, disk, etc.). | `limit` |
| `get_agent_resource_type_details` | Get details about a specific metric type. | `type_id` **(required)** |
| `list_server_resources` | List agent resources being monitored on a server. | `server_id` **(required)**, `limit` |
| `get_resource_details` | Get detailed info about a specific agent resource. | `server_id` **(required)**, `resource_id` **(required)** |
| `get_agent_resource_details` | Get detailed agent resource info including thresholds. | `server_id` **(required)**, `resource_id` **(required)** |

### 3.8 Agent Resource Metrics (1 tool)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_agent_resource_metric` | Get time-series metric graph data for an agent resource. | `server_id` **(required)**, `resource_id` **(required)**, `timescale` |

### 3.9 Agent Resource Thresholds (3 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_agent_resource_threshold` | Get threshold details for an agent resource. | `server_id` **(required)**, `ar_id` **(required)**, `threshold_id` **(required)** |
| `update_agent_resource_threshold` | Update warning/critical thresholds. | `server_id` **(required)**, `ar_id` **(required)**, `threshold_id` **(required)**, `warning_threshold`, `critical_threshold`, `name` |
| `delete_agent_resource_threshold` | Delete a threshold from an agent resource. | `server_id` **(required)**, `ar_id` **(required)**, `threshold_id` **(required)** |

### 3.10 Server Groups (12 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_server_groups` | List all server groups. | `limit` |
| `get_server_group_details` | Get detailed info about a server group. | `group_id` **(required)** |
| `create_server_group` | Create a new server group. | `name` **(required)**, `description`, `server_ids` |
| `add_servers_to_group` | Add servers to an existing group. | `group_id` **(required)**, `server_ids` **(required)** |
| `remove_servers_from_group` | Remove servers from a group. | `group_id` **(required)**, `server_ids` **(required)** |
| `delete_server_group` | Delete a server group (servers are not deleted). | `group_id` **(required)** |
| `update_server_group` | Update group name and/or description. | `group_id` **(required)**, `name`, `description` |
| `list_server_group_servers` | List servers belonging to a group. | `group_id` **(required)**, `limit` |
| `apply_monitoring_policy_to_group` | Apply a template to all servers in a group. | `group_id` **(required)**, `template_id` **(required)** |
| `list_server_group_compound_services` | List compound services for a group. | `group_id` **(required)**, `limit` |
| `list_child_server_groups` | List child groups nested under a parent group. | `group_id` **(required)**, `limit` |

### 3.11 Monitoring Templates (8 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_server_templates` | List all server monitoring templates. | `limit` |
| `get_server_template_details` | Get details about a specific template. | `template_id` **(required)** |
| `apply_template_to_server` | Apply a template to a server. | `server_id` **(required)**, `template_id` **(required)** |
| `apply_template_to_group` | Apply a template to all servers in a group. | `group_id` **(required)**, `template_id` **(required)** |
| `create_server_template` | Create a new monitoring template. | `name` **(required)**, `description` |
| `update_server_template` | Update a template's name or description. | `template_id` **(required)**, `name`, `description` |
| `delete_server_template` | Delete a monitoring template. | `template_id` **(required)** |
| `reapply_server_template` | Reapply a template to all servers using it. | `template_id` **(required)** |

### 3.12 Maintenance Schedules (9 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_maintenance_window` | Schedule a maintenance window to suppress alerts. | `name` **(required)**, `server_ids` **(required)**, `duration_hours` **(required)**, `start_time`, `description` |
| `list_maintenance_windows` | List scheduled maintenance windows. | `active_only`, `limit` |
| `get_maintenance_schedule_details` | Get details about a specific maintenance schedule. | `schedule_id` **(required)** |
| `update_maintenance_schedule` | Update a maintenance schedule. | `schedule_id` **(required)**, `name`, `start_time`, `end_time` |
| `delete_maintenance_schedule` | Delete a maintenance schedule permanently. | `schedule_id` **(required)** |
| `extend_maintenance_schedule` | Extend a schedule by additional minutes. | `schedule_id` **(required)**, `minutes` **(required)** |
| `pause_maintenance_schedule` | Pause an active maintenance schedule. | `schedule_id` **(required)** |
| `resume_maintenance_schedule` | Resume a paused maintenance schedule. | `schedule_id` **(required)** |
| `terminate_maintenance_schedule` | Terminate a schedule early. | `schedule_id` **(required)** |

### 3.13 Server Maintenance Queries (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_server_maintenance_schedules` | Get maintenance schedules for a specific server. | `server_id` **(required)**, `limit` |
| `list_active_or_pending_maintenance` | List currently active or pending maintenance schedules. | `limit` |

### 3.14 Network Services (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_network_service_details` | Get details about a specific network service on a server. | `server_id` **(required)**, `network_service_id` **(required)** |
| `create_network_service` | Create a new network service (monitoring check) on a server. | `server_id` **(required)**, `network_service_type_id` **(required)**, `port`, `frequency`, `name` |
| `update_network_service` | Update an existing network service. | `server_id` **(required)**, `network_service_id` **(required)**, `port`, `frequency`, `name` |
| `delete_network_service` | Delete a network service from a server. | `server_id` **(required)**, `network_service_id` **(required)** |
| `get_network_service_response_time` | Get response time metrics for a network service. | `server_id` **(required)**, `network_service_id` **(required)**, `timescale` |

### 3.15 Network Service Types (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_network_service_types` | List all available network service types (HTTP, DNS, TCP, etc.). | `limit` |
| `get_network_service_type_details` | Get details about a specific network service type. | `type_id` **(required)** |

### 3.16 Monitoring Nodes (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_monitoring_nodes` | List all monitoring nodes (geographic check locations). | `limit` |
| `get_monitoring_node_details` | Get details about a specific monitoring node. | `node_id` **(required)** |

### 3.17 Notification Schedules (8 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_notification_schedules` | List all notification schedules. | `limit` |
| `get_notification_schedule_details` | Get details about a notification schedule. | `schedule_id` **(required)** |
| `create_notification_schedule` | Create a new notification schedule. | `name` **(required)**, `description` |
| `update_notification_schedule` | Update a notification schedule. | `schedule_id` **(required)**, `name`, `description` |
| `delete_notification_schedule` | Delete a notification schedule. | `schedule_id` **(required)** |
| `get_notification_schedule_thresholds` | Get thresholds using this schedule. | `schedule_id` **(required)**, `limit` |
| `get_notification_schedule_compound_services` | Get compound services using this schedule. | `schedule_id` **(required)**, `limit` |
| `get_notification_schedule_network_services` | Get network services using this schedule. | `schedule_id` **(required)**, `limit` |

### 3.18 Notification Schedule Associations (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_notification_schedule_servers` | Get servers using a notification schedule. | `schedule_id` **(required)**, `limit` |
| `get_notification_schedule_server_groups` | Get server groups using a notification schedule. | `schedule_id` **(required)**, `limit` |

### 3.19 Contact Groups (3 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_contact_groups` | List all contact groups. | `limit` |
| `get_contact_group_details` | Get details about a contact group. | `group_id` **(required)** |
| `create_contact_group` | Create a new contact group. | `name` **(required)**, `description` |

### 3.20 Contact Group Management (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `update_contact_group` | Update a contact group. | `group_id` **(required)**, `name`, `description` |
| `delete_contact_group` | Delete a contact group. | `group_id` **(required)** |

### 3.21 Contacts (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_contacts` | List all notification contacts. | `limit` |
| `get_contact_details` | Get details about a specific contact. | `contact_id` **(required)** |
| `create_contact` | Create a new notification contact. | `name` **(required)**, `description` |
| `update_contact` | Update a contact's name or description. | `contact_id` **(required)**, `name`, `description` |
| `delete_contact` | Delete a notification contact. | `contact_id` **(required)** |

### 3.22 Contact Methods (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_contact_info` | List contact methods (email, SMS, phone) for a contact. | `contact_id` **(required)**, `limit` |
| `get_contact_info_details` | Get details about a specific contact method. | `contact_id` **(required)**, `contact_info_id` **(required)** |
| `create_contact_info` | Add a new contact method to a contact. | `contact_id` **(required)**, `contact_type_id` **(required)**, `value` **(required)** |
| `update_contact_info` | Update a contact method. | `contact_id` **(required)**, `contact_info_id` **(required)**, `value` |
| `delete_contact_info` | Remove a contact method from a contact. | `contact_id` **(required)**, `contact_info_id` **(required)** |

### 3.23 Rotating Contacts / On-Call (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_rotating_contacts` | List all on-call rotation schedules. | `limit` |
| `get_rotating_contact_details` | Get details about a rotating contact schedule. | `rotating_contact_id` **(required)** |
| `create_rotating_contact` | Create a new on-call rotation. | `name` **(required)**, `description` |
| `update_rotating_contact` | Update a rotating contact schedule. | `rotating_contact_id` **(required)**, `name`, `description` |
| `delete_rotating_contact` | Delete a rotating contact schedule. | `rotating_contact_id` **(required)** |
| `get_rotating_contact_active` | Get the currently on-call contact. | `rotating_contact_id` **(required)** |

### 3.24 Compound Services (11 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_compound_services` | List all compound services. | `limit` |
| `create_compound_service` | Create a new compound service. | `name` **(required)**, `description`, `server_ids` |
| `get_compound_service_details` | Get details about a compound service. | `service_id` **(required)** |
| `update_compound_service` | Update a compound service. | `service_id` **(required)**, `name`, `description` |
| `delete_compound_service` | Delete a compound service. | `service_id` **(required)** |
| `list_compound_service_thresholds` | List thresholds for a compound service. | `service_id` **(required)** |
| `get_compound_service_availability` | Get availability data for a compound service. | `service_id` **(required)**, `start_time` **(required)**, `end_time` **(required)** |
| `list_compound_service_network_services` | List network services in a compound service. | `service_id` **(required)**, `limit` |
| `get_compound_service_response_time` | Get response time metrics for a compound service. | `service_id` **(required)**, `timescale` |
| `list_compound_service_outages` | List outages for a compound service. | `service_id` **(required)**, `limit` |
| `get_compound_service_network_service_details` | Get details about a network service within a compound service. | `service_id` **(required)**, `network_service_id` **(required)** |

### 3.25 Cloud Monitoring (15 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_cloud_providers` | List available cloud providers (AWS, Azure, GCP). | `limit` |
| `get_cloud_provider_details` | Get details about a cloud provider. | `provider_id` **(required)** |
| `list_cloud_credentials` | List configured cloud credentials. | `limit` |
| `create_cloud_credential` | Create a new cloud credential. | `name` **(required)**, `cloud_provider_id` **(required)**, `description` |
| `get_cloud_credential_details` | Get details about a cloud credential. | `credential_id` **(required)** |
| `update_cloud_credential` | Update a cloud credential. | `credential_id` **(required)**, `name`, `description` |
| `delete_cloud_credential` | Delete a cloud credential. | `credential_id` **(required)** |
| `run_cloud_discovery` | Trigger a cloud discovery run. | `credential_id` **(required)** |
| `list_cloud_discoveries` | List cloud discovery results. | `credential_id` **(required)**, `limit` |
| `get_cloud_discovery_details` | Get details about a cloud discovery result. | `credential_id` **(required)**, `discovery_id` **(required)** |
| `update_cloud_discovery` | Update a cloud discovery configuration. | `credential_id` **(required)**, `discovery_id` **(required)**, `name`, `description` |
| `list_cloud_regions` | List available cloud regions. | `limit` |
| `get_cloud_region_details` | Get details about a cloud region. | `region_id` **(required)** |
| `list_cloud_services` | List available cloud services (EC2, S3, RDS, etc.). | `limit` |
| `get_cloud_service_details` | Get details about a cloud service type. | `service_id` **(required)** |

### 3.26 Digital Experience Monitoring (DEM) (10 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_dem_applications` | List all DEM applications. | `limit` |
| `create_dem_application` | Create a new DEM application. | `name` **(required)**, `description` |
| `get_dem_application_details` | Get details about a DEM application. | `application_id` **(required)** |
| `update_dem_application` | Update a DEM application. | `application_id` **(required)**, `name`, `description` |
| `delete_dem_application` | Delete a DEM application. | `application_id` **(required)** |
| `list_dem_instances` | List monitoring instances for a DEM application. | `application_id` **(required)**, `limit` |
| `create_dem_instance` | Create a monitoring instance within a DEM application. | `application_id` **(required)**, `template` |
| `get_dem_locations` | Get monitoring locations for a DEM application. | `application_id` **(required)** |
| `update_dem_instance_path_monitoring` | Update path monitoring for a DEM instance. | `application_id` **(required)**, `instance_id` **(required)**, `paths` |
| `update_dem_location` | Update monitoring locations for a DEM application. | `application_id` **(required)**, `location_ids` |

### 3.27 Dashboards (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_dashboards` | List all monitoring dashboards. | `limit` |
| `get_dashboard_details` | Get details about a dashboard. | `dashboard_id` **(required)** |
| `create_dashboard` | Create a new monitoring dashboard. | `name` **(required)**, `description` |
| `update_dashboard` | Update a dashboard. | `dashboard_id` **(required)**, `name`, `description` |
| `delete_dashboard` | Delete a dashboard permanently. | `dashboard_id` **(required)** |

### 3.28 Status Pages (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_status_pages` | List all public status pages. | `limit` |
| `get_status_page_details` | Get details about a status page. | `status_page_id` **(required)** |
| `create_status_page` | Create a new public status page. | `name` **(required)**, `description` |
| `update_status_page` | Update a status page. | `status_page_id` **(required)**, `name`, `description` |
| `delete_status_page` | Delete a status page permanently. | `status_page_id` **(required)** |

### 3.29 Reporting and Analytics (7 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_system_health_summary` | Get overall system health summary. | *(none)* |
| `get_outage_statistics` | Get statistical analysis of outages. | `days` |
| `get_server_statistics` | Get server distribution statistics. | *(none)* |
| `get_top_alerting_servers` | Get servers with the most active outages. | `limit` |
| `export_servers_list` | Export server list in CSV format. | `status_filter`, `include_tags` |
| `export_outage_history` | Export outage history in CSV format. | `severity_filter` |
| `generate_availability_report` | Generate an availability/uptime report. | `days` |

### 3.30 SNMP Credentials (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_snmp_credentials` | List all SNMP credentials. | `limit` |
| `get_snmp_credential_details` | Get details about an SNMP credential. | `credential_id` **(required)** |
| `create_snmp_credential` | Create a new SNMP credential. | `name` **(required)**, `community_string`, `version`, `description` |
| `update_snmp_credential` | Update an SNMP credential. | `credential_id` **(required)**, `name`, `community_string`, `description` |
| `delete_snmp_credential` | Delete an SNMP credential. | `credential_id` **(required)** |

### 3.31 SNMP Discovery and Resources (7 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `request_snmp_discovery` | Trigger an SNMP discovery scan on a server. | `server_id` **(required)** |
| `list_server_snmp_resources` | List SNMP resources monitored on a server. | `server_id` **(required)**, `limit` |
| `get_snmp_resource_details` | Get details about a specific SNMP resource. | `server_id` **(required)**, `resource_id` **(required)** |
| `create_snmp_resource` | Create a new SNMP resource (monitored OID). | `server_id` **(required)**, `name`, `oid`, `description` |
| `update_snmp_resource` | Update an SNMP resource. | `server_id` **(required)**, `resource_id` **(required)**, `name`, `oid`, `description` |
| `delete_snmp_resource` | Delete an SNMP resource from a server. | `server_id` **(required)**, `resource_id` **(required)** |
| `get_snmp_resource_metric` | Get time-series metric data for an SNMP resource. | `server_id` **(required)**, `resource_id` **(required)**, `timescale` |

### 3.32 OnSight (7 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_onsights` | List all OnSight instances. | `limit` |
| `get_onsight_details` | Get details about an OnSight instance. | `onsight_id` **(required)** |
| `create_onsight` | Create a new OnSight instance. | `name` **(required)**, `description` |
| `update_onsight` | Update an OnSight instance. | `onsight_id` **(required)**, `name`, `description` |
| `delete_onsight` | Delete an OnSight instance. | `onsight_id` **(required)** |
| `get_onsight_countermeasures` | Get countermeasures for an OnSight instance. | `onsight_id` **(required)**, `limit` |
| `get_onsight_servers` | Get servers monitored by an OnSight instance. | `onsight_id` **(required)**, `limit` |

### 3.33 OnSight Groups (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_onsight_groups` | List all OnSight groups. | `limit` |
| `get_onsight_group_details` | Get details about an OnSight group. | `group_id` **(required)** |
| `create_onsight_group` | Create a new OnSight group. | `name` **(required)**, `description` |
| `update_onsight_group` | Update an OnSight group. | `group_id` **(required)**, `name`, `description` |
| `delete_onsight_group` | Delete an OnSight group. | `group_id` **(required)** |

### 3.34 Fabric Connections (4 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_fabric_connections` | List all fabric connections. | `limit` |
| `get_fabric_connection_details` | Get details about a fabric connection. | `connection_id` **(required)** |
| `create_fabric_connection` | Create a new fabric connection. | `name` **(required)**, `description` |
| `delete_fabric_connection` | Delete a fabric connection. | `connection_id` **(required)** |

### 3.35 Network Service Countermeasures (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_network_service_countermeasures` | List countermeasures on a network service. | `server_id` **(required)**, `ns_id` **(required)**, `limit` |
| `get_network_service_countermeasure_details` | Get details about a network service countermeasure. | `server_id` **(required)**, `ns_id` **(required)**, `cm_id` **(required)** |
| `create_network_service_countermeasure` | Create a countermeasure on a network service. | `server_id` **(required)**, `ns_id` **(required)**, `name`, `description`, `script` |
| `update_network_service_countermeasure` | Update a network service countermeasure. | `server_id` **(required)**, `ns_id` **(required)**, `cm_id` **(required)**, `name`, `description`, `script` |
| `delete_network_service_countermeasure` | Delete a network service countermeasure. | `server_id` **(required)**, `ns_id` **(required)**, `cm_id` **(required)** |

### 3.36 Threshold Countermeasures (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_threshold_countermeasures` | List countermeasures on an agent resource threshold. | `server_id` **(required)**, `ar_id` **(required)**, `threshold_id` **(required)**, `limit` |
| `get_threshold_countermeasure_details` | Get details about a threshold countermeasure. | `server_id` **(required)**, `ar_id` **(required)**, `threshold_id` **(required)**, `cm_id` **(required)** |
| `create_threshold_countermeasure` | Create a countermeasure on a threshold. | `server_id` **(required)**, `ar_id` **(required)**, `threshold_id` **(required)**, `name`, `description`, `script` |
| `update_threshold_countermeasure` | Update a threshold countermeasure. | `server_id` **(required)**, `ar_id` **(required)**, `threshold_id` **(required)**, `cm_id` **(required)**, `name`, `description`, `script` |
| `delete_threshold_countermeasure` | Delete a threshold countermeasure. | `server_id` **(required)**, `ar_id` **(required)**, `threshold_id` **(required)**, `cm_id` **(required)** |

### 3.37 Outage Countermeasures and Metadata (7 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_outage_countermeasures` | List countermeasures executed for an outage. | `outage_id` **(required)**, `limit` |
| `get_outage_countermeasure_details` | Get details about an outage countermeasure. | `outage_id` **(required)**, `cm_id` **(required)** |
| `get_outage_countermeasure_metadata` | Get countermeasure metadata for an outage. | `outage_id` **(required)** |
| `get_outage_countermeasure_output` | Get script output from outage countermeasures. | `outage_id` **(required)** |
| `list_outage_metadata` | List metadata entries for an outage. | `outage_id` **(required)** |
| `get_outage_metadata_details` | Get details about a specific outage metadata entry. | `outage_id` **(required)**, `metadata_id` **(required)** |
| `get_outage_preoutage_graph` | Get pre-outage metric data for trend analysis. | `outage_id` **(required)** |

### 3.38 User Management (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_users` | List all users in FortiMonitor. | `limit` |
| `get_user_details` | Get details about a specific user. | `user_id` **(required)** |
| `create_user` | Create a new user. | `name` **(required)**, `email` **(required)**, `role` |
| `update_user` | Update a user's name, email, or role. | `user_id` **(required)**, `name`, `email`, `role` |
| `delete_user` | Delete a user permanently. | `user_id` **(required)** |
| `get_user_addons` | Get addon information for users. | *(none)* |

### 3.39 Reference Data (13 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_account_history` | List account activity and changes. | `limit` |
| `list_contact_types` | List available contact types (email, SMS, phone, etc.). | `limit` |
| `get_contact_type_details` | Get details about a contact type. | `type_id` **(required)** |
| `list_roles` | List all available user roles. | `limit` |
| `get_role_details` | Get details about a specific role. | `role_id` **(required)** |
| `list_timezones` | List all available timezones. | `limit` |
| `get_timezone_details` | Get details about a timezone. | `timezone_id` **(required)** |
| `list_server_attribute_types` | List all server attribute types. | `limit` |
| `get_server_attribute_type_details` | Get details about a server attribute type. | `type_id` **(required)** |
| `create_server_attribute_type` | Create a new server attribute type. | `name` **(required)**, `description` |
| `update_server_attribute_type` | Update a server attribute type. | `type_id` **(required)**, `name`, `description` |
| `delete_server_attribute_type` | Delete a server attribute type. | `type_id` **(required)** |
| `create_prometheus_resource` | Create a Prometheus resource on a server. | `server_id` **(required)**, `name`, `description` |

---

## 4. Common Workflows

This section provides step-by-step examples for common monitoring tasks using the FortiMonitor MCP tools.

### 4.1 Checking Overall System Health

Start with a high-level overview, then drill into specifics:

1. **Get system health summary**: Use `get_system_health_summary` for a quick overview of total servers, active outages, and critical issues.
2. **View outage statistics**: Use `get_outage_statistics` with `days: 7` to see recent trends.
3. **Check top alerting servers**: Use `get_top_alerting_servers` to identify which servers need the most attention.

Example conversation:
> "What's the current health of our monitoring infrastructure?"
>
> Claude will call `get_system_health_summary`, then `get_top_alerting_servers` to provide a complete picture.

### 4.2 Investigating an Outage

When you receive an alert or need to investigate an issue:

1. **List active outages**: Use `list_active_outages` to see all current outages, or filter by server using `server_id`.
2. **Get outage details**: Use `get_outage_details` with the `outage_id` to see severity, timing, and status.
3. **Check the server**: Use `check_server_health` with `server_id` to get the current server status.
4. **Review outage logs**: Use `list_outage_logs` to see the timeline of events.
5. **Check pre-outage metrics**: Use `get_outage_preoutage_graph` to see what was happening before the outage started.
6. **Acknowledge**: Use `acknowledge_outage` to mark it as seen, and `add_outage_note` to document your findings.

Example conversation:
> "Show me all active outages and help me investigate the most critical one."
>
> Claude will call `list_active_outages`, identify the critical outage, call `get_outage_details`, then `list_outage_logs` and `get_outage_preoutage_graph` to provide a full investigation report.

### 4.3 Managing Maintenance Windows

When planning server maintenance:

1. **Create a maintenance window**: Use `create_maintenance_window` with the server IDs, a descriptive name, and duration in hours.
2. **Verify it was created**: Use `list_maintenance_windows` or `list_active_or_pending_maintenance` to confirm.
3. **If maintenance runs long**: Use `extend_maintenance_schedule` to add more time.
4. **If maintenance finishes early**: Use `terminate_maintenance_schedule` to resume monitoring.
5. **Temporary pause**: Use `pause_maintenance_schedule` and `resume_maintenance_schedule` if you need to temporarily resume alerts during maintenance.

Example conversation:
> "Schedule a 4-hour maintenance window for servers 101 and 102 starting now."
>
> Claude will call `create_maintenance_window` with the appropriate parameters.

### 4.4 Organizing Servers into Groups

For managing servers by function, location, or team:

1. **Create a group**: Use `create_server_group` with a descriptive name.
2. **Add servers**: Use `add_servers_to_group` with the group ID and server IDs.
3. **Apply a monitoring template**: Use `apply_monitoring_policy_to_group` to standardize monitoring across the group.
4. **View group members**: Use `list_server_group_servers` to see all servers in the group.
5. **View group details**: Use `get_server_group_details` for the group overview.

Example conversation:
> "Create a server group called 'Production Web Servers' and add servers 101, 102, and 103 to it."
>
> Claude will call `create_server_group`, then `add_servers_to_group` with the returned group ID.

### 4.5 Monitoring Server Metrics

To check server performance and resource usage:

1. **List available metrics**: Use `get_server_metrics` to see what metrics are collected for a server.
2. **Get metric details**: Use `get_agent_resource_details` for current value and threshold info.
3. **View metric history**: Use `get_agent_resource_metric` with a `timescale` (e.g., "hour", "day", "week", "month") to see trends.
4. **Adjust thresholds**: Use `update_agent_resource_threshold` to modify warning or critical thresholds.

Example conversation:
> "Show me the CPU usage trend for server 101 over the past week."
>
> Claude will call `list_server_resources` to find the CPU resource, then `get_agent_resource_metric` with `timescale: "week"`.

### 4.6 Managing Notifications and On-Call

To configure who gets alerted and when:

1. **List contacts**: Use `list_contacts` to see all notification contacts.
2. **View on-call rotation**: Use `list_rotating_contacts` to see rotation schedules.
3. **Check who's on call**: Use `get_rotating_contact_active` to see the current on-call person.
4. **List notification schedules**: Use `list_notification_schedules` to see when alerts are sent.
5. **View contact groups**: Use `list_contact_groups` to see how contacts are organized.

Example conversation:
> "Who is currently on call for our primary rotation?"
>
> Claude will call `list_rotating_contacts` to find the primary rotation, then `get_rotating_contact_active`.

### 4.7 Working with Cloud Resources

For cloud provider integrations (AWS, Azure, GCP):

1. **List providers**: Use `list_cloud_providers` to see available integrations.
2. **Add credentials**: Use `create_cloud_credential` with the provider and credential name.
3. **Run discovery**: Use `run_cloud_discovery` to scan for cloud resources.
4. **View results**: Use `list_cloud_discoveries` and `get_cloud_discovery_details` to see what was found.

### 4.8 Generating Reports

For compliance and SLA reporting:

1. **Availability report**: Use `generate_availability_report` with a number of days to see uptime percentages.
2. **Export servers**: Use `export_servers_list` for a CSV of all servers and their status.
3. **Export outage history**: Use `export_outage_history` for a CSV of all outages.
4. **Server statistics**: Use `get_server_statistics` for distribution by OS, status, and tags.
5. **Outage statistics**: Use `get_outage_statistics` for breakdown by severity and acknowledgment rates.

---

## 5. Troubleshooting

### 5.1 API Key Issues

**Symptom**: Tools return authentication errors or "401 Unauthorized" responses.

**Solutions**:
- Verify `FORTIMONITOR_API_KEY` is set correctly in your `.env` file
- Ensure there are no extra spaces or quotes around the key
- Confirm the API key has not expired in the FortiMonitor dashboard
- Check that the API key has sufficient permissions for the operations you need

### 5.2 Connection Errors

**Symptom**: Tools return connection timeouts or "Connection refused" errors.

**Solutions**:
- Verify `FORTIMONITOR_BASE_URL` is correct (default: `https://api2.panopta.com/v2`)
- Check your network connectivity and firewall rules
- If behind a proxy, ensure the proxy allows HTTPS traffic to `api2.panopta.com`
- Try increasing the timeout if responses are slow

### 5.3 Rate Limiting

**Symptom**: Tools return "429 Too Many Requests" or rate limit errors.

**Solutions**:
- Reduce the frequency of tool calls
- Increase `RATE_LIMIT_PERIOD` or decrease `RATE_LIMIT_REQUESTS` in your `.env` file
- Default is 100 requests per 60 seconds, which is sufficient for most use cases
- If using bulk operations, prefer `bulk_acknowledge_outages` and `bulk_add_tags` over individual calls

### 5.4 Docker Issues

**Symptom**: Container fails to start or MCP client cannot connect.

**Solutions**:

- **Container not starting**: Check logs with `docker-compose logs fortimonitor-mcp`
- **Health check failing**: Ensure the `.env` file exists and has valid values. Run `docker-compose restart`
- **Permission errors**: The container runs as non-root user `mcpuser`. Ensure the cache volume has correct permissions
- **Memory issues**: The container is limited to 512 MB. If you see OOM errors, increase the memory limit in `docker-compose.yml`
- **Environment variables not loaded**: Ensure you are using `docker-compose up` (which reads `.env` automatically), not manual `docker run` commands. If using `docker run`, pass `--env-file .env`

### 5.5 Tool Not Found

**Symptom**: MCP client reports "Unknown tool" errors.

**Solutions**:
- Ensure you are running the latest version of the server
- Restart the MCP client (Claude Desktop) to reload the tool list
- Check server logs for startup errors that may have prevented tool registration
- Verify the tool name exactly matches the catalog above (tool names are case-sensitive and use underscores)

### 5.6 Empty or Unexpected Responses

**Symptom**: Tools return empty data or unexpected formats.

**Solutions**:
- Verify the resource IDs you are passing exist in your FortiMonitor account
- Some write operations (create, update, delete) return a simple success confirmation rather than detailed data
- Use the corresponding "get details" or "list" tool after a write operation to verify changes
- Check that your API key has read access to the requested resources

### 5.7 Server Startup Errors

**Symptom**: The MCP server fails to start.

**Solutions**:
- Check that all Python dependencies are installed: `pip install -r requirements.txt`
- Verify Python version is 3.11 or higher: `python --version`
- Check the `.env` file exists and contains `FORTIMONITOR_API_KEY`
- Review server logs for specific error messages. Set `LOG_LEVEL=DEBUG` for more detail
- Ensure no other process is conflicting with the stdio communication

### 5.8 Logging

To enable detailed logging for debugging:

1. Set `LOG_LEVEL=DEBUG` in your `.env` file
2. Restart the server or container
3. Review logs:
   - **Docker**: `docker-compose logs -f fortimonitor-mcp`
   - **Local**: Logs appear on stderr in the terminal

Log messages include timestamps, module names, and log levels for easy filtering.
