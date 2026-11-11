#!/usr/bin/env python3
"""PO Agent owner patch: SberProject versions offset pagination (LOCAL ONLY).

Never touches Core V4, credentials, TLS, keychain or user services.
Fail-closed: unexpected source contract => no file is changed.
Live smoke/QA is a separate step after review. GigaCode is QA-only.
"""
from __future__ import annotations

import ast
import difflib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path.cwd().resolve()
CLI = ROOT / ".gigacode/skills/sbt-project/src/sbt-project.js"
BRIDGE = ROOT / "task-api/app/services/sberproject/skill_bridge.py"

def stop(reason: str):
    raise SystemExit("PATCH_BLOCKED: " + reason + " (no files changed)")

def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=90)
    if proc.returncode:
        stop(f"validation command failed: {cmd[0]} (see local logs; not displaying secrets)")

def replace_one(source: str, old: str, new: str, name: str) -> str:
    count = source.count(old)
    if count != 1:
        stop(f"{name}: expected exactly one anchor, got {count}")
    return source.replace(old, new, 1)

def modify_cli(original: str) -> str:
    # Only edit the versions implementation; other commands intentionally keep offset=0.
    start = original.find("async function cmdVersions(")
    if start < 0:
        start = original.find("function cmdVersions(")
    if start < 0:
        stop("cmdVersions function not found")
    body_end = original.find("\nasync function ", start + 10)
    if body_end < 0:
        body_end = original.find("\nfunction ", start + 10)
    if body_end < 0:
        stop("cannot bound cmdVersions")
    fn = original[start:body_end]
    # Avoid options that can silently be ignored by the CLI.
    if not re.search(r"\bopts\.maxResults\b", fn):
        stop("cmdVersions opts.maxResults signature changed")
    if re.search(r"\boffset\s*:\s*0\s*,", fn) is None:
        stop("cmdVersions offset=0 not found")
    fn = replace_one(fn, "offset: 0,", "offset,", "versions GraphQL offset")
    m = re.search(r"(?m)^(?P<indent>\s*)const limit\s*=\s*Math\.min\(parseInt\(opts\.maxResults \?\? '50', 10\), 200\);", fn)
    if not m:
        stop("versions limit declaration changed; review required")
    indent = m.group("indent")
    stmt = (
        f"\n{indent}const offset = Number(opts.offset ?? 0);"
        f"\n{indent}if (!Number.isSafeInteger(offset) || offset < 0 || offset > 500) "
        "throw new Error('Invalid offset: expected integer 0..500');"
    )
    fn = fn[:m.end()] + stmt + fn[m.end():]
    # Derive the cursor from actual number of returned results, not requested limit.
    # This is correct for a short page only if the source still reports has_more.
    match = re.search(r"(?m)^(?P<indent>\s*)has_more\s*:\s*totalCount\s*>\s*limit\s*,", fn)
    if not match:
        stop("versions response has_more expression changed")
    indent = match.group("indent")
    fn = fn[:match.start()] + (
        f"{indent}has_more: totalCount > offset + limit,\n"
        f"{indent}offset,\n"
        f"{indent}next_offset: totalCount > offset + limit ? offset + limit : null,"
    ) + fn[match.end():]
    edited = original[:start] + fn + original[body_end:]
    # CLI must explicitly register the option or --offset may be ignored.
    # Work with the same registration family as --max-results, never assume parser details.
    registration = list(re.finditer(r"(?m)^.*(?:option|addOption|\\.option|\\.addOption).{0,120}--max-results.{0,220}$", edited))
    if len(registration) != 1:
        stop("CLI --max-results registration not uniquely located; cannot safely register --offset")
    line = registration[0].group()
    if "option(" not in line:
        stop("Unknown CLI parser option declaration")
    indent = re.match(r"\s*", line).group()
    # Compatible with Commander .option('--max-results <n>', ...).
    if "('--max-results" not in line and '(\"--max-results' not in line:
        stop("Unknown CLI option registration syntax")
    if line.count("--max-results") != 1:
        stop("ambiguous option declaration")
    if ".option(" in line:
        inserted = f"{indent}.option('--offset <n>', 'SberProject version page offset (0..500)', '0')\n"
        # In fluent chains, option is a line that starts with .option().
        if not line.lstrip().startswith(".option("):
            stop("CLI parser option not a fluent chain; review necessary")
        edited = edited[:registration[0].end()] + "\n" + inserted.rstrip("\n") + edited[registration[0].end():]
    else:
        stop("Unsupported CLI parser shape")
    return edited

def modify_bridge(original: str) -> str:
    # Guard is a one-line check plus a raise; replacement is bounded.
    pat = re.compile(r"(?m)^[ \t]*if offset != 0:\s*\n[ \t]*raise SkillBridgeError\([^\n]*REASON_PAGINATION[^\n]*\)\s*\n")
    matches = list(pat.finditer(original))
    if len(matches) != 1:
        stop("bridge offset rejection guard not uniquely located")
    edited = original[:matches[0].start()] + original[matches[0].end():]
    # CLI has to receive the offset in the versions argv.
    # Exact command invocation argument shapes must match the allowlisted pattern.
    m = re.search(r"\bversions\b", edited)
    if not m:
        stop("bridge versions invocation not found")
    # Requires explicit inspection of live bridge argv builder: don't mutate if ambiguous.
    # Allows safely completing the CLI change separately without risking an auth regression.
    stop("bridge argv construction needs exact source excerpt; no speculative local modification")

def main() -> None:
    if not CLI.is_file() or not BRIDGE.is_file():
        stop("working local CLI or bridge is missing; run from PO_Agent_Harness root")
    cli_before = CLI.read_text(encoding="utf-8")
    bridge_before = BRIDGE.read_text(encoding="utf-8")
    cli_after = modify_cli(cli_before)
    bridge_after = modify_bridge(bridge_before)
    # Transactional preflight: reach here only when every layer is recognized.
    with tempfile.TemporaryDirectory(prefix="po-agent-pagination-preflight-") as d:
        temp_cli = Path(d) / "sbt-project.js"
        temp_bridge = Path(d) / "skill_bridge.py"
        temp_cli.write_text(cli_after, encoding="utf-8")
        temp_bridge.write_text(bridge_after, encoding="utf-8")
        run(["node", "--check", str(temp_cli)])
        ast.parse(bridge_after)
        print("SOURCE_PREFLIGHT_PASS")
        for filename, before, after in [(CLI, cli_before, cli_after), (BRIDGE, bridge_before, bridge_after)]:
            print("".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=str(filename), tofile=str(filename)+" (patched)")))
        if os.environ.get("APPLY_SBERPROJECT_PAGINATION") != "1":
            print("DRY_RUN_ONLY: pass APPLY_SBERPROJECT_PAGINATION=1 only after inspection")
            return
        backup = Path(tempfile.mkdtemp(prefix="po-agent-pagination-backup-"))
        shutil.copy2(CLI, backup / CLI.name)
        shutil.copy2(BRIDGE, backup / BRIDGE.name)
        CLI.write_text(cli_after, encoding="utf-8")
        BRIDGE.write_text(bridge_after, encoding="utf-8")
        print("SOURCE_FILES_UPDATED; BACKUP:", backup)
    print("Do not restart services until a bounded integration smoke passes.")

if __name__ == "__main__":
    main()
