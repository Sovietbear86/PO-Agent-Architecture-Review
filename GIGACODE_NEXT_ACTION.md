# GigaCode — Current Action

## ACTIVE: Assignment A229U2 — AS21 rich-text description re-gate

Role: QA/browser tester only. Do not modify code.

Context:
- A229U1R was GREEN for source-backed description/loading/intelligence rendering.
- Manual PO review found that REAL AS21 may return description as a rich-text document tree / serialized JSON document.
- Owner fixed only the AS21 adapter normalization boundary.
- Agent Core/planner/plugins remain unchanged.
- Public/community sync remains blocked until this gate is GREEN.

## P0 — integrity/build/tests

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove owner production delta after A229U1R is limited to:
   - `src/po_agent/adapters/task_api.py`;
   - adapter regression tests;
   - docs/assignment.
3. Prove 0 Agent Core/planner/plugin/frontend layout changes.
4. Run:
   - focused `test_task_api_as21_adapter.py`;
   - full V4 blast-radius (retain 242/242 or newer exact total if only new adapter tests add count);
   - frontend `npm run build`.
5. Any regression => RED STOP.

## P1 — REAL AS21 description normalization

Use a REAL task whose description is stored in the structured rich-text format; DMS-333 from PO evidence is preferred if still available.

Obtain an independent raw exact AS21/Task API observation first.

Require:
- raw source payload really contains a rich-text document structure or serialized JSON structure;
- canonical exact task lookup returns readable `Task.description`, not the JSON/document tree;
- raw structure is still present in source/evidence data for audit;
- no source content is fabricated;
- paragraphs remain separated;
- human-visible text is preserved;
- links remain understandable/clickable in meaning (at minimum label + URL when distinct).

## P2 — task drawer

Open the same task in Tasks UI.

Require:
- upper `Описание` block contains readable text, not `{"type":"doc"...}`;
- no `content/attrs/marks/textAlign` structural keys are visible;
- empty description still renders `Описание отсутствует`;
- plain-text source descriptions remain unchanged;
- description loading state from A229U1R is retained.

## P3 — Task Intelligence propagation

For the same rich-text task test:
- Резюме;
- Качество;
- Что не хватает.

Require:
- generated business answer is based on normalized readable description;
- structured data fields such as `goal`, `what_to_do`, `description` do not contain serialized rich-text JSON;
- no raw `type=doc/content/attrs/marks` tree is displayed in readable tables;
- links/text referenced in the source remain represented correctly;
- internal `_agent_core_v4` / source_data remain hidden as certified in A229U1R.

## P4 — normalization controls

Test three controlled source shapes:
1. normal plain text;
2. rich-text object;
3. serialized rich-text JSON string.

Require:
- plain text byte/content semantics retained (no unwanted rewriting/truncation);
- object and serialized forms normalize to equivalent human-readable text;
- long descriptions remain untruncated;
- malformed JSON-looking plain text fails soft and is preserved as text, not dropped;
- unknown structural nodes do not leak full Python/JSON object representation into canonical description.

## P5 — architecture/source audit

Require:
- canonical raw AS21 payload preserved in source_data;
- normalization is deterministic adapter logic only;
- 0 Core/planner/plugin changes;
- no LLM used to parse description;
- no product/task-specific special case;
- no mutation/local fallback/tenant scan introduced.

## Verdict

Exactly one:
- `AGENT_CORE_V4_RICH_TEXT_DESCRIPTION_GREEN_A229U2`
- `AGENT_CORE_V4_RICH_TEXT_DESCRIPTION_RED_A229U2`

If GREEN:
- recommend checkpoint `checkpoint/v4-task-details-richtext-green-a229u2`;
- owner may then sync A229U1+A229U2 certified UI/adapter delta to public/community repo;
- resume A229R1 latency verification on this certified HEAD.

If RED:
- preserve first failing boundary and STOP.

Do not modify code.
