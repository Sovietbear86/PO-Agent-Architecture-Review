# GigaCode Next Action

## A229R2U — Synthesis UX and multi-intent research

Only QA. No production code modifications.

Certified baseline: checkpoint/v4-synthesis-elision-green-a229r2i at 36e814511de880f40703fa6b4dcaeb874b18722c.

Owner changes: v4_synthesis_elision.py now reads task_keys_sample and task_key_count, emitting key lists only when complete. Two regression tests added. Feature flag PO_AGENT_V4_SYNTHESIS_ELISION remains false by default.

P0: Pull current branch, record HEAD, check clean tree and frozen Core. Run focused elision tests, complete V4 suite, relevant Task API source suites, frontend build; require no failures.

P1: Flag ON real AS21 browser checks: small result set has exact complete key list in prose and cards, result set >20 does not misrepresent truncated sample as full; zero remains zero. Check source oracle, no source-call change, no browser errors.

P2: Compare flag OFF/ON for tasks of Kalachanov in WMB, DMS-267 lookup, DMS-267 hierarchy, Semavin DMS open defects since 30.09.2026, DMS September sprint in-progress tasks, incomplete period clarification and continuation. Record correctness, UX, model-call count and p50/p90 wall. The ON state must remove one synthesis call for eligible completed results, never on clarification/failure.

P3: RESEARCH ONLY — multi-intent limitation. Run 3 valid trials each:
- Покажи задачу DMS-267 и её иерархию
- Покажи задачи Калачанова в WMB и задачи Семавина в DMS
- Сравни незавершённые задачи в DMS и OLP
- Покажи иерархию DMS-267 и связанные с ней задачи

For each establish independent REAL AS21 oracle for every subgoal and report discovered skills, executed terminal capabilities, omitted goal if any, completion contract, and first failing boundary. Evaluate plugin/catalog composition, an API goal-coverage clarification guard, and a future V5 deep sidecar. Do not implement or claim multi-intent fixed. Do not introduce phrase routers.

P4: Report UX verdict AGENT_CORE_V4_SYNTHESIS_UX_GREEN_A229R2U or AGENT_CORE_V4_SYNTHESIS_UX_RED_A229R2U. Multi-intent findings must be separately marked OPEN if any subgoals remain unfulfilled. Recommend whether flag can be enabled by default; do not flip it.

Commit report at po-agent-platform-v2/qa_reports/AGENT_CORE_V4_SYNTHESIS_UX_MULTI_INTENT_A229R2U.md. If RED record first failing boundary and stop. Core, production code, and current flag default remain unchanged.
