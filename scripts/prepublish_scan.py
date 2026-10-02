from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", "dist", "__pycache__"}

PATTERNS = {
    "possible_secret": re.compile(
        r"(?i)(?:api[_-]?key|token|secret|password)\s*[=:]\s*['\"]?(?!YOUR_|$)[A-Za-z0-9_./+\-=]{16,}"
    ),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "user_home_path": re.compile(r"(?:/Users/[^/\s]+|/home/[^/\s]+|[A-Za-z]:\\Users\\[^\\\s]+)"),
    "corp_email_example": re.compile(r"(?i)\b[A-Za-z0-9._%+-]+@sbertech\.ru\b"),
}

ALLOW_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".md", ".toml",
    ".txt", ".sh", ".env", ".example", ".html", ".css"
}


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.endswith(".lock"):
            continue
        if path.suffix and path.suffix.lower() not in ALLOW_SUFFIXES and path.name not in {".gitignore"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                # .env examples intentionally contain empty placeholders.
                snippet = match.group(0)[:120].replace("\n", " ")
                findings.append(f"{path.relative_to(ROOT)}: {label}: {snippet}")
    if findings:
        print("PRE-PUBLISH SCAN: RED")
        print("\n".join(findings))
        return 1
    print("PRE-PUBLISH SCAN: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
