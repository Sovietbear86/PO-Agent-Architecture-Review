#!/usr/bin/env python3
"""
Rollback GigaCode MCP configuration fix.
"""
import json
import shutil

system_settings = "/Users/kalachanov.v.v/.gigacode/settings.json"
backup = "/Users/kalachanov.v.v/.gigacode/settings.json.mcp-fix-20260802"
orig_backup = "/Users/kalachanov.v.v/.gigacode/settings.json.orig"

# Restore from original backup
shutil.copy(orig_backup, system_settings)
print("Restored from original backup:", orig_backup)
print("Rollback completed!")
