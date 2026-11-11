#!/usr/bin/env bash
# ChatGPT-authored changes, applied by owner, no GigaCode development.
# Dashboard UX + optional source-verified version URL type. No backend/Core/env edits.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
UI="po-agent-platform-v2/frontend/src/recovery/ReleasesDashboard.tsx"
API="po-agent-platform-v2/frontend/src/api/client.ts"
[[ -f "$UI" && -f "$API" ]] || { echo "Expected PO Agent root" >&2; exit 2; }
git fetch --no-tags origin feat/core8-real-query-hardening-v2
BASE="000f0ee"
NEW="a07e47a"
for p in "$UI" "$API"; do
  git cat-file -e "$BASE:$p"
  git cat-file -e "$NEW:$p"
  local_before="$(mktemp)"
  git show "$BASE:$p" > "$local_before"
  if ! cmp -s "$local_before" "$p"; then
    rm -f "$local_before"
    echo "ABORT: '$p' differs from known pre-patch baseline. No files changed." >&2
    exit 3
  fi
  rm -f "$local_before"
done
BACKUP="$(mktemp -d "${TMPDIR:-/tmp}/po-agent-releases-v2-backup.XXXXXX")"
cp "$UI" "$BACKUP/ReleasesDashboard.tsx"
cp "$API" "$BACKUP/client.ts"
git show "$NEW:$UI" > "$UI"
git show "$NEW:$API" > "$API"
echo "PATCH_APPLIED — Releases Dashboard UX + optional validated deep-link."
echo "BACKUP_DIR=$BACKUP"
echo "LIVE_SOURCE_HEAD=$(git rev-parse HEAD) unchanged. No backend/Core, secrets, config or services touched."
echo "Source pagination is STILL BLOCKED: CLI returns has_more without next_offset."
echo "Correct next step is inspect source pagination contract then implement backend + tests, not fake Next."
echo "Optional version deep-link only appears if real HTTPS project.sbertech.ru URL is in version payload."
echo "Rollback: cp '$BACKUP/ReleasesDashboard.tsx' '$UI'; cp '$BACKUP/client.ts' '$API'"
