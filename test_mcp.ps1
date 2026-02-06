# FortiMonitor MCP - Complete Test Suite
# Run this script to verify all fixes are working

param(
    [string]$ApiKey = $env:FORTIMONITOR_API_KEY,
    [string]$ContainerName = "unofficial-fortimonitor-mcp-test"
)

$ErrorCount = 0
$TestCount = 0

function Write-TestHeader {
    param([string]$Title)
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Write-TestStart {
    param([string]$TestName)
    $script:TestCount++
    Write-Host "`n[Test $script:TestCount] $TestName" -ForegroundColor Yellow
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    $script:ErrorCount++
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ $Message" -ForegroundColor Gray
}

# Start
Write-TestHeader "FortiMonitor MCP - Test Suite"
Write-Host "Testing FortiMonitor MCP installation and configuration`n" -ForegroundColor White

# Test 1: Python Syntax Verification
Write-TestStart "Python Syntax Verification"
$syntaxErrors = @()
Get-ChildItem src\tools\*.py | Where-Object { $_.Name -ne "__init__.py" } | ForEach-Object {
    Write-Host "  Checking $($_.Name)... " -NoNewline
    $result = python -m py_compile $_.FullName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓" -ForegroundColor Green
    } else {
        Write-Host "✗" -ForegroundColor Red
        $syntaxErrors += "$($_.Name): $result"
        $script:ErrorCount++
    }
}

if ($syntaxErrors.Count -eq 0) {
    Write-Pass "All Python files have valid syntax"
} else {
    Write-Fail "Syntax errors found:"
    $syntaxErrors | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
}

# Test 2: Module Import Test
Write-TestStart "Module Import Test"
$importTest = python -c "from src.tools.servers import get_servers_tool_definition; print('OK')" 2>&1
if ($importTest -eq "OK") {
    Write-Pass "Server tools module imports successfully"
} else {
    Write-Fail "Import failed: $importTest"
}

# Test 3: Tool Object Creation
Write-TestStart "Tool Object Creation"
$toolTest = python -c @"
from src.tools.servers import get_servers_tool_definition
try:
    tool = get_servers_tool_definition()
    print(f'name={tool.name}')
    print(f'description={tool.description}')
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
"@ 2>&1

if ($toolTest -match "OK") {
    Write-Pass "Tool objects created correctly"
    if ($toolTest -match "name=(\w+)") {
        Write-Info "Tool name: $($Matches[1])"
    }
} else {
    Write-Fail "Tool creation failed: $toolTest"
}

# Test 4: Check for Tool Import
Write-TestStart "Tool Import Check"
$hasImport = Get-ChildItem src\tools\*.py | Where-Object { $_.Name -ne "__init__.py" } | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "from mcp.types import Tool" -or $content -match "from mcp import types") {
        Write-Host "  $($_.Name): " -NoNewline
        Write-Host "✓" -ForegroundColor Green
        $true
    } else {
        Write-Host "  $($_.Name): " -NoNewline
        Write-Host "✗ Missing Tool import" -ForegroundColor Red
        $script:ErrorCount++
        $false
    }
}

if ($hasImport -notcontains $false) {
    Write-Pass "All tool files have Tool import"
} else {
    Write-Fail "Some files missing Tool import"
}

# Test 5: Docker Build
Write-TestStart "Docker Image Build"
Write-Info "Building Docker image (this may take 30-60 seconds)..."
$buildOutput = docker build -t fortimonitor-mcp:latest . 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Pass "Docker image built successfully"
    
    # Check image size
    $imageInfo = docker images fortimonitor-mcp:latest --format "{{.Size}}" 2>$null
    if ($imageInfo) {
        Write-Info "Image size: $imageInfo"
    }
} else {
    Write-Fail "Docker build failed"
    Write-Host "`nBuild output:" -ForegroundColor Red
    Write-Host $buildOutput -ForegroundColor Red
}

# Test 6: Container Cleanup
Write-TestStart "Container Cleanup"
Write-Info "Stopping and removing existing test container..."
docker stop $ContainerName 2>$null | Out-Null
docker rm $ContainerName 2>$null | Out-Null
Write-Pass "Cleanup complete"

# Test 7: Container Startup
Write-TestStart "Container Startup"

if (-not $ApiKey) {
    Write-Fail "FORTIMONITOR_API_KEY environment variable not set"
    Write-Info "Set with: `$env:FORTIMONITOR_API_KEY = 'your-key-here'"
    Write-Info "Skipping container tests..."
} else {
    Write-Info "Starting container with API key: $($ApiKey.Substring(0, [Math]::Min(8, $ApiKey.Length)))..."
    
    $startOutput = docker run -d `
        --name $ContainerName `
        -e FORTIMONITOR_API_KEY=$ApiKey `
        fortimonitor-mcp:latest 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Container started"
        Write-Info "Container ID: $($startOutput.Substring(0, 12))"
        
        # Wait for container to initialize
        Write-Info "Waiting for container to initialize..."
        Start-Sleep -Seconds 5
        
        # Test 8: Container Status
        Write-TestStart "Container Status Check"
        $containerStatus = docker inspect $ContainerName --format='{{.State.Status}}' 2>$null
        
        if ($containerStatus -eq "running") {
            Write-Pass "Container is running"
            
            # Get container details
            $containerUptime = docker inspect $ContainerName --format='{{.State.StartedAt}}' 2>$null
            if ($containerUptime) {
                Write-Info "Started at: $containerUptime"
            }
        } else {
            Write-Fail "Container is not running (status: $containerStatus)"
        }
        
        # Test 9: Container Logs
        Write-TestStart "Container Logs Check"
        $logs = docker logs $ContainerName 2>&1
        
        if ($logs -match "error|Error|ERROR|Traceback|SyntaxError|Exception") {
            Write-Fail "Errors found in container logs:"
            Write-Host "`nLogs:" -ForegroundColor Red
            Write-Host $logs -ForegroundColor Red
        } else {
            Write-Pass "No errors in container logs"
            if ($logs) {
                Write-Info "Log entries: $($logs.Split("`n").Count) lines"
            } else {
                Write-Info "Logs are empty (expected for always-running container)"
            }
        }
        
        # Test 10: MCP Server Test
        Write-TestStart "MCP Server Module Test"
        $serverTest = docker exec -i $ContainerName python -c @"
try:
    from src.server import server
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
"@ 2>&1
        
        if ($serverTest -match "OK") {
            Write-Pass "MCP server module loads successfully"
        } else {
            Write-Fail "MCP server module failed to load: $serverTest"
        }
        
        # Test 11: Tool List Test
        Write-TestStart "Tool List Generation Test"
        $toolListTest = docker exec -i $ContainerName python -c @"
try:
    from src.tools.servers import (
        get_servers_tool_definition,
        get_server_details_tool_definition
    )
    from src.tools.outages import (
        get_outages_tool_definition
    )
    
    tools = [
        get_servers_tool_definition(),
        get_server_details_tool_definition(),
        get_outages_tool_definition()
    ]
    
    print(f'LOADED:{len(tools)}')
    for tool in tools:
        print(f'TOOL:{tool.name}')
except Exception as e:
    print(f'ERROR:{e}')
"@ 2>&1
        
        if ($toolListTest -match "LOADED:(\d+)") {
            $toolCount = $Matches[1]
            Write-Pass "Successfully loaded $toolCount tools"
            
            $toolNames = $toolListTest | Select-String -Pattern "TOOL:(\w+)" -AllMatches
            if ($toolNames) {
                Write-Info "Sample tools:"
                $toolNames.Matches | Select-Object -First 3 | ForEach-Object {
                    Write-Info "  • $($_.Groups[1].Value)"
                }
            }
        } else {
            Write-Fail "Tool list generation failed: $toolListTest"
        }
        
        # Test 12: API Connection Test
        Write-TestStart "FortiMonitor API Connection Test"
        Write-Info "Testing API connection (this may take a few seconds)..."
        
        $apiTest = docker exec -i $ContainerName python -c @"
import asyncio
from src.fortimonitor.client import FortiMonitorClient
import os

async def test():
    try:
        client = FortiMonitorClient(api_key=os.environ.get('FORTIMONITOR_API_KEY'))
        servers = await client.get_servers(limit=1)
        if servers:
            print(f'OK:connected')
            print(f'SERVERS:{len(servers)}')
        else:
            print('OK:connected_no_servers')
    except Exception as e:
        print(f'ERROR:{e}')

asyncio.run(test())
"@ 2>&1
        
        if ($apiTest -match "OK:connected") {
            Write-Pass "FortiMonitor API connection successful"
            if ($apiTest -match "SERVERS:(\d+)") {
                Write-Info "Retrieved server data successfully"
            }
        } else {
            Write-Fail "API connection failed: $apiTest"
            Write-Info "Check that your API key is valid"
        }
    } else {
        Write-Fail "Container failed to start: $startOutput"
    }
}

# Test 13: Claude Code Configuration Check
Write-TestStart "Claude Code Configuration Check"
$claudeConfig = "$env:APPDATA\Claude\claude_desktop_config.json"

if (Test-Path $claudeConfig) {
    Write-Pass "Claude Code config file exists"
    
    $config = Get-Content $claudeConfig -Raw | ConvertFrom-Json
    
    if ($config.mcpServers.fortimonitor) {
        Write-Pass "FortiMonitor MCP server configured in Claude Code"
        
        $command = $config.mcpServers.fortimonitor.command
        $args = $config.mcpServers.fortimonitor.args
        
        Write-Info "Command: $command"
        Write-Info "Container: $($args[2])"
        
        if ($args[2] -eq $ContainerName) {
            Write-Pass "Container name matches configuration"
        } else {
            Write-Fail "Container name mismatch!"
            Write-Info "Config expects: $($args[2])"
            Write-Info "Running container: $ContainerName"
        }
    } else {
        Write-Fail "FortiMonitor MCP not configured in Claude Code"
        Write-Info "Add configuration to: $claudeConfig"
    }
} else {
    Write-Fail "Claude Code config file not found"
    Write-Info "Expected at: $claudeConfig"
    Write-Info "Have you installed Claude Code?"
}

# Final Summary
Write-TestHeader "Test Summary"

Write-Host "`nTests run: $TestCount" -ForegroundColor White
if ($ErrorCount -eq 0) {
    Write-Host "Errors: 0" -ForegroundColor Green
    Write-Host "`n✅ ALL TESTS PASSED!" -ForegroundColor Green -BackgroundColor Black
    Write-Host "`nYour FortiMonitor MCP is ready to use with Claude Code!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor White
    Write-Host "  1. Open or restart Claude Code" -ForegroundColor Gray
    Write-Host "  2. Look for the 🔌 icon showing 'fortimonitor' connected" -ForegroundColor Gray
    Write-Host "  3. Ask Claude: 'How many FortiMonitor servers do we have?'" -ForegroundColor Gray
    Write-Host "  4. Claude should use the MCP and return real data!" -ForegroundColor Gray
} else {
    Write-Host "Errors: $ErrorCount" -ForegroundColor Red
    Write-Host "`n❌ TESTS FAILED" -ForegroundColor Red -BackgroundColor Black
    Write-Host "`nPlease review the errors above and fix them before proceeding." -ForegroundColor Red
    Write-Host "`nCommon fixes:" -ForegroundColor White
    Write-Host "  • Syntax errors: Run fix_tool_definitions_final.py" -ForegroundColor Gray
    Write-Host "  • API key issues: Set FORTIMONITOR_API_KEY environment variable" -ForegroundColor Gray
    Write-Host "  • Container issues: Check Docker Desktop is running" -ForegroundColor Gray
    Write-Host "  • Claude Code config: Check claude_desktop_config.json" -ForegroundColor Gray
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Return exit code
exit $ErrorCount
