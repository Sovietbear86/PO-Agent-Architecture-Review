# GigaCode — Current Action

## ACTIVE: Assignment A229U2R — hardened production rich-text re-gate

Role: QA/browser tester only. Do not modify code.

Previous A229U2 RED:
- base adapter normalization was correct;
- production exact lookup bypassed it through `HardenedProductionTaskApiAS21Adapter._map_raw_unit`;
- raw rich-text JSON leaked into canonical `Task.description`;
- raw description provenance was absent from hardened `source_data`.

Owner fix:
- hardened mapper now reuses `_rich_text_to_plain`;
- raw source description is preserved in `source_data["description"]`;
- direct production-class regression added;
- no Core/planner/plugin/frontend changes.

## P0 — integrity/tests

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove production delta after prior A229U2 RED is limited to:
   - `src/po_agent/adapters/hardened_production_task_api.py`;
   - new hardened-adapter regression;
   - docs/assignment.
3. Prove 0 Agent Core/planner/plugin/frontend changes.
4. Run:
   - `tests/test_hardened_production_task_rich_text.py`;
   - focused `tests/test_task_api_as21_adapter.py`;
   - full V4 blast-radius;
   - frontend build.
5. Any regression => RED STOP.

## P1 — blocking production point-read case

Use live DMS-333 if still available.

Before Agent query:
- fetch independent raw exact Task API observation;
- confirm source description is structured/serialized rich text.

Then:
`Покажи задачу DMS-333`

Require:
- status COMPLETED;
- canonical `task.description` is human-readable;
- no visible serialized JSON/doc tree;
- raw original source description is still present in source_data/evidence path for audit;
- normalized content matches the human-visible text/link semantics of the raw source;
- no fabrication or dropped link meaning.

Run at least 3 times. All 3 must be stable.

## P2 — drawer rendering

Open DMS-333 from Tasks UI.

Require:
- upper Description block shows readable source text;
- no `type/doc/content/attrs/marks/textAlign` keys visible;
- source link meaning remains visible;
- A229U1R loading indicator retained;
- exact task lookup cardinality remains one per drawer open.

## P3 — Task Intelligence propagation

Test:
- Резюме;
- Качество;
- Что не хватает.

Require:
- business answer is based on normalized description;
- structured fields such as description/goal/what_to_do do not expose raw rich-text JSON;
- no raw document tree appears in tables;
- internal source_data remains hidden from user UI;
- links/content remain semantically represented.

## P4 — normalization controls

Run controlled checks through the hardened production mapper:
1. plain text;
2. rich-text object;
3. serialized rich-text JSON string;
4. malformed JSON-looking plain text;
5. long description.

Require:
- plain/long text preserved without truncation;
- object and serialized forms normalize equivalently;
- malformed text fails soft and stays visible;
- raw source description preserved in source_data;
- unknown structural nodes never stringify the full raw object into canonical description.

## P5 — architecture/source audit

Require:
- deterministic adapter-only normalization;
- 0 LLM parsing of description;
- 0 Core/planner/plugin/frontend delta;
- 0 product/task-specific branch;
- raw source provenance preserved;
- no mutation/local fallback/tenant scan introduced.

## Verdict

Exactly one:
- `AGENT_CORE_V4_RICH_TEXT_DESCRIPTION_GREEN_A229U2R`
- `AGENT_CORE_V4_RICH_TEXT_DESCRIPTION_RED_A229U2R`

If GREEN:
- recommend checkpoint `checkpoint/v4-task-details-richtext-green-a229u2r`;
- owner may sync certified A229U1+A229U2 delta to public/community repo;
- resume A229R1 latency verification on the new certified HEAD.

If RED:
- preserve first failing boundary and STOP.

Do not modify code.
