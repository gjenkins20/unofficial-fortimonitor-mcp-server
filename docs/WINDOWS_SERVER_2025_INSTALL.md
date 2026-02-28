# FortiMonitor MCP Server - Windows Server 2025 Installation Guide

## Proof of Concept Deployment

This guide covers installing and configuring the FortiMonitor MCP Server on Windows Server 2025 with Claude Code already installed.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install Python](#install-python)
3. [Install Git](#install-git)
4. [Clone the Repository](#clone-the-repository)
5. [Configure the Environment](#configure-the-environment)
6. [Install Dependencies](#install-dependencies)
7. [Verify the Installation](#verify-the-installation)
8. [Configure Claude Code Integration](#configure-claude-code-integration)
9. [Running the Server](#running-the-server)
10. [Docker Alternative](#docker-alternative)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, confirm the following:

| Requirement              | Details                                       |
|--------------------------|-----------------------------------------------|
| Operating System         | Windows Server 2025                           |
| Claude Code              | Already installed and functional               |
| Network Access           | Outbound HTTPS to `api2.panopta.com`           |
| Network Access           | Outbound HTTPS to `github.com`                 |
| FortiMonitor API Key     | Obtained from your FortiMonitor account        |
| Administrator Access     | Required for software installation             |

---

## Step 1: Install Python

Python 3.9 or higher is required. Python 3.11 is recommended.

### Option A: Download from python.org

1. Open a browser and navigate to:
   ```
   https://www.python.org/downloads/windows/
   ```

2. Download the latest **Python 3.11.x** Windows installer (64-bit).

3. Run the installer. **Check both of these options:**
   - "Add python.exe to PATH"
   - "Use admin privileges when installing py.exe"

4. Click **"Install Now"** (or customize the install location if needed).

### Option B: Install via winget (if available)

Open **PowerShell as Administrator** and run:

```powershell
winget install Python.Python.3.11
```

### Verify Python installation

Open a **new** PowerShell window and run:

```powershell
python --version
pip --version
```

Expected output (versions may vary):
```
Python 3.11.x
pip 24.x.x from ...
```

> **Note:** If `python` is not recognized, close and reopen PowerShell to pick up the updated PATH, or manually add `C:\Users\<user>\AppData\Local\Programs\Python\Python311\` and its `Scripts\` subdirectory to your system PATH.

---

## Step 2: Install Git

### Option A: Download from git-scm.com

1. Navigate to:
   ```
   https://git-scm.com/download/win
   ```

2. Download the **64-bit Git for Windows** installer.

3. Run the installer with default settings. When prompted:
   - Select **"Git from the command line and also from 3rd-party software"**
   - Select **"Use Windows' default console window"** or your preference

### Option B: Install via winget

```powershell
winget install Git.Git
```

### Verify Git installation

Open a **new** PowerShell window:

```powershell
git --version
```

Expected output:
```
git version 2.x.x.windows.x
```

---

## Step 3: Clone the Repository

1. Choose a working directory. For this guide we use `C:\Projects`:

```powershell
mkdir C:\Projects
cd C:\Projects
```

2. Clone the repository:

```powershell
git clone https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server.git
```

3. Navigate into the project directory:

```powershell
cd unofficial-fortimonitor-mcp-server
```

4. Verify the clone:

```powershell
git status
git log --oneline -5
```

---

## Step 4: Configure the Environment

1. Copy the example environment file:

```powershell
copy .env.example .env
```

2. Open the `.env` file in a text editor:

```powershell
notepad .env
```

3. Set the **required** values:

```ini
# REQUIRED - Replace with your actual FortiMonitor API key
FORTIMONITOR_API_KEY=your_actual_api_key_here

# FortiMonitor API base URL (default is usually correct)
FORTIMONITOR_BASE_URL=https://api2.panopta.com/v2

# Server identification
MCP_SERVER_NAME=unofficial-fortimonitor-mcp
MCP_SERVER_VERSION=1.0.0

# Logging level (use DEBUG for POC troubleshooting, INFO for normal operation)
LOG_LEVEL=INFO

# Schema caching (recommended: leave enabled)
ENABLE_SCHEMA_CACHE=true
SCHEMA_CACHE_DIR=cache/schemas
SCHEMA_CACHE_TTL=86400

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

4. Save and close the file.

---

## Step 5: Install Dependencies

1. Create a Python virtual environment:

```powershell
python -m venv venv
```

2. Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

> **Note:** If you receive an execution policy error, run the following first:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

3. Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

4. Install project dependencies:

```powershell
pip install -r requirements.txt
```

5. Install the project in editable mode (creates the `unofficial-fortimonitor-mcp` entry point):

```powershell
pip install -e .
```

---

## Step 6: Verify the Installation

### 6a. Run the test suite

```powershell
pytest tests\ -v
```

All tests should pass. Expected output ends with something like:
```
========================= X passed in Y.YYs =========================
```

### 6b. Test API connectivity

Verify your API key works by running a quick curl test in PowerShell:

```powershell
$apiKey = "your_actual_api_key_here"
Invoke-RestMethod -Uri "https://api2.panopta.com/v2/server?api_key=$apiKey&limit=1"
```

You should receive a JSON response with server data. If you get an authentication error, double-check your API key.

### 6c. Test the MCP server starts

```powershell
python -m src.server
```

The server should start without errors. Press `Ctrl+C` to stop it (it runs as a stdio server and will appear to hang waiting for input -- that is normal behavior).

---

## Step 7: Configure Claude Code Integration

Claude Code uses an MCP configuration file to discover and connect to MCP servers.

### Locate the Claude Code configuration

The Claude Code MCP settings file is typically at:

```
%APPDATA%\Claude\claude_desktop_config.json
```

Or for Claude Code (CLI):

```
%USERPROFILE%\.claude\settings.json
```

### Add the FortiMonitor MCP server

Edit the configuration file and add the `fortimonitor` entry under `mcpServers`:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "C:\\Projects\\unofficial-fortimonitor-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "src.server"],
      "cwd": "C:\\Projects\\unofficial-fortimonitor-mcp-server",
      "env": {
        "FORTIMONITOR_API_KEY": "your_actual_api_key_here",
        "FORTIMONITOR_BASE_URL": "https://api2.panopta.com/v2"
      }
    }
  }
}
```

> **Important:** Use the full path to the `python.exe` inside the virtual environment. Adjust `C:\Projects\unofficial-fortimonitor-mcp-server` if you cloned to a different location.

### Alternative: Use environment variables from .env file

If you prefer not to embed the API key in the config, you can set system environment variables instead:

```powershell
[System.Environment]::SetEnvironmentVariable("FORTIMONITOR_API_KEY", "your_actual_api_key_here", "User")
[System.Environment]::SetEnvironmentVariable("FORTIMONITOR_BASE_URL", "https://api2.panopta.com/v2", "User")
```

Then simplify the config to:

```json
{
  "mcpServers": {
    "fortimonitor": {
      "command": "C:\\Projects\\unofficial-fortimonitor-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "src.server"],
      "cwd": "C:\\Projects\\unofficial-fortimonitor-mcp-server"
    }
  }
}
```

### Restart Claude Code

After saving the configuration, fully restart Claude Code for the changes to take effect.

---

## Step 8: Running the Server

The MCP server runs automatically when Claude Code invokes it via the configuration above. No manual startup is required during normal use.

### Manual startup (for testing)

If you need to run the server manually for debugging:

```powershell
cd C:\Projects\unofficial-fortimonitor-mcp-server
.\venv\Scripts\Activate.ps1
python -m src.server
```

### Verify in Claude Code

Once configured, open Claude Code and try a query like:

```
Show me all monitored servers
```

or

```
Are there any active outages?
```

Claude should use the FortiMonitor MCP tools to query your FortiMonitor instance and return results.

---

## Docker Alternative

If Docker Desktop or Docker Engine is available on the Windows Server, this provides an isolated deployment.

### Install Docker (if not present)

1. Enable the **Containers** Windows feature:

```powershell
Install-WindowsFeature -Name Containers
```

2. Install Docker via winget or download from [docker.com](https://docs.docker.com/desktop/setup/install/windows-install/).

### Build and run with Docker Compose

```powershell
cd C:\Projects\unofficial-fortimonitor-mcp-server

# Set your API key in the .env file (Step 4 above)

# Build and start the container
docker-compose up -d --build

# Verify it is running
docker ps
docker logs unofficial-fortimonitor-mcp
```

### Configure Claude Code for Docker

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

---

## Troubleshooting

### Python not found after installation

Close all PowerShell windows and reopen. If still not found:

```powershell
# Check if Python is in PATH
$env:PATH -split ";" | Select-String -Pattern "Python"

# Manually add if needed (adjust path to your Python install)
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311;C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts"
```

### Virtual environment activation fails

If you see a script execution policy error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### API authentication errors

1. Verify the API key is correct in `.env`
2. Test the key directly:

```powershell
$headers = @{}
$response = Invoke-RestMethod -Uri "https://api2.panopta.com/v2/server?api_key=YOUR_KEY&limit=1" -Headers $headers
$response
```

3. Confirm the server has outbound HTTPS access to `api2.panopta.com`

### MCP server not appearing in Claude Code

1. Verify the config JSON is valid (no trailing commas, proper escaping of backslashes)
2. Confirm the `python.exe` path points to the venv Python
3. Restart Claude Code completely
4. Check for errors by running the server manually:

```powershell
cd C:\Projects\unofficial-fortimonitor-mcp-server
.\venv\Scripts\Activate.ps1
python -m src.server
```

### Firewall considerations

Ensure outbound HTTPS (port 443) is allowed to:
- `api2.panopta.com` (FortiMonitor API)
- `github.com` (for cloning the repository)
- `pypi.org` and `files.pythonhosted.org` (for pip packages)

### Cache directory errors

If schema caching fails, ensure the cache directory exists:

```powershell
mkdir C:\Projects\unofficial-fortimonitor-mcp-server\cache\schemas -Force
```

---

## Summary

| Step | Action                                  | Status |
|------|-----------------------------------------|--------|
| 1    | Install Python 3.11+                    |        |
| 2    | Install Git                             |        |
| 3    | Clone the repository                    |        |
| 4    | Configure `.env` with API key           |        |
| 5    | Create venv and install dependencies    |        |
| 6    | Run tests and verify connectivity       |        |
| 7    | Configure Claude Code MCP settings      |        |
| 8    | Restart Claude Code and test            |        |

After completing these steps, the FortiMonitor MCP Server will provide Claude with 241 tools for managing and monitoring your FortiMonitor infrastructure, including server management, outage tracking, metrics retrieval, maintenance windows, notifications, and more.
