#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 git@github.com:ORG/NEW-REPO.git" >&2
  exit 2
fi

REMOTE="$1"

python3 scripts/prepublish_scan.py

if [[ -d .git ]]; then
  echo "Refusing to reuse existing .git history. Run this script only from an exported snapshot directory." >&2
  exit 3
fi

git init
git add .
git commit -m "Initial community distribution"
git branch -M main
git remote add origin "$REMOTE"
git push -u origin main
