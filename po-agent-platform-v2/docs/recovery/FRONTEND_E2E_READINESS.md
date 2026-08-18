# Frontend E2E readiness

## Why this stage exists

The recovered backend and Harness have extensive deterministic/adversarial coverage, while the React workspace has so far been validated mainly by TypeScript/build checks. The next product risk is therefore composition: browser -> Vite -> FastAPI -> Harness -> AS21 adapter -> source.

## Architecture snapshot

```text
React PO Workspace (Vite, :5175)
  -> /api/v1 via Vite proxy
  -> FastAPI po_agent.main (:8004)
  -> api/v1 router
  -> HarnessRuntime / RuntimeBundle
  -> source-aware Skills
  -> AS21Adapter
       -> FakeAS21 (local deterministic)
       -> TaskApiAS21Adapter -> task-api (:8003) -> SWTR/AS21
```

The UI's canonical production interaction is `POST /api/v1/query`; health/readiness is `GET /api/v1/health`. Dashboard screens intentionally ask the Harness using natural-language Skills rather than directly calling SWTR.

## Important architecture finding

`frontend/src/api/client.ts` still exposes CRUD-style helpers for `/tasks`, `/team`, `/releases`, `/evaluations` and `/metrics`, but the recovered `api/v1` router currently implements only `/health`, `/query`, `/feedback/{trace_id}` and `/learning/semantic`.

This is not currently breaking the recovered workspace because the active `recovery/*` screens use `agent.query()` for product data. Treat the unused CRUD helpers as legacy/dead API surface until explicit backend endpoints are implemented; do not build new UI flows on them.

## E2E gates

### Gate 1 — stack readiness (implemented)

`npm run test:e2e:readiness` verifies, without introducing a browser-test dependency:

1. Vite frontend is reachable and serves the React mount point.
2. `/api/v1/health` works through the frontend proxy.
3. Health payload identifies runtime and adapter.
4. `/api/v1/query` works through the same proxy.
5. The response matches the frontend Harness contract (`status`, `trace_id`, `session_id`, `evidence`).

Run locally:

```bash
# terminal 1
cd po-agent-platform-v2
export AS21_MODE=fake
uvicorn po_agent.main:app --reload --port 8004

# terminal 2
cd po-agent-platform-v2/frontend
npm ci
npm run dev

# terminal 3
cd po-agent-platform-v2/frontend
npm run test:e2e:readiness
```

Expected final marker: `E2E_READINESS_GREEN`.

### Gate 2 — browser E2E (next)

After Gate 1 is green, add Playwright and cover at minimum:

- workspace loads and all six routes render;
- PO Agent drawer opens/closes;
- user query -> visible answer -> evidence panel;
- clarification options continue the same session;
- thumbs up/down feedback reaches backend;
- task search renders real Harness data;
- local task survives route changes via localStorage;
- backend unavailable state is visible and non-destructive;
- task-api/SWTR shadow mode remains read-only.

### Gate 3 — real SWTR composition

Repeat the same browser suite with `AS21_MODE=task-api` and task-api connected to SWTR. This lane must remain read-only and must assert zero mutation calls.

## Release rule

Do not call the frontend production-ready until Gate 1 + Gate 2 are green in fake mode and the critical read-only subset of Gate 3 is green against real SWTR.
