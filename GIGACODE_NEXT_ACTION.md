# GigaCode — CURRENT NEXT ACTION

## A230R3.4-R2-UI-ENVELOPE-QA — Independent regression re-gate

**QA ONLY.** Do not modify code, tests, docs, configuration, V4 Core, runtime source, Git history or Public repository. Do not auto-fix, commit or merge. Fetch origin and establish exact `LOCAL_HEAD = REMOTE_HEAD = TESTED_HEAD` before testing; preserve dirty worktree safely (STOP on conflicts, no reset --hard). Frozen Agent Core V4 6/6 byte-identical vs checkpoint `6fb335d`.

### Prior QA RED and owner minimal fix
A230R3.4-UI-ENVELOPE-QA confirmed primary raw planner JSON leakage fixed, but found a regression: `team.assignee_recommendation` emits `data.candidates` and the new renderer had omitted `candidates` from its allowlist, silently losing ranked recommendations. Owner added `candidates` back to `BUSINESS_COLLECTIONS` in **frontend-only** `po-agent-platform-v2/frontend/src/components/V4ResultPanel.tsx` (owner commit `1c5f563`). No Core/API/MCP/source changes.

### Required QA
1. Fetch and record exact TESTED_HEAD, confirm production delta restricted to frontend component. All six Core files remain byte-identical to checkpoint.
2. Verify `data.candidates` for `team.assignee_recommendation` now renders ranked member rows, not zero rows; `data.matches` for `team.competency_match` remains rendered. Check both top-level data and `results[i].data` envelopes. The user must not lose rows due to unsafe allowlist omissions.
3. Verify all supported business lists `tasks, sprints, matches, candidates, queue, timeline, durations, risks, risk_queue, dependencies, members, worklogs, entries`. A raw `results` collection remains intentionally hidden. Unknown planner/tool envelopes must NEVER be stringified into UI. Verify task key/title and worklogs remain readable.
4. Run frontend `npm run build`; browser DOM smoke with authorized read-only REAL AS21 cases: task search, ranked assignee recommendations, member competencies, worklogs, sprint result, empty/partial/error. Check no raw `capability_id`, `arguments`, `step`, `widget:`, `kind:`, `JSON.stringify` output. Evidence accordion shows `Источники` accurately. No data leaks in visible normal user panel.
5. Confirm original `Pages.tsx` QualityPage raw JSON issue is **pre-existing separate item**, not this component's RED unless newly affected. No scope creep.
6. Run relevant V4 full regression (expected baseline 326), Task API SWTR (69) and report frontend build. Treat environmental LLM failures separately and don't hide newly induced failures.
7. Report test matrix, counts and exact first failing boundary if RED. Do not change files. **No merge to Public until GREEN.**

### Command
Run A230R3.4-R2-UI-ENVELOPE-QA from GIGACODE_NEXT_ACTION.md. Independent QA only, current HEAD, full build + UI business rows/no raw JSON + Core 6/6; report and STOP.
