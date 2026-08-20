# Core-8 Hardening Freeze

Effective immediately, Gate E expansion is paused.

Reason: a live composite query (`Покажи открытые задачи Гаранина в последнем спринте по DMS`) exposed a false-empty risk not covered by the previous Core-8 acceptance suite.

Authoritative temporary sequence:
1. execute `qa_assignments/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md` against real AS21 data;
2. inspect logs and fix source-contract / grounding / semantic / runtime defects;
3. repeat until `CORE8_REAL_QUERY_HARDENING_GREEN = YES`;
4. only then resume Gate E from Wave 1.

No new skills, frontend work, or broader Gate-E implementation should advance while this freeze is active.

Important distinction: source-contract/adapter defects must be fixed in code and must NOT be 'learned' by the Learning Loop. Clarification/default semantics may enter Learning Loop only after source facts and grounding are proven correct.