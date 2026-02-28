@echo off
REM =============================================================================
REM FortiMonitor MCP Server - Docker Build Script (Windows)
REM =============================================================================
REM
REM Usage:
REM   scripts\build.bat                         Build with default settings
REM   set VERSION=1.0.0 && scripts\build.bat    Build with version tag
REM
REM =============================================================================

setlocal enabledelayedexpansion

REM Configuration
if "%IMAGE_NAME%"=="" set IMAGE_NAME=unofficial-fortimonitor-mcp
if "%VERSION%"=="" set VERSION=latest

echo =============================================
echo  FortiMonitor MCP Server - Docker Build
echo =============================================
echo.

REM Navigate to project root
cd /d "%~dp0.."

echo Building Docker image: %IMAGE_NAME%:%VERSION%
echo.

REM Build the image
docker build ^
    --tag "%IMAGE_NAME%:%VERSION%" ^
    --tag "%IMAGE_NAME%:latest" ^
    --file Dockerfile ^
    .

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    exit /b 1
)

echo.
echo =============================================
echo  Build Complete!
echo =============================================
echo.
echo   Image: %IMAGE_NAME%:%VERSION%
echo   Image: %IMAGE_NAME%:latest
echo.
echo Run with:
echo   docker run -e FORTIMONITOR_API_KEY=your-key %IMAGE_NAME%:latest
echo.
