#!/usr/bin/env bash
# ChatGPT-owned read-only-to-live-tree integration preflight.
# Creates a separate worktree from the *current local HEAD*; NEVER modifies,
# resets, stashes or restarts the running PO Agent checkout/services.
set -Eeuo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [[ "$(git rev-parse --is-inside-work-tree)" != "true" ]]; then
  echo "Not a Git checkout" >&2; exit 2
fi
if [[ ! -f po-agent-platform-v2/frontend/package.json ]]; then
  echo "Expected PO Agent repository root, got $ROOT" >&2; exit 2
fi

BASE="$(git rev-parse HEAD)"
BRANCH="$(git symbolic-ref --quiet --short HEAD || echo detached)"
echo "Source checkout: $ROOT"
echo "Local branch: $BRANCH | local HEAD: $BASE"
echo "No local changes will be staged or moved:"
git status --short | head -30 || true

# The owner changes were committed on GitHub and may not be present locally,
# because previous owner's live SberProject commits failed to push.
echo "Fetching owner dashboard commits only (does not merge/reset)..."
git fetch --no-tags origin feat/core8-real-query-hardening-v2

for commit in 00373ff 79ad7ab c467643 a8dc8a7; do
  if ! git cat-file -e "$commit^{commit}" 2>/dev/null; then
    echo "Missing owner commit $commit; network/fetch incomplete. STOP." >&2
    exit 3
  fi
done

DEST="$(mktemp -d "${TMPDIR:-/tmp}/po-agent-release-integrate.XXXXXX")"
# Git worktree add requires an empty or nonexistent destination.
rmdir "$DEST"
git worktree add --detach "$DEST" "$BASE"
echo "Isolated worktree: $DEST"
echo "Applying ONLY the 4 ChatGPT owner frontend commits on local HEAD..."
if ! git -C "$DEST" cherry-pick 00373ff 79ad7ab c467643 a8dc8a7; then
  echo "MERGE_CONFLICT: isolated worktree only. Live source and processes untouched." >&2
  echo "Inspect: git -C '$DEST' status --short" >&2
  echo "DO NOT resolve with GigaCode or overwrite local worktree. Send this output to ChatGPT." >&2
  exit 4
fi

echo "Dashboard integration staged in isolated worktree."
echo "Integrated HEAD: $(git -C "$DEST" rev-parse HEAD)"
echo "Core V4 diff against original local HEAD (must be empty):"
CORE_DIFF="$(git -C "$DEST" diff --name-only "$BASE" HEAD -- 'po-agent-platform-v2/src/*agent_core_v4*' 'po-agent-platform-v2/src/v4_plugin_registry.py' 'po-agent-platform-v2/src/**/agent_core_v4*')"
if [[ -n "$CORE_DIFF" ]]; then echo "$CORE_DIFF"; exit 5; fi

echo "Running one frontend build in isolated checkout (npm ci; requires registry access)..."
(
  cd "$DEST/po-agent-platform-v2/frontend"
  if ! npm ci --no-audit --no-fund; then
    echo 'npm ci blocked by existing package-lock.json drift; repairing LOCKFILE ONLY in isolated worktree.' >&2
    npm install --package-lock-only --ignore-scripts --no-audit --no-fund
    npm ci --no-audit --no-fund
  fi
  npm run build
)

REPORT="$DEST/RELEASE_DASHBOARD_INTEGRATION_RESULT.txt"
{
  echo "LOCAL_BASE=$BASE"
  echo "LOCAL_BRANCH=$BRANCH"
  echo "ISOLATED_HEAD=$(git -C "$DEST" rev-parse HEAD)"
  echo "SOURCE_REPO=$ROOT"
  echo "ISOLATED_WORKTREE=$DEST"
  echo "FRONTEND_BUILD=PASS"
  echo "LOCKFILE_STATUS=$(git -C \"$DEST\" status --short -- po-agent-platform-v2/frontend/package-lock.json | tr -d '\\n')"
  echo "CORE_V4_DIFF=EMPTY"
  echo "LIVE_CHECKOUT_UNMODIFIED=true"
  echo "LIVE_RUNTIME_CHECK=NOT_RUN"
} > "$REPORT"
echo
echo "PREPARED_AND_BUILT (not yet live-deployed; no browser smoke performed)"
echo "Report: $REPORT"
echo "Send the integrated HEAD and report to ChatGPT for controlled deployment + QA handoff."
