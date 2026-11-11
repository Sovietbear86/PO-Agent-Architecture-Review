#!/usr/bin/env python3
"""Read-only local pagination contract inventory. No network, no auth access.

Owner uses the output to implement source-level paging in the unpushed local
SberProject adapter; GigaCode is not authorized to change code.
"""
import ast
import os
from pathlib import Path
import re
import subprocess

root = Path(os.environ.get("PO_AGENT_ROOT", os.getcwd())).resolve()
candidates = [
    *root.glob("task-api/app/**/*sberproject*.py"),
    *root.glob("task-api/app/**/*skill_bridge*.py"),
    *root.glob("po-agent-platform-v2/task-api/app/**/*sberproject*.py"),
    *root.glob(".gigacode/skills/sbt-project/src/*.js"),
    *root.glob(".gigacode/skills/sbt-project/src/*.ts"),
]
candidates = sorted({p.resolve() for p in candidates if p.is_file() and len(p.parts) < 30})
print("PAGINATION_CONTRACT_INVENTORY (read-only, no credentials or network)")
try:
    rev = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], text=True).strip()
    print("LOCAL_HEAD:", rev)
except (OSError, subprocess.CalledProcessError):
    pass
keys = re.compile(r"\b(?:offset|next_offset|has_more|hasMore|pageInfo|endCursor|startCursor|limit|skip|cursor|first|versions|productVersionListByPage|sberproject)\b", re.I)
sensitive = re.compile(r"(?:token|password|secret|authorization|cookie|api[_-]?key|bearer|credential|keychain|pem|certificate)", re.I)
for path in candidates:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        continue
    rel = path.relative_to(root)
    print(f"\nFILE: {rel}")
    if path.suffix == ".py":
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and keys.search(node.name):
                    args = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
                    print("  function", node.lineno, node.name, "params:", ", ".join(args))
        except SyntaxError:
            print("  PARSE_ERROR (no source printed)")
    count = 0
    for no, line in enumerate(text.splitlines(), start=1):
        if keys.search(line) and not sensitive.search(line) and len(line) <= 230:
            # Do not print assignments with literal values, HTTP headers, or data.
            if re.search(r"\b(?:print|logger|logging|headers|env|os\.getenv|process\.env)\b", line, re.I):
                continue
            print(f"  L{no}: {line.strip()}")
            count += 1
            if count >= 35:
                print("  [... truncated at 35 safe lines per file]")
                break
print("\nEND; no changes performed. Send this report to ChatGPT to implement real pagination safely.")
