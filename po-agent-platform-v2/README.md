# PO Agent Platform v2.1

Harness-based PO workspace with deterministic metrics, source-aware Skills and a controlled AI-PDLC improvement loop.

## Current recovery status

The recovery branch implements the new runtime as a strangler next to the legacy agent. The recovery CI treats the new Harness as the product boundary and keeps legacy/external-service tests as a separate diagnostic lane.

- 54 canonical Skills are implemented in code.
- Skill availability is source-aware: implemented does not mean usable when required source facts are absent.
- `fake` mode provides deterministic local fixtures for development and acceptance tests.
- `task-api` mode uses an asynchronous, fail-closed adapter over the existing task-api/SWTR boundary.
- Source outages, unsupported capabilities and malformed source contracts are returned as typed failures, never as an empty portfolio.
- Metrics and scoring remain deterministic; LLM use is limited to interpretation/drafting layers.
- Feedback cannot directly mutate production behaviour. Changes pass evals, failure mining, candidate generation, offline/shadow evaluation, regression gate and explicit human approval before version promotion; rollback is auditable.
- The recovery frontend is a PO Workspace with persistent agent chat plus task, sprint, release, team and quality workspaces.

## Architecture

```text
PO Workspace / Agent Chat
          |
          v
  Source-aware Harness
          |
   Intent -> Versioned Skill -> Allow-listed Capability
          |                         |
          |                         +-> deterministic Metrics / PO logic
          v
      AS21Adapter
       /      \
 FakeAS21   TaskApiAS21Adapter
                 |
              task-api
                 |
              AS21/SWTR
```

Additional source contracts are injected independently for facts that task-api does not currently expose:

- `TeamCompetencySource` — declared team profiles/competencies;
- `SprintSnapshotSource` — committed sprint scope snapshots;
- `ReleaseTimelineSource` — historical release progress points.

The runtime advertises source facts and calculates readiness for every Skill. A Skill that needs history, attachments, snapshots, competencies or a release timeline is marked unavailable when that fact is not connected.

## AI-PDLC / Harness learning loop

```text
Execution
  -> Operational History
  -> Explicit Feedback
  -> Eval Seeds
  -> Failure Mining
  -> Improvement Candidate
  -> Offline / Shadow Evaluation
  -> Regression Gate
  -> Human Approval
  -> Version Promotion
  -> Rollback
```

Operational history is not silently reused as conversational memory. Session context is scoped separately. Improvement candidates are inert until approval.

## Quick start

Prerequisites: Python 3.11+, Node.js 22+ for the frontend.

```bash
cd po-agent-platform-v2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
cp .env.example .env
```

### Run with deterministic fake AS21

```bash
export AS21_MODE=fake
uvicorn po_agent.main:app --reload --port 8004
```

### Run through task-api / SWTR boundary

Start task-api first, then:

```bash
export AS21_MODE=task-api
export TASK_API_BASE_URL=http://localhost:8003
# optional; otherwise runtime probes the canonical task-api config locations
export TEAM_CONFIG_PATH=../task-api/config/team_members.yaml
uvicorn po_agent.main:app --reload --port 8004
```

The task-api adapter currently advertises `tasks`, `sprints` and `releases`. History and attachment Skills intentionally remain unavailable until task-api exposes those facts. Sprint carryover/scope-change require a snapshot source; release forecast requires a timeline source.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

## API

- `POST /api/v1/query` — execute a Harness request.
- `GET /api/v1/health` — readiness, adapter mode, source health, source facts and ready/unavailable Skill counts.
- `GET /health` — process liveness.
- `GET /version` — application version.
- `GET /docs` — OpenAPI UI.

Example query payload:

```json
{
  "query": "Покажи WMB-101",
  "session_id": "po-session-1"
}
```

Responses include `trace_id`, resolved Skill/version, evidence, warnings and structured data.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `AS21_MODE` | `fake` or `task-api` | `fake` |
| `TASK_API_BASE_URL` | task-api URL | `http://localhost:8003` |
| `TASK_API_TIMEOUT_SECONDS` | source timeout | `30` |
| `TEAM_CONFIG_PATH` | optional canonical team profile YAML | auto-probe in task-api mode |
| `LLM_API_BASE_URL` | OpenAI-compatible LLM endpoint | `https://api.ai.sbt/v1` |
| `LLM_API_KEY` | LLM credential | unset |
| `LLM_MODEL_NAME` | model name | `qwen-coder-3.7` |
| `DATABASE_URL` | local persistence | `sqlite:///data/app.db` |

Legacy `SWTR_BASE_URL`/`SWTR_TOKEN` remain only for compatibility code paths; the recovered production boundary is `Harness -> TaskApiAS21Adapter -> task-api -> SWTR`.

## CI and release gates

`Harness Recovery CI` contains four lanes:

1. `backend-recovery` — canonical acceptance suites for the recovered Harness.
2. `backend-hermetic-regression` — deterministic backend regression without real LLM/SWTR dependencies.
3. `frontend` — TypeScript typecheck + Vite production build.
4. `backend-legacy-diagnostic` — complete old suite, intentionally non-blocking while legacy real-service debt is retired.

Before merge, the first three lanes must be green. The legacy diagnostic lane remains visible but does not define recovery correctness.

## Source of truth

- `PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md` — product/master specification.
- `docs/recovery/CANONICAL_SKILL_CATALOG.md` — capability inventory.
- `docs/recovery/LEGACY_TEST_DEBT.md` — quarantined legacy test debt.
- `docs/recovery/FINAL_HARDENING_STATUS.md` — merge-readiness checklist and remaining external prerequisites.
