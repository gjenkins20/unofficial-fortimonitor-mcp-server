# FortiMonitor MCP Server — Windows Deployment Guide

**For Claude Desktop and Claude Code on Windows 10/11**
**Last Updated: February 2026**

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Method 1: Local Python with Virtual Environment (Recommended)](#3-method-1-local-python-with-virtual-environment-recommended)
4. [Method 2: Docker Container](#4-method-2-docker-container)
5. [Claude Code (CLI) Configuration](#5-claude-code-cli-configuration)
6. [Verifying Your Installation](#6-verifying-your-installation)
7. [Troubleshooting](#7-troubleshooting)
8. [Configuration Reference](#8-configuration-reference)
9. [Frequently Asked Questions](#9-frequently-asked-questions)

---

## 1. Overview

The FortiMonitor MCP Server connects Claude Desktop (or Claude Code) to the FortiMonitor (Panopta) monitoring platform through the Model Context Protocol (MCP). Once connected, Claude gains access to 241 monitoring tools spanning server management, outage handling, metrics, maintenance windows, notifications, and more.

This guide covers **Windows deployment only**. It incorporates lessons learned from real-world Windows deployment testing and addresses platform-specific issues that are not covered in the general documentation.

### 1.1 Windows-Specific Considerations

Windows deployments require special handling due to the following confirmed issues:

| Issue | Impact | Solution |
|-------|--------|----------|
| Claude Desktop ignores the `cwd` config field | Python cannot locate the `src` module | Use `cmd /c` with `cd /d` to set the working directory inline |
| System Python lacks project dependencies | Server fails with `ModuleNotFoundError` | Use a virtual environment with all dependencies installed |
| Docker Desktop must be running first | Connection fails with a named pipe error | Start Docker Desktop before launching Claude Desktop |

These issues are addressed step-by-step in this guide.

---

## 2. Prerequisites

### 2.1 Software Requirements

| Component | Minimum Version | Required For | Download |
|-----------|----------------|--------------|----------|
| Windows 10 or 11 | 64-bit | All methods | — |
| Claude Desktop | Latest | Claude Desktop integration | [claude.ai/download](https://claude.ai/download) |
| Python | 3.11+ | Local deployment (Method 1) | [python.org](https://www.python.org/downloads/) |
| Git | Any recent | Cloning the repository | [git-scm.com](https://git-scm.com/downloads) |
| Docker Desktop | Latest | Container deployment (Method 2) | [docker.com](https://www.docker.com/products/docker-desktop/) |

> **Python Installation Tip:** During Python installation, check **"Add Python to PATH"**. This ensures `python` is available from any Command Prompt or PowerShell window.

### 2.2 FortiMonitor Credentials

You need two values from your FortiMonitor account:

| Credential | Description | Example |
|------------|-------------|---------|
| `FORTIMONITOR_API_KEY` | Your FortiMonitor API key | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `FORTIMONITOR_BASE_URL` | API endpoint URL | `https://api2.panopta.com/v2` |

To find your API key, log into FortiMonitor and navigate to your account settings.

### 2.3 Claude Desktop Configuration File Location

The Claude Desktop MCP configuration file is located at:

```
%APPDATA%\Claude\claude_desktop_config.json
```

The full path is typically:

```
C:\Users\<your-username>\AppData\Roaming\Claude\claude_desktop_config.json
```

To open this location quickly, press **Win + R**, type `%APPDATA%\Claude`, and press Enter.

> **Note:** If the file does not exist, create it. If the `Claude` folder does not exist under `%APPDATA%`, launch Claude Desktop at least once first — it creates the folder on first run.

---

## 3. Method 1: Local Python with Virtual Environment (Recommended)

This is the recommended deployment method. It has fewer external dependencies than Docker and avoids the Docker Desktop startup-order requirement.

### 3.1 Clone the Repository

Open a Command Prompt or PowerShell window and run:

```powershell
cd C:\Users\<your-username>\Documents\Programming
git clone <repository-url> fortimonitor_mcp_server_claude
cd fortimonitor_mcp_server_claude
```

Replace `<repository-url>` with the actual repository URL provided by your team.

### 3.2 Create and Configure the Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
deactivate
```

This creates a `.venv` folder inside the project directory containing Python and all required dependencies (MCP SDK, requests, pydantic, etc.).

### 3.3 Configure Claude Desktop

Open the configuration file:

```
%APPDATA%\Claude\claude_desktop_config.json
```

Replace the entire contents with the following, substituting your username and API key:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "cmd",
      "args": [
        "/c",
        "cd /d C:\\Users\\<your-username>\\Documents\\Programming\\fortimonitor_mcp_server_claude && .venv\\Scripts\\python.exe -m src.server"
      ],
      "env": {
        "FORTIMONITOR_API_KEY": "<your-api-key>",
        "FORTIMONITOR_BASE_URL": "https://api2.panopta.com/v2"
      }
    }
  }
}
```

**You must change two values:**
1. Replace `<your-username>` with your Windows username
2. Replace `<your-api-key>` with your FortiMonitor API key

### 3.4 Why This Configuration Works

This configuration addresses two Windows-specific issues simultaneously:

- **`cmd /c` with `cd /d`** — Changes to the project directory before launching Python. This is required because Claude Desktop does not reliably apply the `cwd` configuration field on Windows. Without this, Python cannot find the `src` module.

- **`.venv\Scripts\python.exe`** — Uses the virtual environment's Python interpreter, which has the MCP SDK and all project dependencies installed. Using the system Python (`python.exe`) will fail with `ModuleNotFoundError`.

> **Important:** Use double backslashes (`\\`) in the JSON file for all Windows paths. JSON requires backslash escaping. A single backslash will cause a JSON parsing error.

### 3.5 Restart Claude Desktop

After saving the configuration file:

1. **Fully close Claude Desktop.** Check the system tray (bottom-right corner near the clock) for the Claude icon. Right-click it and select **Quit** or **Exit**. If in doubt, open Task Manager (`Ctrl+Shift+Esc`) and end any `Claude` processes.
2. **Reopen Claude Desktop.**
3. Navigate to **Settings > Developer** and verify the `fortimonitor` server shows a green/connected indicator.

Proceed to [Section 6: Verifying Your Installation](#6-verifying-your-installation) to confirm everything is working.

---

## 4. Method 2: Docker Container

This method runs the MCP server inside a Docker container. Two approaches are available.

> **Prerequisite:** Docker Desktop must be installed and **running** before you open Claude Desktop. If Docker is not running, the connection will fail with a named pipe error.

### 4.1 Option A: Persistent Container (docker exec)

This approach starts a long-running container once, and Claude Desktop connects to it each session. Best for users who want the container always ready.

**Step 1 — Start the container** (run once in PowerShell):

```powershell
docker run -d --name unofficial-fortimonitor-mcp `
  -e FORTIMONITOR_API_KEY=<your-api-key> `
  -e FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2 `
  ghcr.io/gjenkins20/unofficial-fortimonitor-mcp:latest `
  tail -f /dev/null
```

**Step 2 — Configure Claude Desktop:**

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "docker",
      "args": ["exec", "-i", "unofficial-fortimonitor-mcp", "python", "-m", "src.server"]
    }
  }
}
```

**Managing the container:**

| Action | Command |
|--------|---------|
| Stop the container | `docker stop unofficial-fortimonitor-mcp` |
| Start it again | `docker start unofficial-fortimonitor-mcp` |
| Remove it entirely | `docker rm -f unofficial-fortimonitor-mcp` |
| View container logs | `docker logs unofficial-fortimonitor-mcp` |

### 4.2 Option B: Fresh Container Per Session (docker run)

This approach starts a new container each time Claude Desktop connects. No need to pre-start anything, but the initial connection is slightly slower.

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "FORTIMONITOR_API_KEY=<your-api-key>",
        "-e", "FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2",
        "ghcr.io/gjenkins20/unofficial-fortimonitor-mcp:latest",
        "python", "-m", "src.server"
      ]
    }
  }
}
```

### 4.3 Critical Docker Flags

| Flag | Purpose | Notes |
|------|---------|-------|
| `--rm` | Remove container on exit | Prevents stale containers from accumulating |
| `-i` | Keep stdin open | **Required** — MCP stdio transport needs this to communicate |
| `-e` | Set environment variable | Pass API credentials into the container |

> **Never use `-t` (TTY) or `-d` (detached) flags with `docker run` for MCP servers.** Both flags break the stdio protocol and will cause an immediate disconnection.

### 4.4 Restart Claude Desktop

Follow the same restart steps as [Section 3.5](#35-restart-claude-desktop), then proceed to [Section 6](#6-verifying-your-installation) to verify.

---

## 5. Claude Code (CLI) Configuration

If you use Claude Code (the CLI tool) instead of or in addition to Claude Desktop, the MCP server is configured differently.

### 5.1 Add the MCP Server via CLI

Run the following command from any directory:

```powershell
claude mcp add fortimonitor -- cmd /c "cd /d C:\Users\<your-username>\Documents\Programming\fortimonitor_mcp_server_claude && .venv\Scripts\python.exe -m src.server"
```

Then set the required environment variables by editing the Claude Code MCP configuration. See the Claude Code documentation for details on setting environment variables for MCP servers.

### 5.2 Using a .claude/settings.json

Alternatively, create or edit a project-level `.claude/settings.json` inside the repository:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "cmd",
      "args": [
        "/c",
        "cd /d C:\\Users\\<your-username>\\Documents\\Programming\\fortimonitor_mcp_server_claude && .venv\\Scripts\\python.exe -m src.server"
      ],
      "env": {
        "FORTIMONITOR_API_KEY": "<your-api-key>",
        "FORTIMONITOR_BASE_URL": "https://api2.panopta.com/v2"
      }
    }
  }
}
```

> The same `cmd /c` with `cd /d` pattern is required for Claude Code on Windows, just as it is for Claude Desktop.

---

## 6. Verifying Your Installation

After completing setup, confirm the server is working with these steps.

### 6.1 Check Connection Status

In Claude Desktop, go to **Settings > Developer**. The `fortimonitor` server should show a green indicator. If it shows red or "failed", see [Section 7: Troubleshooting](#7-troubleshooting).

### 6.2 Test Prompts

Try these prompts in Claude to verify the connection is active and the server is responding:

| Prompt | Expected Result |
|--------|-----------------|
| "How many servers are being monitored in FortiMonitor?" | Returns a count of monitored servers |
| "List all server groups." | Returns your server group names and IDs |
| "Show active outages." | Returns any currently active outages (or confirms there are none) |
| "Get the system health summary." | Returns an overview of your monitoring infrastructure |
| "What server templates are available?" | Returns a list of monitoring templates |

If Claude responds with monitoring data from your FortiMonitor account, the deployment is complete and working.

### 6.3 Manual Server Test (Optional)

To verify the server independently of Claude, open a Command Prompt and run:

```powershell
cd /d C:\Users\<your-username>\Documents\Programming\fortimonitor_mcp_server_claude
.venv\Scripts\python.exe -m src.server
```

If the server starts without errors and waits for input, the Python environment is correctly configured. Press `Ctrl+C` to exit.

---

## 7. Troubleshooting

### 7.1 Common Errors and Fixes

| Error / Symptom | Root Cause | Fix |
|-----------------|------------|-----|
| `ModuleNotFoundError: No module named 'src'` | Python is running from the wrong directory; the `cwd` field was ignored | Use the `cmd /c` with `cd /d` configuration pattern shown in Section 3.3 |
| `ModuleNotFoundError: No module named 'mcp'` | System Python is being used instead of the virtual environment | Change the command to use `.venv\Scripts\python.exe` instead of `python` |
| `failed to connect to docker API at npipe://...` | Docker Desktop is not running | Start Docker Desktop before opening Claude Desktop |
| Server disconnected immediately after connecting | Using `-t` or `-d` flags with `docker run` | Remove `-t` and `-d` flags; use only `--rm -i` |
| `pull access denied for unofficial-fortimonitor-mcp` | Using short image name without registry prefix | Use the full image path: `ghcr.io/gjenkins20/unofficial-fortimonitor-mcp:latest` |
| Server shows "failed" in Settings > Developer | Configuration file was not reloaded | Fully close and reopen Claude Desktop after every config change |
| JSON parse error when Claude Desktop starts | Single backslashes in file paths | Use double backslashes (`\\`) for all paths in the JSON config |
| `python is not recognized as an internal or external command` | Python is not on the system PATH | Reinstall Python and check "Add Python to PATH", or use the full path to `python.exe` |

### 7.2 Viewing Server Logs

MCP server logs for Claude Desktop on Windows are located at:

```
%APPDATA%\Claude\logs\mcp-server-fortimonitor.log
```

This log shows:
- The exact command being executed
- The MCP protocol handshake
- Any Python errors from the server process

**Always check this log first** when troubleshooting connection issues.

To quickly view the latest log entries, open PowerShell and run:

```powershell
Get-Content "$env:APPDATA\Claude\logs\mcp-server-fortimonitor.log" -Tail 50
```

### 7.3 Common Verification Steps

If the server is not connecting, work through this checklist:

1. **Is the JSON valid?** Paste your config into a JSON validator (e.g., jsonlint.com). A missing comma or unescaped backslash is the most common issue.

2. **Can the server start manually?** Run the manual test from [Section 6.3](#63-manual-server-test-optional). If this fails, the issue is with your Python environment, not Claude Desktop.

3. **Is the virtual environment set up?** Check that `.venv\Scripts\python.exe` exists inside the project folder. If not, re-run `python -m venv .venv` and `pip install -r requirements.txt`.

4. **Did you fully restart Claude Desktop?** Closing the window is not enough. Check the system tray and Task Manager for remaining processes.

5. **Are the environment variables correct?** Double-check that `FORTIMONITOR_API_KEY` is set to a valid key and `FORTIMONITOR_BASE_URL` is `https://api2.panopta.com/v2`.

---

## 8. Configuration Reference

### 8.1 Claude Desktop Configuration Fields

| Field | Description |
|-------|-------------|
| `command` | The executable to run. Use `"cmd"` on Windows for proper directory handling. |
| `args` | Arguments passed to the command. `/c` tells cmd to execute the string and exit. |
| `cwd` | Working directory. **Not reliable on Windows** — use `cmd /c` with `cd /d` instead. |
| `env` | Environment variables passed to the server process. Include API credentials here. |

### 8.2 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FORTIMONITOR_API_KEY` | Yes | — | Your FortiMonitor API key |
| `FORTIMONITOR_BASE_URL` | No | `https://api2.panopta.com/v2` | FortiMonitor API endpoint |
| `MCP_SERVER_NAME` | No | `unofficial-fortimonitor-mcp` | Server name shown in Claude |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENABLE_SCHEMA_CACHE` | No | `true` | Enable API schema caching |
| `SCHEMA_CACHE_TTL` | No | `86400` | Cache TTL in seconds (24 hours) |
| `RATE_LIMIT_REQUESTS` | No | `100` | Max API requests per period |
| `RATE_LIMIT_PERIOD` | No | `60` | Rate limit period in seconds |

### 8.3 Server Information

| Property | Value |
|----------|-------|
| Server Name | `unofficial-fortimonitor-mcp` |
| Tool Count | 241 tools |
| Transport | stdio (JSON-RPC 2.0 over stdin/stdout) |
| Python Module | `src.server` |
| Docker Image | `ghcr.io/gjenkins20/unofficial-fortimonitor-mcp:latest` |

### 8.4 Complete Validated Configuration (Copy-Paste Ready)

Replace `YOUR_USERNAME` and `YOUR_API_KEY` below, then paste into `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "cmd",
      "args": [
        "/c",
        "cd /d C:\\Users\\YOUR_USERNAME\\Documents\\Programming\\fortimonitor_mcp_server_claude && .venv\\Scripts\\python.exe -m src.server"
      ],
      "env": {
        "FORTIMONITOR_API_KEY": "YOUR_API_KEY",
        "FORTIMONITOR_BASE_URL": "https://api2.panopta.com/v2"
      }
    }
  }
}
```

---

## 9. Frequently Asked Questions

**Q: Can I use the `cwd` field instead of the `cmd /c` workaround?**
No. Claude Desktop does not reliably apply the `cwd` field on Windows. The `cmd /c` with `cd /d` pattern is the only confirmed working approach.

**Q: Can I use PowerShell instead of `cmd`?**
The validated configuration uses `cmd`. While PowerShell may work with adjustments to the command syntax, it has not been tested and is not supported by this guide.

**Q: Do I need both Python and Docker?**
No. Choose one method. Method 1 (local Python) is recommended because it has fewer dependencies. You only need Docker if you prefer container-based deployment.

**Q: How do I update the MCP server?**
Pull the latest changes from the repository, then reinstall dependencies:

```powershell
cd /d C:\Users\<your-username>\Documents\Programming\fortimonitor_mcp_server_claude
git pull
.venv\Scripts\activate
pip install -r requirements.txt
deactivate
```

Then fully restart Claude Desktop.

**Q: The server was working but stopped. What happened?**
Common causes: Windows updates restarted the machine (Docker container is no longer running), Python was updated (breaking the virtual environment), or the API key expired. Re-run the manual test from Section 6.3 to isolate the issue.

**Q: Can I run the MCP server for both Claude Desktop and Claude Code at the same time?**
Each client starts its own server process, so yes — both can run simultaneously without conflict.

**Q: Where do I report issues?**
Contact your team's FortiMonitor administrator for API credential issues. For MCP server bugs, file an issue in the project repository.
