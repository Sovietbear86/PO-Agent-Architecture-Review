#!/usr/bin/env python3
"""Run a local validation command and persist redacted diagnostics for review.

Raw logs stay local. Sanitized logs and a compact JSON summary are produced in
.artifacts/diagnostics/<run_id>/. Nothing under .artifacts is intended for git.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SECRET_PATTERNS = [
    (re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[A-Za-z0-9._~+\-/=]+"), r"\1<REDACTED>"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+\-/=]+"), r"\1<REDACTED>"),
    (re.compile(r"(?i)((?:token|api[_-]?key|platform_session|cookie|secret|password)\s*[:=]\s*[\"']?)[^\s\"']+"), r"\1<REDACTED>"),
    (re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), "<REDACTED_JWT>"),
]

CLASSIFIERS = {
    "AUTH": ("401", "403", "unauthorized", "forbidden", "invalid token", "expired token", "authentication", "permission denied"),
    "NETWORK": ("timeout", "timed out", "connection refused", "connection reset", "dns", "name or service not known", "ssl", "certificate", "proxy"),
    "ENV": ("no such file", "command not found", "modulenotfounderror", "importerror", "address already in use", "environment variable", "not installed"),
    "SOURCE": ("404", "endpoint", "schema", "unexpected response", "source unavailable", "service unavailable"),
    "DATA": ("not found", "empty result", "no tasks", "missing field", "unexpected status", "unknown status", "assert 0"),
    "CODE": ("traceback", "assertionerror", "typeerror", "attributeerror", "keyerror", "valueerror", "runtimeerror"),
}


def redact(text: str) -> str:
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def classify(text: str, return_code: int) -> list[str]:
    if return_code == 0:
        return []
    lowered = text.casefold()
    matches = [name for name, markers in CLASSIFIERS.items() if any(marker in lowered for marker in markers)]
    # A traceback alone is not proof of a code defect; preserve competing categories.
    return matches or ["UNKNOWN"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run command with persistent redacted diagnostics")
    parser.add_argument("--name", default="validation", help="Short test/run name")
    parser.add_argument("--root", default=None, help="Repository root; auto-detected by default")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command after --")
    args = parser.parse_args()
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        parser.error("command is required after --")

    repo_root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{args.name}"
    out_dir = repo_root / ".artifacts" / "diagnostics" / run_id
    out_dir.mkdir(parents=True, exist_ok=False)

    started = datetime.now(timezone.utc)
    env = os.environ.copy()
    proc = subprocess.run(command, cwd=repo_root / "po-agent-platform-v2", env=env, text=True, capture_output=True)
    finished = datetime.now(timezone.utc)
    combined = f"$ {shlex.join(command)}\n\n[STDOUT]\n{proc.stdout}\n\n[STDERR]\n{proc.stderr}\n"
    sanitized = redact(combined)
    categories = classify(sanitized, proc.returncode)

    # raw.log is intentionally local-only and may contain credentials/source data.
    (out_dir / "raw.log").write_text(combined, encoding="utf-8")
    (out_dir / "sanitized.log").write_text(sanitized, encoding="utf-8")
    summary = {
        "schema_version": 1,
        "run_id": run_id,
        "name": args.name,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_seconds": round((finished - started).total_seconds(), 3),
        "command": command,
        "return_code": proc.returncode,
        "result": "PASS" if proc.returncode == 0 else "FAIL",
        "failure_categories": categories,
        "classification_is_heuristic": True,
        "share_files": ["summary.json", "sanitized.log"],
        "raw_log_local_only": True,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (repo_root / ".artifacts" / "diagnostics" / "LATEST").write_text(run_id + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Diagnostics: {out_dir}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
