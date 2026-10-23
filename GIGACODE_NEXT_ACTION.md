# A230R3 — FORSENSIC DIAGNOSTICS BEFORE SKILL QA

**GigaCode: READ-ONLY investigation ONLY. No production/test/Core/UI/MCP/config modifications; no code fixes, merges or commits. Do not start public-deploy/public-health-check QA yet. Report in chat and STOP.**

## Reproductions observed 2026-10-24
- «покажи списания Гаранина за 2 недели» -> wrong date clarification ("2 недели" not recognized).
- Follow-up «с 21.09.2026 по сегодня» -> wrong generic task.search filters (status/type/task created), loses worklog intent/person.
- «Покажи списания Гаранина в DMS за последние 2 недели» -> same generic task.search clarification despite valid person, space, rolling time.
- «Покажи списания Гаранина в активном спринте DMS» -> COMPLETED, 0 records/0 hours, 34 sprint tasks. Independently verify source-backed author/date/membership and full pagination; NEVER assume zero correct from this answer.
- «покажи задачи Гаранина в активном спринте по DMS» -> generic planner fallback, while identical Agataeva query finds 2 tasks. Isolate member identity/aliases and planner routing.
- Successful task query shows internal step/capability/arguments/data JSON in user-visible widget; UI renderer not sanitizing planner envelope.
- «Что именно нужно уточнить?» repeats generic task-search guidance instead of clarifying missing field.

## Proven baseline and limitations
- A230R2.2 person+date worklog capability is NOT IMPLEMENTED. Source audit did verify upstream POST /rest/api/timesheet/v1/report with bounded filter by author externalId and logged-on date.
- Current time_accounting_member.py supports member worklogs only with space+sprint through bounded per-task reads. Do not route person+date accounting into task.search_created.
- _task_live_handlers.py date parser has rolling one-week variants but not generic N weeks; that parser is for TASK CREATION, not a substitute for worklog dates.
- Frozen 6 Core V4 files MUST stay byte-identical to checkpoint 6fb335d.

## Required gates
P0. Record TESTED_HEAD, running services/ports, flags, isolated session, hash Core six files.
P1. Trace planner typed steps and initial/follow-up intent for each case. Show first failing boundary: period parser, skill/capability selection, clarification memory, entity resolver, fallback, completion gate.
P2. Compare Garanin and Agataeva task searches in same DMS active sprint; inspect canonical logins, plan, bounded source reads; no unscoped scans.
P3. Bounded independent REAL AS21 oracle for Garanin worklog-author/date and DMS sprint. Verify whether 0 hours is true with source records and pagination; if no evidence say UNVERIFIED not factual zero. Prior 14 records in Oct source audit are a different scope; never hardcode.
P4. Inspect exact frontend component rendering raw internal step JSON (not only V4ResultPanel), report safe UI formatter seam, do not leak task descriptions.
P5. Report why generic filter suggestions incorrectly appear on worklog or missing-context queries; identify requirements for typed clarification and "what should I clarify?" answer.
P6. Capture latency bottlenecks from existing traces if possible, not a load test.

## Deliverable
Chat-only concise table: symptom, expected, first failing boundary, CONFIRMED/LIKELY/UNVERIFIED, severity, smallest additive non-Core fix. Distinguish **not yet implemented** from regressions. Recommend owner fix order: (1) MCP→Task API→member.worklogs_period; (2) rolling N-week parser + date semantics + continuation; (3) member/task routing; (4) zero-result completeness guard; (5) UI JSON envelope; (6) independent A/B regression. Do not implement or alter GIGACODE_NEXT_ACTION.md.

## Short command
Execute A230R3-FORENSIC from GIGACODE_NEXT_ACTION.md. Read-only. Analyze 7 cases, bounded REAL AS21 oracle, identity/period routing, zero-hours, UI raw JSON. Return report, STOP.
