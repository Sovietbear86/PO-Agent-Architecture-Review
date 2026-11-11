#!/usr/bin/env python3
"""Owner-only guarded patch for the existing SberProject CLI and task-api bridge.

Run from PO_Agent_Harness root. Default: dry run and show a bounded source diff.
APPLY_SBERPROJECT_PAGINATION=1 writes both files only after all preflight checks.
Does not touch Core V4, auth, TLS, keychain, user services, or config.
"""
from __future__ import annotations

import ast
import difflib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path.cwd().resolve()
CLI = ROOT / ".gigacode/skills/sbt-project/src/sbt-project.js"
BRIDGE = ROOT / "task-api/app/services/sberproject/skill_bridge.py"


def fail(message: str) -> None:
    raise SystemExit(f"PATCH_BLOCKED: {message}; no source changes performed")


def one(pattern: str, source: str, label: str, flags: int = 0) -> re.Match[str]:
    matches = list(re.finditer(pattern, source, flags))
    if len(matches) != 1:
        fail(f"{label}: expected exactly one matching source anchor; found {len(matches)}")
    return matches[0]


def bounded_js_function(source: str) -> tuple[int, int]:
    m = one(r"(?m)^(?:async\s+)?function\s+cmdVersions\s*\(", source, "cmdVersions")
    next_func = re.search(r"(?m)^(?:async\s+)?function\s+\w+\s*\(", source[m.end():])
    if next_func is None:
        fail("cmdVersions: unable to locate following function boundary")
    return m.start(), m.end() + next_func.start()


def patch_cli(original: str) -> str:
    a, b = bounded_js_function(original)
    body = original[a:b]
    # Scope modifications to versions only. There are other commands using offset:0.
    m = one(r"(?m)^([ \t]*)const limit\s*=\s*Math\.min\(parseInt\(opts\.maxResults\s*\?\?\s*['\"]50['\"],\s*10\),\s*200\);", body, "versions limit")
    indent = m.group(1)
    new = (
        f"\n{indent}const offset = Number(opts.offset ?? '0');"
        f"\n{indent}if (!Number.isSafeInteger(offset) || offset < 0 || offset > 500) {{"
        f"\n{indent}  throw new Error('Invalid versions pagination offset');"
        f"\n{indent}}}"
    )
    body = body[:m.end()] + new + body[m.end():]
    m = one(r"(?m)^([ \t]*)offset:\s*0,", body, "versions GraphQL hardcoded offset")
    body = body[:m.start()] + m.group(1) + "offset," + body[m.end():]
    # Derive cursor from the actual emitted result rows; do not claim a future page
    # by blindly adding a limit when GraphQL returns fewer rows.
    # Live CLI returns jsonOutput(versions, { meta fields inline }).
    one(r"\\bjsonOutput\\(\\s*versions\\s*,\\s*\\{", body, "versions inline jsonOutput")
    rows = "versions"
    hm = one(r"(?m)^([ \t]*)has_more:\s*totalCount\s*>\s*limit\s*,?", body, "versions has_more")
    indent = hm.group(1)
    substitute = (
        f"{indent}has_more: totalCount > offset + {rows}.length,\n"
        f"{indent}offset,\n"
        f"{indent}next_offset: totalCount > offset + {rows}.length ? offset + {rows}.length : null,"
    )
    body = body[:hm.start()] + substitute + body[hm.end():]
    edited = original[:a] + body + original[b:]
    # Find the versions command in the Commander registration, not a similarly
    # named flag on another command.
    cmd = one(r"\\.command\\(\\s*['\\\"]versions\\s+<productId>['\\\"]\\s*\\)", edited, "versions command registration")
    action = edited.find(".action(", cmd.end())
    if action < 0 or action - cmd.end() > 3500:
        fail("versions command registration: cannot identify option chain")
    region = edited[cmd.end():action]
    opt = one(r"(?m)^([ \t]*)\.option\(\s*['\"]--max-results\s+<n>['\"][^\n]*\)\s*$", region, "versions max-results option")
    new_opt = opt.group(1) + ".option('--offset <n>', 'Version page offset (0..500)', '0')"
    region = region[:opt.end()] + "\n" + new_opt + region[opt.end():]
    edited = edited[:cmd.end()] + region + edited[action:]
    if edited == original:
        fail("versions: no edits")
    return edited


def bounded_py_method(source: str) -> tuple[int, int]:
    m = one(r"(?m)^([ \t]*)(?:async\s+)?def versions\s*\(", source, "skill_bridge.versions")
    indent = m.group(1)
    next_def = re.search(r"(?m)^" + re.escape(indent) + r"(?:async\s+)?def\s+\w+\s*\(", source[m.end():])
    return m.start(), (m.end() + next_def.start()) if next_def else len(source)


def patch_bridge(original: str) -> str:
    a, b = bounded_py_method(original)
    body = original[a:b]
    guard = one(
        r"(?m)^[ \t]*if\s+offset\s*!=\s*0\s*:\s*\n[ \t]*raise\s+SkillBridgeError\([^\n]*REASON_PAGINATION[^\n]*\)\s*\n",
        body, "offset!=0 guard")
    body = body[:guard.start()] + "\n" + body[guard.end():]
    # Exact CLI argv structure, as reported by live read-only inventory.
    # Live bridge constructs argv inline inside _run_skill(...).
    cmd = one(r'''\\[\\s*['"]versions['"]\\s*,\\s*product\\s*,\\s*['"]--max-results['"]\\s*,\\s*str\\(limit\\)\\s*\\]''', body, "versions CLI argv list")
    body = body[:cmd.start()] + '["versions", product, "--max-results", str(limit), "--offset", str(offset)]' + body[cmd.end():]
    cursor = one(r'''['"]next_offset['"]\\s*:\\s*None\\b''', body, "bridge inline next_offset")
    body = body[:cursor.start()] + '"next_offset": (meta.get("next_offset") if type(meta.get("next_offset")) is int else None)' + body[cursor.end():]
    # Ensure bridge actually reads CLI metadata and preserves source identity.
    if not re.search(r"\bmeta\s*=\s*", body):
        fail("bridge metadata variable not found")
    edited = original[:a] + body + original[b:]
    try:
        ast.parse(edited)
    except SyntaxError:
        fail("bridge syntax validation failed")
    return edited


def main() -> None:
    if not CLI.is_file() or not BRIDGE.is_file():
        fail("missing local skill or bridge; invoke from PO_Agent_Harness root")
    before = {CLI: CLI.read_text(encoding="utf-8"), BRIDGE: BRIDGE.read_text(encoding="utf-8")}
    after = {CLI: patch_cli(before[CLI]), BRIDGE: patch_bridge(before[BRIDGE])}
    with tempfile.TemporaryDirectory(prefix="po-agent-sberproject-paging-") as tmp:
        js = Path(tmp) / "sbt-project.js"
        js.write_text(after[CLI], encoding="utf-8")
        try:
            result = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            fail("node --check not available/completed")
        if result.returncode:
            fail("node --check failed")
        print("SOURCE_PREFLIGHT_PASS: CLI JS + bridge Python parsed, authentication untouched")
        # Edits are deliberately small: show them for operator review before apply.
        for path in (CLI, BRIDGE):
            diff = "".join(difflib.unified_diff(before[path].splitlines(True), after[path].splitlines(True),
                              fromfile=str(path.relative_to(ROOT)),
                              tofile=str(path.relative_to(ROOT)) + " (proposed)"))
            print(diff[:11000])
        if os.environ.get("APPLY_SBERPROJECT_PAGINATION") != "1":
            print("DRY_RUN_ONLY. To install after review: APPLY_SBERPROJECT_PAGINATION=1 python3 /tmp/apply_sberproject_pagination_owner.py")
            return
        backup_dir = Path(tempfile.mkdtemp(prefix="po-agent-sberproject-paging-backup-"))
        for path in (CLI, BRIDGE):
            shutil.copy2(path, backup_dir / path.name)
        changed: list[Path] = []
        try:
            for path in (CLI, BRIDGE):
                # Race check: never overwrite concurrent user edits.
                if path.read_text(encoding="utf-8") != before[path]:
                    raise RuntimeError("local source changed during preflight")
                path.write_text(after[path], encoding="utf-8")
                changed.append(path)
        except (OSError, RuntimeError):
            for path in changed:
                shutil.copy2(backup_dir / path.name, path)
            fail("write failed or concurrent edit; restored backups")
        print("PAGINATION_SOURCE_PATCH_APPLIED; backups:", backup_dir)
        print("Services have NOT been restarted; no live success has been claimed.")
        print("Run a single bounded live page 0/20/40/60 smoke after controlled service restart.")


if __name__ == "__main__":
    main()
