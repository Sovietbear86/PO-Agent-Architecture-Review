#!/usr/bin/env python3
"""
Rollback GigaCode MCP configuration fix.
"""
import json
import shutil

system_settings = "/home/user/.gigacode/settings.json"
backup = "/home/user/.gigacode/settings.json.mcp-fix-20260802"
orig_backup = "/home/user/.gigacode/settings.json.orig"

# Restore from original backup
shutil.copy(orig_backup, system_settings)
print("Restored from original backup:", orig_backup)
print("Rollback completed!")
