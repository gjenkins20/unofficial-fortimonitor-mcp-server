"""Test configuration loading."""

import os
from pathlib import Path

# Check .env file
print("=== Environment File Check ===")
env_file = Path(".env")
if env_file.exists():
    print(f"✓ .env file exists at: {env_file.absolute()}")
    with open(env_file, 'r') as f:
        print("\nContents:")
        for line in f:
            if 'API_KEY' in line:
                # Mask the API key for security
                parts = line.split('=')
                if len(parts) == 2:
                    print(f"{parts[0]}={parts[1][:10]}...{parts[1][-4:]}")
            else:
                print(line.rstrip())
else:
    print("✗ .env file not found!")

print("\n=== Environment Variables ===")
print(f"FORTIMONITOR_BASE_URL: {os.getenv('FORTIMONITOR_BASE_URL', 'NOT SET')}")
api_key = os.getenv('FORTIMONITOR_API_KEY', 'NOT SET')
if api_key != 'NOT SET':
    print(f"FORTIMONITOR_API_KEY: {api_key[:10]}...{api_key[-4:]}")
else:
    print("FORTIMONITOR_API_KEY: NOT SET")

print("\n=== Loading Settings Class ===")
try:
    from src.config import Settings
    settings = Settings()
    print(f"✓ Settings loaded successfully")
    print(f"  Base URL: {settings.fortimonitor_base_url}")
    print(f"  API Key: {settings.fortimonitor_api_key[:10]}...{settings.fortimonitor_api_key[-4:]}")
    print(f"  API Key length: {len(settings.fortimonitor_api_key)}")
except Exception as e:
    print(f"✗ Error loading settings: {e}")
    print("\nTrying direct import...")
    try:
        from src.config import settings
        print(f"  Type of settings: {type(settings)}")
        print(f"  Settings object: {settings}")
    except Exception as e2:
        print(f"  Direct import also failed: {e2}")