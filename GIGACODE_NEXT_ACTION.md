# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_160_H1A_WMB_SOURCE_RETRY`

## Mission
Finish H1A certification after Assignment 159 proved the Capability Registry runtime and exact A/B parity GREEN, with only one protected Browser C case failing on `AS21SourceUnavailable` for `Задачи Калачанова в WMB`.

This is a CONTINUATION. Do NOT rerun Assignment 158 from scratch and do NOT repeat already-green H1A registry/unit phases unless provenance changed.

QA only. Do not modify production/backend/frontend/test source code or committed `.env` files.

Accepted evidence from prior assignments:
- Assignment 157: `PLAYWRIGHT_BROWSER_HARNESS_GREEN_H0_CERTIFIED`.
- Assignment 158 Phase 0-1: H1A registry contract/unit gate PASS (10/10).
- Assignment 159 Phase 0: v3=true, qwen LLM, source healthy preflight PASS.
- Assignment 159 Phase 1: focused H1A runtime registry proof PASS 2/2.
- Assignment 159 Phase 2: fresh REAL Agent A == Oracle B exact parity PASS.
- Assignment 159 Phase 3: 4/5 Playwright PASS; only `Задачи Калачанова в WMB` failed with `AS21SourceUnavailable`.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B.
- Browser C = real Playwright Chromium against mounted WorkspaceApp.
- No local DB, sync, fake, frozen or surrogate truth.
- Concurrency=1.
- Source-backed timeout 300s.
- A source failure may be called transient ONLY after the required retries are actually executed and recorded.
- Retry proven source failures exactly twice, with 30s backoff between attempts.
- Exact task-key-set parity is mandatory.
- No source/backend/frontend/test edits.
- No caveat GREEN.

## Phase 0 — provenance and runtime preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Record HEAD/clean state.
3. Confirm Assignment 159 report exists and contains:
   - H1A runtime proof PASS;
   - exact A/B parity PASS;
   - 4/5 Browser PASS;
   - WMB failure `AS21SourceUnavailable`.
4. Start/reuse the production-like Agent backend with `PO_AGENT_AGENT_CORE_V3_ENABLED=true`, REAL Task API and qwen LLM.
5. Query `/health` and require:
   - `agent_core_v3_enabled=true`;
   - semantic mode qwen/LLM;
   - source status healthy.
6. Also probe the REAL source path needed by WMB before Browser C. Health alone is not sufficient evidence: execute one direct REAL AS21/MCP-SWTR WMB-capable read/query and record success/failure.

If preflight source is unavailable, execute the required 2 retries with 30s backoff. If still unavailable, STOP with `BLOCKED_BY_PROVEN_SOURCE_OUTAGE` and raw evidence.

## Phase 1 — focused WMB triage with mandatory retries
Fresh-read REAL AS21 Oracle B for:
`Задачи Калачанова в WMB`

Persist exact normalized task-key set and timestamp. Historical count/key sets are not authoritative.

Then execute the same query through Agent A in a fresh session.

Require:
- `architecture_stage == H1A_REGISTRY`;
- `capability_id == task-search-v3`;
- source authority REAL_AS21;
- `llm_used=true`;
- accepted constraints include `assignee=Kalachanov.V.V` and `space=WMB`;
- postconditions PASS;
- status COMPLETED unless Oracle B itself proves source unavailable;
- Agent A exact keys == fresh Oracle B exact keys.

If either Oracle B or Agent A returns `AS21SourceUnavailable`, retry that failing operation twice with 30s backoff and record all three attempts separately. Do NOT label it transient without this evidence.

If Oracle B succeeds but Agent A still fails after retries, verdict must be `H1A_WMB_AGENT_SOURCE_PATH_RED` and STOP: this is a product/adaptor path defect, not a generic source outage.

If both Oracle B and Agent A fail after retries, verdict may be `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`.

## Phase 2 — focused Browser C WMB
Only after Phase 1 is GREEN, run the single Browser test for WMB first:

`npm run e2e:h0 -- --grep "Калачанова.*WMB"`

Require PASS in real Chromium with:
- drawer session correlation intact;
- Agent Core v3/current H1A stage visible;
- no stale correction/clarification;
- COMPLETED;
- exact/semantic result consistent with the same fresh Oracle B set.

If Browser C gets `AS21SourceUnavailable`, perform two re-runs of the focused Browser test with 30s backoff, recording each attempt. If direct Oracle B remains healthy while Browser/Agent path repeatedly fails, classify as product path RED, not transient source outage.

## Phase 3 — protected full H0 regression
Only after focused WMB Browser PASS, run:

`npm run e2e:h0`

Require all 5 tests PASS.

Do not stop on an unrelated transient source error without the same required retry evidence. Preserve the first failing boundary and raw trace if any real defect appears.

## Phase 4 — H1A final consistency audit
Before verdict, correct/report any arithmetic inconsistencies from prior reports. Assignment 159 stated 16 total Garanin tasks but listed per-space counts that summed differently; recompute from the exact key set, not prose counts.

Confirm final H1A evidence:
- registry unit/contract PASS;
- runtime registry proof PASS;
- exact Agent A/Oracle B parity PASS;
- focused WMB PASS;
- full Browser C 5/5 PASS.

## Phase 5 — final report
Write:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1A_WMB_SOURCE_RETRY_160.md`

Allowed verdicts ONLY:
- `AGENT_CORE_V3_H1A_REGISTRY_GREEN`
- `H1A_WMB_AGENT_SOURCE_PATH_RED`
- `H1A_BROWSER_REGRESSION_RED`
- `H1A_AGENT_ORACLE_PARITY_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

GREEN requires focused WMB Agent/Oracle parity + focused Browser PASS + full H0 Playwright 5/5 PASS, in addition to already-accepted H1A gates.

Commit/push ONLY the new QA report and STOP.

## Start now
Execute Assignment 160 completely. Do not call the WMB failure transient unless the mandated retry sequence is actually performed and recorded.