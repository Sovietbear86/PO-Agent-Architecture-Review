#!/usr/bin/env python3
"""Read-only, bounded source contract excerpt for ChatGPT owner pagination patch.

Prints only code excerpts from specified line windows, suppresses credential-looking
lines and values; never imports project modules, invokes auth, or makes network calls.
"""
from pathlib import Path
import os
import re

root = Path.cwd().resolve()
sources = (
    (root / ".gigacode/skills/sbt-project/src/sbt-project.js", [(2100, 2175), (2390, 2490)]),
    (root / "task-api/app/services/sberproject/skill_bridge.py", [(125, 225)]),
    (root / "task-api/app/routers/sberproject_read.py", [(1, 135)]),
)
SECRET = re.compile(r"(?i)(token|secret|password|credential|cookie|authorization|bearer|keychain|private.key|client_secret|pem|process\.env|os\.environ|dotenv)")
for path, ranges in sources:
    print("\n###", path.relative_to(root))
    if not path.is_file():
        print("NOT_FOUND (local working tree path)")
        continue
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        print("READ_ERROR")
        continue
    for a, b in ranges:
        print(f"--- lines {a}-{min(b, len(lines))} ---")
        for idx in range(a-1, min(b, len(lines))):
            line = lines[idx]
            if SECRET.search(line):
                print(f"{idx+1}: [REDACTED credential/config related line]")
            else:
                print(f"{idx+1}: {line[:240]}")
print("\nEND — source excerpts only; no changes, network or auth.")
