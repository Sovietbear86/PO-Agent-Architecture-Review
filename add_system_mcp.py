#!/usr/bin/env python3
"""
Add s21_agent MCP server to system GigaCode settings.
"""
import json
import os

system_settings = "/Users/kalachanov.v.v/.gigacode/settings.json"
backup = "/Users/kalachanov.v.v/.gigacode/settings.json.system-mcp-backup"

# Read current settings
with open(system_settings, 'r') as f:
    settings = json.load(f)

# Backup
import shutil
shutil.copy(system_settings, backup)
print(f"Backup created: {backup}")

# Add mcpServers if not exists
if "mcpServers" not in settings:
    settings["mcpServers"] = {}

# Add s21_agent
settings["mcpServers"]["s21_agent"] = {
    "command": "python3",
    "args": [
        "/Users/kalachanov.v.v/Desktop/Мои документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1/s21_mcp_proxy.py"
    ],
    "transport": "stdio"
}

# Remove sseServer
if "sseServer" in settings:
    del settings["sseServer"]
    print("Removed 'sseServer' from system config")

# Save updated settings
with open(system_settings, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print("System config updated with s21_agent!")
print("Keys:", list(settings.keys()))
