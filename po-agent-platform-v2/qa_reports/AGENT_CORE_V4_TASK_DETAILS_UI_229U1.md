# A229U1 — Task details drawer UI re-gate

**Verdict:** `AGENT_CORE_V4_TASK_DETAILS_UI_RED_A229U1`

**Classification:** `RED_P0_FRONTEND_TSC_BUILD_REGRESSION`

**START_HEAD:** `f95ab8c`
**Previous GREEN checkpoint:** `aa78e52` (A229F2R3)
**Date:** 2026-10-06
**STOP at:** P0.3 (frontend TypeScript/build) — first failing boundary

---

## Summary

| Phase | Result |
|-------|--------|
| P0.1 worktree / P0.2 backend isolation | ✅ GREEN |
| **P0.3 frontend TypeScript/build** | ❌ **RED — `npm run build` fails (exit 2, TS2550)** |
| P0.4 frontend tests | ✅ N/A (no frontend unit tests exist; Playwright e2e only) |
| P0.5 V4 blast-radius | ✅ GREEN (242/242 — no backend regression) |
| P1–P5 | ⏸️ SKIPPED (first-RED STOP rule) |

The owner's A229U1 diff is frontend-only and well-scoped (exactly the Tasks detail drawer), but it introduces a **TypeScript build regression**: `npm run build` (the project's own build script = `tsc && vite build`) now fails at the `tsc` stage.

---

## P0.1 — Worktree (GREEN)

Clean; only `GIGACODE.md` modified (QA memory file, not production code).

## P0.2 — Backend isolation (GREEN)

`git diff --name-only aa78e52..f95ab8c` shows exactly 5 files:

```
GIGACODE_NEXT_ACTION.md
PO_AGENT_HARNESS_EVOLUTION_PLAN.md
V4_DOD_LOCK.md
po-agent-platform-v2/frontend/src/recovery/Pages.tsx      (+184)
po-agent-platform-v2/frontend/src/recovery/workspace.css  (+83)
```

**0 Agent Core / planner / plugin / Task API / backend test changes.** Scope matches the assignment (Tasks detail drawer only).

## P0.3 — Frontend TypeScript/build (RED — first failing boundary)

### Evidence

| Check | `aa78e52` (previous) | `f95ab8c` (A229U1) |
|-------|---------------------|--------------------|
| `npm run build` (= `tsc && vite build`) | tsc exit 0 (baseline worktree probe) | **exit 2** |
| `tsc --noEmit` errors | 0 | **1** |
| `vite build` (alone) | ✅ | ✅ (282.47 kB JS, 644 ms) |

The single error:

```
src/recovery/Pages.tsx(143,29): error TS2550: Property 'replaceAll' does not exist on
type 'string'. Do you need to change your target library? Try changing the 'lib'
compiler option to 'es2021' or later.
```

### Root cause

The new label-fallback line added by the diff (inside the new intelligence label-mapping helper):

```ts
return labels[key] ?? key.replaceAll('_', ' ')
```

`String.prototype.replaceAll` requires lib **ES2021**, while `frontend/tsconfig.json` is pinned to `"target": "ES2020"` / `"lib": ["ES2020", "DOM", "DOM.Iterable"]`. The `replaceAll` call was introduced by this diff (verified: it appears only in the `aa78e52..f95ab8c` diff at this line). Baseline `aa78e52` tsc is clean, so this is a regression introduced by A229U1.

### Blast radius note (non-blocking context)

- `vite build` alone passes (esbuild strips types, no type checking) and `replaceAll` is runtime-available in all modern browsers (Chrome 85+, Safari 13.1+, Firefox 77+), so the dev server and any esbuild-based bundle are not functionally broken by this line.
- However, the project's own `npm run build` / `npm run lint` gates (`tsc && vite build`, `tsc --noEmit && eslint`) **fail**, so CI/build is RED. Per spec: "Any build/backend regression => RED STOP."

## P0.4 — Frontend tests (N/A)

No frontend unit-test suite exists (`package.json` scripts: dev/build/preview/lint/e2e*; only `@playwright/test` present). Nothing retained to run at P0.

## P0.5 — Full V4 blast-radius (GREEN)

**242 passed / 0 failed** (`tests/test_agent_core_v4*.py tests/test_v4*.py`) — identical to the A229F2R3 GREEN baseline; no backend regression from the diff (expected, since it is frontend-only).

---

## Owner fix (proposed, not implemented)

Smallest fix (zero config change, keeps the ES2020 lib target):

```ts
// Pages.tsx:143
return labels[key] ?? key.split('_').join(' ')
```

`split/join` is behaviorally identical for this delimiter case and ES2020-safe. Alternative (broader, not recommended for this delta): bump `tsconfig.json` `target`/`lib` to ES2021 — that is a project-wide config change and out of scope for a UI-only delta.

After the fix: re-run `npm run build` (must be exit 0), then re-gate P1–P5 (browser phases were never started; the agent on 8004 was still on `909bf51` and was not restarted for a browser session since the STOP was reached at P0).

---

## Services state at STOP

- Agent V4: 127.0.0.1:8004 (still on `909bf51`, A229F2R3 — **stale** for A229U1, not restarted)
- Task API: 127.0.0.1:8241 UP
- MCP-SWTR SSE: 127.0.0.1:3000 UP
- Vite UI: 127.0.0.1:5175 (PID 89616; serves the new frontend code in dev mode)

No code was modified by QA. Baseline worktree probe (`/tmp/a229u1_base` @ `aa78e52`) removed after use.
