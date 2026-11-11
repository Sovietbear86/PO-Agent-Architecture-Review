#!/usr/bin/env bash
# ChatGPT-owned narrow correction for already deployed Releases dashboard.
# Does not change backend, Core V4, secrets, or restart live services.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TARGET="po-agent-platform-v2/frontend/src/recovery/ReleasesDashboard.tsx"
[[ -f "$TARGET" ]] || { echo "Missing dashboard file; STOP" >&2; exit 2; }
git fetch --no-tags origin feat/core8-real-query-hardening-v2
# The original dashboard checked in by ChatGPT was the parent of the widget
# corrections. Compare bytes before replacing to protect unrelated live edits.
BASE="a8dc8a7"
LATEST="61f2cb3"
git cat-file -e "$BASE:$TARGET"
git cat-file -e "$LATEST:$TARGET"
OLD="$(mktemp)"
NEW="$(mktemp)"
trap 'rm -f "$OLD" "$NEW"' EXIT
git show "$BASE:$TARGET" > "$OLD"
git show "$LATEST:$TARGET" > "$NEW"
if ! cmp -s "$OLD" "$TARGET"; then
  echo "LIVE_DASHBOARD_DIVERGED: deployed file differs from expected initial dashboard." >&2
  echo "Nothing changed. Send diff --no-index from safe local snapshot to ChatGPT (no secrets)." >&2
  exit 3
fi
BACKUP="$(mktemp "${TMPDIR:-/tmp}/po-agent-releases-dashboard.XXXXXXXX.bak")"
cp "$TARGET" "$BACKUP"
cp "$NEW" "$TARGET"
echo "RELEASES_WIDGET_PATCH_APPLIED"
echo "BACKUP=$BACKUP"
echo "Frontend dev server should hot-reload; no process restart required."
echo "Check OLP/DMS date semantics, 'Далее' disabled reason and visual parity."
echo "For rollback: cp '$BACKUP' '$TARGET'"
