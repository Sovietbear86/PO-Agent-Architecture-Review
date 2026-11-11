#!/usr/bin/env bash
# ChatGPT-authored patch for the live Release Dashboard. Only one frontend file.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TARGET="po-agent-platform-v2/frontend/src/recovery/ReleasesDashboard.tsx"
[[ -f "$TARGET" ]] || { echo "Missing ReleasesDashboard.tsx" >&2; exit 2; }
git fetch --no-tags origin feat/core8-real-query-hardening-v2
BEFORE="000f0ee"
AFTER="0f87b92"
git cat-file -e "$BEFORE:$TARGET"
git cat-file -e "$AFTER:$TARGET"
T1="$(mktemp)" T2="$(mktemp)"
trap 'rm -f "$T1" "$T2"' EXIT
git show "$BEFORE:$TARGET" > "$T1"
git show "$AFTER:$TARGET" > "$T2"
if ! cmp -s "$T1" "$TARGET"; then
  echo "ABORT: local dashboard diverged since previous approved patch; no overwrite." >&2
  exit 3
fi
BACKUP="$(mktemp "${TMPDIR:-/tmp}/po-agent-releases-layout.XXXXXXXX.bak")"
cp "$TARGET" "$BACKUP"
cp "$T2" "$TARGET"
echo "LAYOUT_PATCH_APPLIED; backup=$BACKUP"
echo "The live application should hot-reload through Vite; no backend restart."
echo "Check: toolbar spacing; selected detail pane to right of milestones on wide screens;"
echo "scrollable tasks area correctly says linkage pending, not 0 tasks."
echo "Rollback: cp '$BACKUP' '$TARGET'"
