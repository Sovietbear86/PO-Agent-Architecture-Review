#!/usr/bin/env python3
"""
Fix GigaCode MCP configuration by removing sseServer from system settings.
"""
import json

system_settings = "/home/user/.gigacode/settings.json"
backup = "/home/user/.gigacode/settings.json.mcp-fix-20260802"

# Read current settings
with open(system_settings, 'r') as f:
    settings = json.load(f)

# Backup
import shutil
shutil.copy(system_settings, backup)
print(f"Backup created: {backup}")

# Remove sseServer
if "sseServer" in settings:
    del settings["sseServer"]
    print("Removed 'sseServer' from system config")

# Save updated settings
with open(system_settings, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print("System config updated!")
