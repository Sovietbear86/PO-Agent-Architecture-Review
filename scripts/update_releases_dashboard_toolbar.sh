#!/usr/bin/env bash
# ChatGPT owner patch: only release toolbar styles, preserves live SberProject bridge.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TARGET="po-agent-platform-v2/frontend/src/recovery/ReleasesDashboard.tsx"
git fetch --no-tags origin feat/core8-real-query-hardening-v2
BASE="a07e47a"
UPDATED="cbf59c9"
OLD="$(mktemp)" NEW="$(mktemp)"
trap 'rm -f "$OLD" "$NEW"' EXIT
git show "$BASE:$TARGET" > "$OLD"
git show "$UPDATED:$TARGET" > "$NEW"
if ! cmp -s "$OLD" "$TARGET"; then
  echo "STOP: source differs from verified live version. Nothing changed." >&2; exit 2
fi
BACKUP="$(mktemp "${TMPDIR:-/tmp}/po-agent-releases-toolbar.XXXXXXXX.bak")"
cp "$TARGET" "$BACKUP"
cp "$NEW" "$TARGET"
echo "TOOLBAR_PATCH_APPLIED; backup=$BACKUP"
echo "Task-style version search and Sprint-style right-aligned Refresh. Vite hot reload."
echo "PAGINATION_NOT_FIXED: backend SberProject facade exposes only first page and no cursor."
echo "Rollback: cp '$BACKUP' '$TARGET'"
