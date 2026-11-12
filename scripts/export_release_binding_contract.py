#!/usr/bin/env python3
"""Bounded read-only inventory for P3.2.5; run from PO_Agent_Harness root.

Displays function-level API signatures and sanitized context. Does NOT import
modules, access network/keys/env, or modify files. Review output before sharing.
"""
from pathlib import Path
import ast
import re

ROOT = Path.cwd()
MAX_FILES = 24
MAX_LINES = 135
SENSITIVE = re.compile(
    r"(?i)(password|token|credential|authorization|cookie|keychain|"
    r"client_secret|private.key|pem|process\\.env|os\\.environ|dotenv|"
    r"api[_-]?key|bearer|secret)"
)
RELEVANT = re.compile(
    r"(?i)(sberproject|as21|swtr|task[_-]?detail|task[_-]?read|"
    r"get[_-]?task|searchTaskCr|release|fix_version_s)"
)
TARGETS = (
    ROOT / "task-api/app/services/sberproject/skill_bridge.py",
    ROOT / "task-api/app/services/sberproject/sberproject_read.py",
    ROOT / "task-api/app/routers/sberproject_read.py",
    ROOT / ".gigacode/skills/sbt-project/src/sbt-project.js",
)
CANDIDATES = [
    *TARGETS,
    *sorted((ROOT / "task-api/app").rglob("*.py"))[:500],
]
seen = set()
selected = []
for path in CANDIDATES:
    if path in seen or not path.is_file():
        continue
    seen.add(path)
    try:
        lines = path.read_text("utf-8").splitlines()
    except (OSError, UnicodeError):
        continue
    # Limit scope: relevant source only, no tenant-wide or filesystem scan.
    if path not in TARGETS and not RELEVANT.search(str(path)):
        if not any(RELEVANT.search(line) for line in lines[:400]):
            continue
    selected.append((path, lines))
    if len(selected) >= MAX_FILES:
        break

def safe_line(n, line):
    if SENSITIVE.search(line):
        return f"{n}: [REDACTED security/config line]"
    return f"{n}: {line[:200]}"

for path, lines in selected:
    print("\\n###", path.relative_to(ROOT), "(lines:", len(lines), ")")
    matches = [i for i, line in enumerate(lines) if (
        RELEVANT.search(line) and
        (re.search(r"\\b(def|async def|function|async function|class)\\b", line)
         or "searchTaskCr" in line or "fix_version_s" in line
         or "issueKey" in line or "def versions(" in line)
    )]
    # For the known local bridge, reveal only the relevant task/release binding
    # methods and their short neighborhoods, not whole modules.
    allowed = set()
    for i in matches[:18]:
        allowed.update(range(max(0, i - 2), min(len(lines), i + 7)))
    # JS cmdRelease and searchTaskCr query: bounded samples around named funcs.
    if path.suffix == ".js":
        for i, line in enumerate(lines):
            if re.search(r"(?:function\\s+cmdRelease|function\\s+cmdVersions|searchTaskCr)", line):
                allowed.update(range(max(0, i - 2), min(len(lines), i + 13)))
    for i in sorted(allowed)[:MAX_LINES]:
        print(safe_line(i + 1, lines[i]))
    if len(allowed) > MAX_LINES:
        print("[TRUNCATED: send specific source interval only if needed]")
print("\\nEND: read-only source contract inventory; no network, writes, or secrets.")
