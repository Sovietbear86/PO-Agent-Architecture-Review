# GigaCode — Current Action

## Status
`WAIT_FOR_OWNER_H0_REAL_WORKSPACE_CUTOVER`

## Reason
Real browser evidence proved that production UI still mounts the legacy `recovery/WorkspaceApp` chat path and therefore Assignment 149 cannot be treated as a valid Hermes/v3 browser certification. The architecture plan has been rebaselined in `HERMES_ARCHITECTURE_REBASELINE_2026-09-03.md`.

Do not continue old Assignment 149 and do not modify production/backend/frontend code.

## Next QA work
Wait for owner H0 changes that:
- cut the real Workspace drawer over to the unified Agent Core entry point;
- remove transient localStorage session reuse;
- expose real runtime/session identity in the actual mounted UI;
- eliminate duplicate assistant entry-point ambiguity.

After owner H0 commits are ready, a new focused browser A/B/C assignment will be issued.

QA/tester only. STOP.