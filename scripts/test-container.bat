@echo off
REM =============================================================================
REM FortiMonitor MCP Server - Container Test Script (Windows)
REM =============================================================================
REM
REM Usage:
REM   scripts\test-container.bat
REM   set FORTIMONITOR_API_KEY=your-key && scripts\test-container.bat
REM
REM =============================================================================

setlocal enabledelayedexpansion

REM Configuration
if "%IMAGE_NAME%"=="" set IMAGE_NAME=fortimonitor-mcp
if "%VERSION%"=="" set VERSION=latest

set TESTS_PASSED=0
set TESTS_FAILED=0

echo =============================================
echo  FortiMonitor MCP Server - Container Tests
echo =============================================
echo.

REM Test 1: Image exists
echo Testing: Image exists...
docker image inspect %IMAGE_NAME%:%VERSION% >nul 2>&1
if %errorlevel%==0 (
    echo   PASSED
    set /a TESTS_PASSED+=1
) else (
    echo   FAILED
    set /a TESTS_FAILED+=1
)

REM Test 2: Container starts
echo Testing: Container starts...
docker run --rm -e FORTIMONITOR_API_KEY=test-key %IMAGE_NAME%:%VERSION% python -c "print('Container OK')" >nul 2>&1
if %errorlevel%==0 (
    echo   PASSED
    set /a TESTS_PASSED+=1
) else (
    echo   FAILED
    set /a TESTS_FAILED+=1
)

REM Test 3: Python imports work
echo Testing: Python imports...
docker run --rm -e FORTIMONITOR_API_KEY=test-key %IMAGE_NAME%:%VERSION% python -c "from src.server import FortiMonitorMCPServer; print('Imports OK')" >nul 2>&1
if %errorlevel%==0 (
    echo   PASSED
    set /a TESTS_PASSED+=1
) else (
    echo   FAILED
    set /a TESTS_FAILED+=1
)

REM Test 4: Config module loads
echo Testing: Config module...
docker run --rm -e FORTIMONITOR_API_KEY=test-key %IMAGE_NAME%:%VERSION% python -c "from src.config import get_settings; print('Config OK')" >nul 2>&1
if %errorlevel%==0 (
    echo   PASSED
    set /a TESTS_PASSED+=1
) else (
    echo   FAILED
    set /a TESTS_FAILED+=1
)

REM Test 5: MCP module available
echo Testing: MCP module...
docker run --rm -e FORTIMONITOR_API_KEY=test-key %IMAGE_NAME%:%VERSION% python -c "from mcp.server import Server; print('MCP OK')" >nul 2>&1
if %errorlevel%==0 (
    echo   PASSED
    set /a TESTS_PASSED+=1
) else (
    echo   FAILED
    set /a TESTS_FAILED+=1
)

REM Test 6: Environment variable handling
echo Testing: Env var handling...
docker run --rm -e FORTIMONITOR_API_KEY=my-test-key-123 %IMAGE_NAME%:%VERSION% python -c "from src.config import get_settings; s = get_settings(); assert s.fortimonitor_api_key == 'my-test-key-123'" >nul 2>&1
if %errorlevel%==0 (
    echo   PASSED
    set /a TESTS_PASSED+=1
) else (
    echo   FAILED
    set /a TESTS_FAILED+=1
)

REM Test 7: Tool definitions load
echo Testing: Tool definitions...
docker run --rm -e FORTIMONITOR_API_KEY=test-key %IMAGE_NAME%:%VERSION% python -c "from src.tools.servers import get_servers_tool_definition; t = get_servers_tool_definition(); assert t.name == 'get_servers'" >nul 2>&1
if %errorlevel%==0 (
    echo   PASSED
    set /a TESTS_PASSED+=1
) else (
    echo   FAILED
    set /a TESTS_FAILED+=1
)

echo.
echo =============================================
echo  Test Summary
echo =============================================
echo.
echo   Passed: %TESTS_PASSED%
echo   Failed: %TESTS_FAILED%
echo.

if %TESTS_FAILED% gtr 0 (
    echo Some tests failed!
    exit /b 1
) else (
    echo All tests passed!
    exit /b 0
)
