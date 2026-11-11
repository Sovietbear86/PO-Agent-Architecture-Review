#!/usr/bin/env bash
# ChatGPT owner deployment: ONLY Releases UI source files from a green isolated
# integration worktree. No Git merges, staging, resets, service restarts or env edits.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
PAGE="po-agent-platform-v2/frontend/src/recovery/Pages.tsx"
DASH="po-agent-platform-v2/frontend/src/recovery/ReleasesDashboard.tsx"
ORIGINAL_HEAD="$(git rev-parse HEAD)"
echo "Live checkout HEAD: $ORIGINAL_HEAD"
[[ -f "$PAGE" ]] || { echo "ERROR: not PO Agent root" >&2; exit 2; }
[[ -z "$(git status --porcelain -- "$PAGE" "$DASH")" ]] || { echo "ERROR: target frontend files already modified; refuse overwrite." >&2; exit 3; }

# Use the exact green HEAD from the owner's independent preflight, never arbitrary
# origin branch and never assume an unpushed connector exists on GitHub.
INTEGRATED_HEAD="${1:-}"
if [[ -z "$INTEGRATED_HEAD" ]]; then
  echo "ERROR: pass the verified isolated HEAD from PREPARED_AND_BUILT report." >&2
  echo "Usage: bash scripts/deploy_releases_dashboard_local.sh <INTEGRATED_HEAD>" >&2
  exit 4
fi
git cat-file -e "${INTEGRATED_HEAD}^{commit}" || exit 5
[[ "$(git rev-parse "${INTEGRATED_HEAD}~4")" == "$ORIGINAL_HEAD" ]] || {
  echo "ERROR: source HEAD changed since the green preflight; STOP." >&2; exit 6;
}
EXPECTED="$(git diff --name-only "$ORIGINAL_HEAD" "$INTEGRATED_HEAD")"
while IFS= read -r name; do
  [[ -z "$name" || "$name" == "$PAGE" || "$name" == "$DASH" ]] || {
    echo "ERROR: preflight includes unrelated source change $name. STOP." >&2
    exit 7
  }
done <<< "$EXPECTED"
[[ -n "$EXPECTED" ]] || { echo "ERROR: no UI delta" >&2; exit 8; }
git cat-file -e "${INTEGRATED_HEAD}:${PAGE}"
git cat-file -e "${INTEGRATED_HEAD}:${DASH}"
SAVE="$(mktemp -d "${TMPDIR:-/tmp}/po-agent-release-ui-backup.XXXXXX")"
cp "$PAGE" "$SAVE/Pages.tsx"
git show "${INTEGRATED_HEAD}:${PAGE}" > "$SAVE/Pages.new.tsx"
git show "${INTEGRATED_HEAD}:${DASH}" > "$SAVE/ReleasesDashboard.new.tsx"
# Preserve permissions; replacement is not atomic across both files, but
# backup/rollback provided and live browser will be checked after.
cp "$SAVE/Pages.new.tsx" "$PAGE"
cp "$SAVE/ReleasesDashboard.new.tsx" "$DASH"
echo "DEPLOYED_FRONTEND_SOURCE_ONLY"
echo "LIVE_HEAD_UNCHANGED=$ORIGINAL_HEAD"
echo "BACKUP_DIR=$SAVE"
echo "Releases dashboard source files now updated in live checkout."
echo "Git status of target files (expect M Pages.tsx, ?? ReleasesDashboard.tsx):"
git status --short -- "$PAGE" "$DASH"
echo "No backend/agent or Core V4 files modified, no services restarted."
echo "Open the running browser Releases page, switch OLP/DMS, click refresh."
echo "If browser smoke fails, restore using:"
echo "  cp '$SAVE/Pages.tsx' '$PAGE'; rm '$DASH'"
echo "Then report exact failure to ChatGPT; do NOT ask GigaCode to fix."
