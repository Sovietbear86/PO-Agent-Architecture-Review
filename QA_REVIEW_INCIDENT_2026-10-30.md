# Review incident triage — 2026-10-30

## Context (DO NOT MODIFY APP)
Owner observed two symptoms in **running Review**, not Public:
1. Chat query `Покажи задачи Калачанова в STS с 20.10.2026` returned `FAILED`, 80,738 ms, evidence=0, generic V4 fail-closed.
2. Overview snapshot refresh reports `Не удалось обновить · данные на 30.10.2026, 15:14`; sprint tile displays 18/36 (50%) and Predictability N/A, **possibly cached**.
Public PR #4 independent browser QA may be running concurrently. Never terminate or reconfigure user or Public services. Preserve all dirty files. No write-capable AS21 calls, no bulk scans, no secrets in reports.

## Owner-verified GitHub delta
`git compare ceac9fe...feat/core8-real-query-hardening-v2`: **one commit, only `GIGACODE_NEXT_ACTION.md` changed**. No tracked Review production code delta since previous independently tested A230R3.5 baseline. This excludes local uncommitted or running process/environment differences.

## Narrow read-only forensic tasks (independent QA only)
1. Record **actual running Review** PID/port, `git rev-parse HEAD`, `git status --short`, environment variable **presence only** (AS21_MODE, TASK_API_BASE_URL, LLM_API_BASE_URL, LLM_MODEL_NAME, AGENT_CORE_V4_ENABLED; NEVER values/secrets). Match running revision to code; no service restart.
2. Get sanitized trace for the 80,738-ms `FAILED` request (trace/session IDs if log available). Determine exact stage and warning/exception classification: LLM 429/timeouts vs AS21/MCP 401/403/502 vs planner V4ContractError/repair-budget vs timeout/adapter. No guessing based on latency alone. Check HTTP status and elapsed timings for existing logs without replaying unlimited requests.
3. Reproduce safely on Review at most 2 bounded queries (with user consent if live resources needed), one simple known-safe scoped task query and one original person+space+creation-period query. Compare single bounded REAL AS21 oracle, avoid tenant-wide scans. Date `с 20.10.2026` is **open-ended creation date** ambiguous to planner; assess whether `task.search_created` parser supports this expression, vs named employee resolver. No changes to Agent Core or hardcoded phrase routing.
4. Snapshot forensic: `pageSnapshot.tsx` sets `REFRESH_TIMEOUT_MS=120000`, concurrency=2, and caches prior results in sessionStorage. On the Overview it issues 3 LLM-powered queries, the Sprint view issues 6. Identify which request rejected/timeout on click; distinguish stale cached tile from current source. Confirm `refreshError` is not a provenance signal. Compare any 18/36 metric to fresh source only when authorized. Do NOT label cached 50% as current.
5. Investigate recent API / LLM 429 traffic during parallel Public QA, shared LLM quotas, transient AS21 connectivity, request queue; don't infer environment from code. Explicitly check difference between Review and Public processes (ports 8004/8904 and endpoint targets), no cross-proxy confusion.
6. Confirm 6 frozen Core V4 files byte-identical to checkpoint `6fb335d`; do not alter code/config or clear user caches. If confirmed bug, prepare minimal **outside-Core** owner patch proposal and isolated offline regression. User owns code changes; GigaCode QA-only.
7. Report `first failing boundary`, concrete timestamp/trace, source of latency, AS21 completeness, whether snapshot display is stale, reproducibility, safe containment, and whether Public work affected Review. If logs unavailable, mark not verified rather than attributing to 429.

## Priority
**P1 reliability incident** for Review. Keep ongoing Public independent QA untouched; do not update `GIGACODE_NEXT_ACTION.md` until its current Public run finishes.
