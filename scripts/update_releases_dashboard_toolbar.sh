#!/usr/bin/env bash
# ChatGPT owner: safe local Releases toolbar correction, prior live patch rolled back.
# Fail closed: build in temporary frontend clone BEFORE changing live UI.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TARGET="po-agent-platform-v2/frontend/src/recovery/ReleasesDashboard.tsx"
FRONT="po-agent-platform-v2/frontend"
BASE="a07e47a"
UPDATED="14f49e1"
git fetch --no-tags origin feat/core8-real-query-hardening-v2
OLD="$(mktemp)" NEW="$(mktemp)"
STAGING=""
trap 'rm -f "$OLD" "$NEW"; if [[ -n "$STAGING" ]]; then rm -rf "$STAGING"; fi' EXIT
git show "$BASE:$TARGET" > "$OLD"
git show "$UPDATED:$TARGET" > "$NEW"
if ! cmp -s "$OLD" "$TARGET"; then
  echo "STOP: live dashboard does not match rollback baseline a07e47a. No changes." >&2
  exit 2
fi
if grep -Fq 'style={input}' "$NEW"; then
  echo "STOP: dangling React input style binding still present." >&2
  exit 3
fi
[[ -d "$FRONT/node_modules" ]] || { echo "STOP: local frontend node_modules absent; cannot preflight." >&2; exit 4; }
STAGING="$(mktemp -d "${TMPDIR:-/tmp}/po-agent-releases-toolbar-build.XXXXXX")"
( cd "$FRONT"; tar -cf - --exclude='./node_modules' --exclude='./dist' --exclude='./.git' . ) | ( cd "$STAGING"; tar -xf - )
ln -s "$ROOT/$FRONT/node_modules" "$STAGING/node_modules"
cp "$NEW" "$STAGING/src/recovery/ReleasesDashboard.tsx"
echo "Running strict frontend build on isolated snapshot before live update..."
( cd "$STAGING" && npm run build )
BACKUP="$(mktemp "${TMPDIR:-/tmp}/po-agent-releases-toolbar.XXXXXXXX.bak")"
cp "$TARGET" "$BACKUP"
cp "$NEW" "$TARGET"
echo "TOOLBAR_PATCH_APPLIED; isolated strict build PASS; backup=$BACKUP"
echo "Task-style search, right-aligned Sprint-style refresh; Vite hot reload."
echo "PAGINATION_OPEN: SberProject source adapter still lacks next_offset."
echo "Rollback: cp '$BACKUP' '$TARGET'"
