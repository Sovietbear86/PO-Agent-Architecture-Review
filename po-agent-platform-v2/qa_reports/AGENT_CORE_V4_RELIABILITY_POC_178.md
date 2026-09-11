# Assignment 178 — Agent Core v4 Skill-Native Reliability POC (Continuation)

**Verdict: `V4_CAPABILITY_BINDING_RED`**

**Date:** 2026-09-11
**QA role:** tester/adversarial reviewer only (no production/test/code modifications)
**Branch:** `feat/core8-real-query-hardening-v2`
**Test base HEAD:** `75669be41d8f12b302c937599289edd9553e4c01`
**Owner commits under test (verified ancestors of HEAD):**
- `9fa53e90c53c42b407851aa20712748f21303d4f` — `fix(v4): use authoritative current sprint source`
- `9b9a29299ed69f7a485f98df7a37299078980e22` — `test(v4): require live current sprint source method`

**Runtime under test:**
- Model/provider: `Qwen/Qwen3.8-27B` (unchanged)
- Env: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`, `PO_AGENT_AS21_MODE=task-api`
- PO Agent: **fresh instance on `127.0.0.1:8005`** started from current HEAD (see §0.1)
- Task API: `127.0.0.1:8003` (shared, unchanged) — `swtr-read` connected to MCP-SWTR (SSE, 48 tools)
- MCP-SWTR (Oracle B): `127.0.0.1:3000/sse` → REAL AS21
- Concurrency: 1. Source timeout ≥ 300 s. Fresh session per run.

---

## 0. Checkpoint reuse & environment integrity

### 0.1 Stale runtime discovered and replaced
The pre-existing PO Agent instance on `127.0.0.1:8004` was serving **pre-fix** code:
for `Какой текущий спринт в DMS?` it returned *"…текущий спринт не найден…"* (sprint_id=None),
while the task-api `swtr-read/spaces/DMS/current-sprint` endpoint and the repository's new
adapter code both return `DMS-SPRNT-1`. Direct test of the current codebase
(`ProductionTaskApiAS21Adapter.get_current_sprint_id("DMS")`) returned `DMS-SPRNT-1`,
proving the running 8004 process predated the owner fix pull. Process enumeration/kill is
blocked in this environment, so a **fresh instance was started on port 8005** from current
HEAD and all Agent A phases were executed against it. The 8005 instance health:
`agent_core_v4_enabled:true, agent_core_v4_ready:true, adapter:task-api, source_status:healthy`.

Retained (not re-run) evidence from Assignment 177, per checkpoint-reuse instruction:
focused V4 unit tests GREEN; production factory wires `ReliableAgentCoreV4Runtime`;
`/query-v4` bypasses legacy semantic/correction runtime; `semantic_prepass_used=false`;
no hardcoded person/sprint/task ids in V4 runtime.

### 0.2 Focused owner-fix gate (Phase 0)
- `pytest tests/test_agent_core_v4_reliable.py tests/test_agent_core_v4_skill_native.py` → **9 passed**.
- Statically + at runtime: `sprint.current` now calls `adapter.get_current_sprint_id(product)`
  (→ `GET /api/v1/swtr-read/spaces/{space}/current-sprint` → MCP-SWTR → REAL AS21). It no longer
  calls `search_tasks` / `/api/v1/tasks` / local `~/.task-tracker/tasks.json`. No local-cache access.
- **Oracle B** (direct MCP-SWTR `get_current_sprint`, space=DMS): **`DMS-SPRNT-1`**
  (`id.code=DMS-SPRNT-1`, name "Спринт 1", status NEW, 100 tasks in sprint).
- **Agent A** (`/query-v4`, 3 fresh sessions): **3/3** `Текущий спринт в DMS — DMS-SPRNT-1`,
  `prepass=false`, `skills=[sprint.current]`, trajectory `load_skill sprint.current →
  space.resolve DMS → sprint.current {product:DMS} → ready`. **Phase 0 gate = GREEN** (no
  `V4_SOURCE_ADAPTER_RED`).

---

## 1. Phase 1 — Fresh Oracle B (REAL MCP-SWTR only)

Collected directly from `127.0.0.1:3000/sse` (no `/api/v1/tasks`, no local DB, no sync,
no prior counts). Artifact: `qa_178_oracle_results.json`.

| Entity | Oracle B (fresh) |
|---|---|
| DMS current sprint | **`DMS-SPRNT-1`** (100 tasks) |
| `OLP-SPRNT-5` | **67 tasks**; assignees = Galtsov.A.A, Garanin.R.V, Kondratchikova.P.I, Kuznetsov.M.Se, Makoshina.V.V, Reshetnik.A, Semavin.M.M, **Shaldunov.A.V**, **Sidneva.Y.S** |
| Goncharov in `OLP-SPRNT-5` | **none** (0 tasks; `search_users("Гончарова")`=0, `Гончаров`=8 global matches) |
| Garanin.R.V (approved spaces) | **33 tasks** |
| Moiseev.A.N DMS | all=26, **open=26** |
| `DMS-380` | "В компоненте Lineager не работает аутентификация в режиме mTLS, TLS, SSL"; status **QA**; assignee **Semavin.M.M** (Семавин Михаил Михайлович) |
| Populated sprint (health) | `OLP-SPRNT-5` (67 tasks, 66 done) |
| Versions/releases | WMB: 24Q1/24Q2/25Q1; OLP: 1.6.0; STS/CRPV: 25 each; **DMS: 0** |

Notes:
- MCP `get_task` tool is unreliable (returned unrelated units for `DMS-380`); the
  task-api `swtr-read/tasks/{code}` and `read_unit` paths are the authoritative source path
  used by the agent. `DMS-380` detail confirmed via task-api.
- No task in the sampled corpora carries a populated `release`/`version` attribute (see Phase 5 case 8).

---

## 2. Phase 2 — Critical identity/search gate (5x fresh each) → **GREEN**

`qa_178_phase2_results.json`. Exact task-key-set equality vs Oracle B.

| Case | Query | Oracle | Result (5 runs) |
|---|---|---|---|
| 1 | `Задачи Гаранина` | 33 keys | **5/5 EXACT** (33/33), `Garanin.R.V` |
| 2 | `Открытые задачи Андрея Моисеева в DMS` | 26 open keys | **5/5 EXACT** (26/26), `Moiseev.A.N` |
| 3 | `Открытые задачи Гончарова в спринте OLP-SPRNT-5` | 0 (no Goncharov in sprint) | **5/5 EMPTY_PARITY** (0/0), resolves `Goncharov.A.O`, **no fabrication** |

- Person resolution is source-backed (team roster + REAL AS21); no surname/phrase hardcode.
- `semantic_prepass_used=false` on all runs; progressive skill loading visible (`tasks.search`).
- Case 3 confirms the PVM-Guru-style contextual behavior: a globally-ambiguous name
  (`Гончаров`, 8 matches) with a sprint context is resolved to a source-backed login
  (`Goncharov.A.O`) and returns the (correct) empty set — fail-closed, no fabrication.

---

## 3. Phase 3 — Current sprint full reliability (5x fresh) → **GREEN**

`qa_178_phase3_current_sprint.json`. **5/5** `Текущий спринт в DMS — DMS-SPRNT-1`,
`prepass=false`, `skills=[sprint.current]`, authoritative `swtr-read` path. Exact Oracle B parity.

---

## 4. Phase 4 — Generalization (≥6 compound, no code changes between) → 5/6 EXACT

`qa_178_phase4_oracle.json` + `qa_178_phase4_results.json`. Exact key parity, 2 runs each.

| Case | Query | Type | Oracle | Result |
|---|---|---|---|---|
| 1 | `Задачи Макошиной в OLP` | configured, person+space | 14 | **2/2 EXACT** |
| 2 | `Задачи Гальцова в OLP` | configured, person+space | 38 | **2/2 EXACT** |
| 3 | `Задачи Семавина в OLP` | configured, person+space | 166 | **2/2 EXACT** (166/166) |
| 4 | `Задачи Шалдунова в спринте OLP-SPRNT-5` | **sprint-only (not in roster)**, person+sprint | 10 | **2/2 EXACT** (contextual resolve) |
| 5 | `Открытые задачи Кузнецова в спринте OLP-SPRNT-5` | configured, person+sprint+open | 13 | **2/2 EXACT** |
| 6 | `Открытые задачи Шидневой в спринте OLP-SPRNT-5` | **sprint-only (not in roster)**, person+sprint+open | 1 | **2/2 NEEDS_CLARIFICATION** |

- 5/6 compound cases reach exact Oracle parity, including two **sprint-only** (non-roster)
  people and person+space / person+sprint / open constraints.
- **Gap (1/6):** `Шиднева` (Sidneva.Y.S, present in `OLP-SPRNT-5` but not in the roster)
  → `NEEDS_CLARIFICATION` («Не удалось однозначно определить пользователя «Шиднева»»).
  Root cause: context-scoped identity matching is **lexical** and does not bridge
  Cyrillic-reference ↔ Latin-login transliteration reliably for this person (contrast:
  `Шалдунов` succeeded). Fail-closed (no fabrication), but a generalization gap in
  contextual identity resolution.

---

## 5. Phase 5 — Representative cross-skill POC (9 scenarios) → 7/9 terminal-correct

`qa_178_phase5_results.json`. One fresh run each; trajectory + skill + source facts captured.

| # | Query | Skill | Status | Oracle comparison |
|---|---|---|---|---|
| 1 | `Покажи DMS-380` | `task.lookup` | COMPLETED | source-accurate (DMS-380, status QA, assignee Semavin.M.M) |
| 2 | `Кратко объясни DMS-380` | `task.summary` | COMPLETED | source-accurate (Lineager mTLS/TLS/SSL, SSLException) |
| 3 | `Проверь качество постановки DMS-380` | `task.quality` | COMPLETED | 85/100 good |
| 4 | `Проверь критерии приемки DMS-380` | `task.acceptance` | COMPLETED | 0/100, 0 conditions (source-accurate: no AC section) |
| 5 | `Есть ли блокеры у DMS-380` | `task.blockers` | COMPLETED | no blockers (status QA) |
| 6 | `Покажи здоровье спринта OLP-SPRNT-5` | `sprint.health` | COMPLETED | 67 total / 66 done (matches Oracle 67) |
| 7 | `Какой текущий спринт в DMS?` | `sprint.current` | COMPLETED | data=DMS-SPRNT-1 (correct); see §5.1 |
| 8 | `Покажи здоровье релиза 25Q1` | `release.health` | NEEDS_CLARIFICATION | release not populated (see §5.2) |
| 9 | `Покажи DMS-380 и затем задачи его исполнителя` | `tasks.lookup_then_assignee` | **FAILED** | see §5.3 (first failing boundary) |

### 5.1 Case 7 — cosmetic LLM text glitch (data correct)
Answer text rendered `DMS-SPRNT-SPRNT-1` (doubled `SPRNT`) in this run, while the capability
data and Phase 0/3 (8 clean runs) all show `DMS-SPRNT-1`. This is an intermittent final-summary
text-generation artifact, **not** a source/data defect (underlying `sprint_id` is correct).

### 5.2 Case 8 — release health is source-limited (fail-closed, no fabrication)
Candidate live releases `25Q1` (WMB), `24Q2` (WMB), `1.6.0` (OLP) all return
`NEEDS_CLARIFICATION` — «Не удалось подтвердить релиз … по данным REAL AS21». The
`release.health` path resolves a release by `get_release_tasks(release_id)` (TQL `release = <id>`);
no sampled task carries a populated `release` attribute, so no release can be confirmed as
populated. The `swtr-read/versions` endpoint returns 502 and `search_versions(DMS)`=0.
**Behavior is fail-closed (no fabrication)** — a source-availability limitation, not a fabrication.

### 5.3 Case 9 — FIRST FAILING BOUNDARY (capability binding) — RED
```
trajectory: load_skill tasks.lookup_then_assignee
            -> call task.lookup {"task_key": "DMS-380"}
            -> call task.search {"assignee": "semavin.m.m"}
result:     status=FAILED, warnings=[v4_runtime_failure]
            exception_type=V4ContractError
            error="task.search.assignee must equal a source-backed prior observation"
```
**Root cause (confirmed by inspecting the `task.lookup` observation):**
`task.lookup` returns `data={"task": {...}}` whose task object exposes **only**
`assignee` (the Russian **display** string `"Семавин Михаил Михайлович"`) — it does **not**
expose a canonical login/external id under any trusted-identity key
(`member_login` / `external_id` / `assignee_login` / `assignee_id`).
Therefore `_trusted_identity_values(...)` never captures the canonical login, and the
planner's subsequent `task.search(assignee="semavin.m.m")` is rejected by the
source-safe literal guard (`_validate_call_literals`, `assignee` branch) → `V4ContractError`
→ the multi-step **lookup → assignee → tasks** chain cannot complete.

This is a **capability-binding** contract gap: `task.lookup`'s output does not surface a
bindable canonical assignee identity for a downstream `task.search`. It is **pre-existing**
(the owner's `9fa53e9` only changed `sprint.current`) and is not a fabrication — the runtime
fails closed rather than returning wrong data.

---

## 6. Phase 6 — Safety controls (fresh sessions) → 6/7 fail-closed, no fabrication

`qa_178_phase6_results.json`.

| Case | Query | Expect | Result |
|---|---|---|---|
| 1 | `Задачи Петрова в DMS` | fail-closed | **NEEDS_CLARIFICATION**, 0 keys |
| 2 | `Задачи Гаранина в XYZ` | fail-closed (bad space) | **NEEDS_CLARIFICATION**, 0 keys |
| 3 | `Задачи Гаранина в спринте WMB-SPRNT-9999` | fail-closed (bad sprint) | **NEEDS_CLARIFICATION**, 0 keys |
| 4 | `Покажи DMS-999999` | fail-closed (bad task) | **COMPLETED**, 0 keys, "не найдена" |
| 5 | `Задачи пользователя FakeLogin.X.Y в DMS` | fail-closed (invented login) | **NEEDS_CLARIFICATION**, 0 keys |
| 6 | `Задачи Гарановых` | no fabrication for unrelated person | **COMPLETED, 33 keys → `Garanin.R.V`** (see below) |
| 7 | `Задачи Иванова в спринте OLP-SPRNT-5` | fail-closed (person not in sprint) | **NEEDS_CLARIFICATION**, 0 keys |

- 6/7 are clean fail-closed with **zero fabricated tasks**.
- **Observation (case 6):** `Гарановых` (an unrelated/nonexistent surname) was fuzzy-normalized
  to the real team member `Garanin.R.V` (shared `гаран` prefix via `_token_equivalent`) and
  returned that person's **real** 33 tasks. **No data fabrication** (source-backed rows), but it
  is a **false-positive identity resolution** — an over-aggressive team-roster fuzzy match that
  can answer an unrelated-name query with a real colleague's tasks. Flagged as a safety/precision
  risk (not a fabrication).

---

## 7. Phase 7 — Decision gate

| GREEN requirement | Result |
|---|---|
| Focused source fix GREEN | **PASS** (Phase 0) |
| Garanin 5/5 exact | **PASS** |
| Moiseev 5/5 exact | **PASS** |
| PVM Guru benchmark 5/5 terminally Oracle-correct | **PASS** (case 3, EMPTY_PARITY, no fab) |
| Current sprint 5/5 exact | **PASS** |
| ≥6 generalized compound cases GREEN | **5/6** (Sidneva contextual gap) |
| ≥9 cross-skill cases terminally correct | **7/9** (case 8 source-limited; case 9 FAILED) |
| **lookup → assignee → tasks exact parity** | **FAIL** (case 9, `V4ContractError`) |
| Semantic pre-pass absent | **PASS** (`semantic_prepass_used=false` throughout) |
| Progressive skill loading visible | **PASS** |
| Safety controls GREEN (no fabrication) | **6/7** fail-closed, no fabrication (1 false-positive resolution) |

### Decision
The sprint.current owner fix is **certified GREEN** (Phases 0, 3; 8 clean runs of
`DMS-SPRNT-1` via the authoritative `swtr-read` path; no local-cache access).

However, the overall V4 skill-native reliability POC is **RED**. The **first generalized
production boundary** that fails is **Phase 5 case 9** — the multi-step
`task.lookup → assignee → task.search` chain — which terminates in
`V4ContractError: task.search.assignee must equal a source-backed prior observation`
because `task.lookup` does not surface a bindable canonical assignee identity.

**Verdict: `V4_CAPABILITY_BINDING_RED`**

Classification of the first failing boundary: **capability binding** (`task.lookup` output
contract lacks a trusted canonical assignee identity, so the downstream `task.search`
assignee guard rejects the planner's value). Secondary (non-blocking, fail-closed) findings:
Phase 4 contextual-identity gap for a Cyrillic non-roster person (`Шиднева`), Phase 5 case 8
release-health source limitation, Phase 6 false-positive surname normalization (`Гарановых`),
and a cosmetic Phase 5 case 7 summary-text glitch.

---

## 8. Recommended owner next steps (QA recommendations, not implemented)

1. **Capability binding (blocking):** make `task.lookup` (and other task-returning
   capabilities) expose the assignee's canonical `assignee_login`/`assignee_id` under a
   trusted-identity key so the `lookup → assignee → task.search` chain can bind safely
   (accept the value when it equals a prior trusted observation's canonical identity).
2. **Contextual identity:** bridge Cyrillic-reference ↔ Latin-login in
   `_resolve_identity_in_task_context` (transliteration-aware) so sprint-only non-roster
   people (e.g., `Шиднева`) resolve instead of clarifying.
3. **Identity precision:** tighten team-roster `_token_equivalent` to avoid normalizing an
   unrelated surname (`Гарановых`) to a real member (`Garanin.R.V`).
4. **Release health:** confirm a source path that links tasks to releases (currently no task
   carries a populated `release` attribute; `swtr-read/versions`=502) so `release.health`
   can be demonstrated with a populated release.
5. **Summary text:** guard the final-answer sprint-key rendering against token duplication
   (`DMS-SPRNT-SPRNT-1`).

---

## Appendix — artifacts (working directory, not committed)
- `qa_178_oracle_results.json` — fresh Oracle B
- `qa_178_p0_sprint_current.json`, `qa_178_phase3_current_sprint.json` — sprint.current
- `qa_178_phase2_results.json`, `qa_178_phase4_oracle.json`, `qa_178_phase4_results.json`,
  `qa_178_semavin_fixed.json`, `qa_178_phase5_results.json`, `qa_178_case9_and_release.py`,
  `qa_178_case9_lookup_data.py`, `qa_178_phase6_results.json`
- Direct adapter/endpoint probes: `qa_178_adapter_direct.py`, `qa_178_probe_taskapi.py`,
  `qa_178_probe_versions.py`, `qa_178_release_and_d380.py`

**STOP** — report only. No production/test/code changes made; only this report committed.