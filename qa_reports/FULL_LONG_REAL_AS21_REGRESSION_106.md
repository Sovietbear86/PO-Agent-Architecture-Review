# FULL_LONG_REAL_AS21_REGRESSION_106

**Generated:** 2026-09-01T08:48:03.148667
**Git HEAD:** 6df531789c936b36d70a03a1dec45300b9bd43af
**Execution Time:** 2026-09-01T08:48:03.148678

## EXECUTIVE SUMMARY

| Metric | Count |
|--------|-------|
| **Total Skills Tested** | 54 |
| **PASS** | 23 |
| **EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE** | 6 |
| **SOURCE_DATA_NOT_AVAILABLE_FOR_VALID_TEST** | 0 |
| **EXPECTED_CLARIFICATION** | 25 |
| **FAIL** | 0 |
| **BLOCKED** | 0 |

## FINAL VERDICT

> **FULL_REGRESSION_GREEN_READY_FOR_NEXT_PLAN_STEP**

## FAILURE TRIAGE

### EXPECTED_CLARIFICATION

- task-search-attachments
- task-search-excel
- task-search-pdf
- task-search-msg
- task-search-assignee
- task-search-status
- task-search-release
- task-aging
- task-blocker-analysis
- team-workload
- team-wip
- team-blocked
- team-capacity
- team-competency-match
- team-bottlenecks
- team-distribution
- release-health
- release-scope
- release-progress
- release-blockers
- release-dependencies
- release-risk-queue
- po-status-report
- po-reminder-draft
- po-local-task-draft

### EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE

- task-summary
- sprint-carryover
- sprint-scope-change
- sprint-predictability
- release-forecast
- po-daily-brief

## SOURCE INTEGRITY COUNTERS

- **sprint2_tasks_available:** 0
- **sprint1_tasks_available:** 0
- **dms_space_available:** 1
- **olp_space_available:** 1
- **pass_count:** 23
- **clarification_count:** 25
- **source_unavailable_count:** 6

## ALL SKILL TEST RESULTS

### task-lookup

- **Natural Query:** Покажи задачу DMS-261
- **Resolved Skill:** task-lookup
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** {"oracle_task_count": 0, "oracle_task_keys": [], "matches_oracle": null}
- **Elapsed Time:** 3008ms
- **Classification:** PASS
- **Retry Count:** 0

### task-search

- **Natural Query:** Покажи задачи со словом 'тест' в DMS-SPRNT-2
- **Resolved Skill:** task-search
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-324, DMS-346, DMS-345, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 5, "task_keys": ["DMS-324", "DMS-346", "DMS-345", "DMS-335", "DMS-341"], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 12643ms
- **Classification:** PASS
- **Retry Count:** 0

### task-search-attachments

- **Natural Query:** Покажи задачи в DMS-SPRNT-2 с вложениями
- **Resolved Skill:** task-search-attachments
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-search-excel

- **Natural Query:** Покажи задачи в DMS-SPRNT-2 с Excel файлами
- **Resolved Skill:** task-search-excel
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-search-pdf

- **Natural Query:** Покажи задачи в DMS-SPRNT-2 с PDF файлами
- **Resolved Skill:** task-search-pdf
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-search-msg

- **Natural Query:** Покажи задачи в DMS-SPRNT-2 с MSG файлами
- **Resolved Skill:** task-search-msg
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-search-assignee

- **Natural Query:** Покажи задачи в DMS-SPRNT-2, назначенные Гаранину
- **Resolved Skill:** task-search-assignee
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-search-status

- **Natural Query:** Покажи задачи в DMS-SPRNT-2 со статусом OPEN
- **Resolved Skill:** task-search-status
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-search-sprint

- **Natural Query:** Покажи задачи в DMS-SPRNT-2
- **Resolved Skill:** task-search-sprint
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-376, DMS-354, DMS-347, DMS-374, DMS-373, DMS-274, DMS-352, DMS-359, DMS-356, DMS-357, DMS-268, DMS-355, DMS-338, DMS-324, DMS-261, DMS-269, DMS-346, DMS-270, DMS-345, DMS-340, DMS-253, DMS-344, DMS-343, DMS-223, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 26, "task_keys": ["DMS-376", "DMS-354", "DMS-347", "DMS-374", "DMS-373", "DMS-274", "DMS-352", "DMS-359", "DMS-356", "DMS-357", "DMS-268", "DMS-355", "DMS-338", "DMS-324", "DMS-261", "DMS-269", "DMS-346", "DMS-270", "DMS-345", "DMS-340", "DMS-253", "DMS-344", "DMS-343", "DMS-223", "DMS-335", "DMS-341"], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 12043ms
- **Classification:** PASS
- **Retry Count:** 0

### task-search-release

- **Natural Query:** Покажи задачи из релиза 1.6.0 в DMS
- **Resolved Skill:** task-search-release
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-search-product

- **Natural Query:** Покажи все задачи в пространстве DMS
- **Resolved Skill:** task-search-product
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": false}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2024ms
- **Classification:** PASS
- **Retry Count:** 0

### task-summary

- **Natural Query:** Резюмируй задачу DMS-261
- **Resolved Skill:** task-summary
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** llm_unavailable_deterministic_summary
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 3444ms
- **Classification:** EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE
- **Retry Count:** 0

### task-quality

- **Natural Query:** Оцени качество задачи DMS-261
- **Resolved Skill:** task-quality
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261, DMS-261, DMS-261, DMS-261, DMS-261, DMS-261, DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 3459ms
- **Classification:** PASS
- **Retry Count:** 0

### task-missing-requirements

- **Natural Query:** Покажи недостающие элементы в задаче DMS-261
- **Resolved Skill:** task-missing-requirements
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 3113ms
- **Classification:** PASS
- **Retry Count:** 0

### task-acceptance-analysis

- **Natural Query:** Проанализируй критерии приемки задачи DMS-261
- **Resolved Skill:** task-acceptance-analysis
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2997ms
- **Classification:** PASS
- **Retry Count:** 0

### task-dependency-analysis

- **Natural Query:** Покажи зависимости задачи DMS-261
- **Resolved Skill:** task-dependency-analysis
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2534ms
- **Classification:** PASS
- **Retry Count:** 0

### task-history

- **Natural Query:** Покажи историю задачи DMS-261
- **Resolved Skill:** task-history
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 5139ms
- **Classification:** PASS
- **Retry Count:** 0

### task-time-in-status

- **Natural Query:** Покажи сколько времени задача DMS-261 провела в каждом статусе
- **Resolved Skill:** task-time-in-status
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 4876ms
- **Classification:** PASS
- **Retry Count:** 0

### task-aging

- **Natural Query:** Покажи старые активные задачи в DMS-SPRNT-2
- **Resolved Skill:** task-aging
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-blocker-analysis

- **Natural Query:** Покажи блокировки в DMS-SPRNT-2
- **Resolved Skill:** task-blocker-analysis
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### task-similar

- **Natural Query:** Покажи похожие задачи для DMS-261
- **Resolved Skill:** task-similar
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, DMS-261, DMS-261
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2927ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-health

- **Natural Query:** Оцени здоровье спринта DMS-SPRNT-2
- **Resolved Skill:** sprint-health
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-376, DMS-354, DMS-347, DMS-374, DMS-373, DMS-274, DMS-352, DMS-359, DMS-356, DMS-357, DMS-268, DMS-355, DMS-338, DMS-324, DMS-261, DMS-269, DMS-346, DMS-270, DMS-345, DMS-340, DMS-253, DMS-344, DMS-343, DMS-223, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 26, "task_keys": ["DMS-376", "DMS-354", "DMS-347", "DMS-374", "DMS-373", "DMS-274", "DMS-352", "DMS-359", "DMS-356", "DMS-357", "DMS-268", "DMS-355", "DMS-338", "DMS-324", "DMS-261", "DMS-269", "DMS-346", "DMS-270", "DMS-345", "DMS-340", "DMS-253", "DMS-344", "DMS-343", "DMS-223", "DMS-335", "DMS-341"], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 12497ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-current

- **Natural Query:** Покажи текущий спринт в DMS
- **Resolved Skill:** sprint-current
- **Capability Arguments:** {}
- **Evidence IDs:** DMS
- **Response Status:** 200
- **Response Warnings:** current_sprint_not_found
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** {"oracle_task_count": 0, "oracle_task_keys": [], "matches_oracle": null}
- **Elapsed Time:** 5230ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-scope

- **Natural Query:** Покажи текущий спринт DMS-SPRNT-2
- **Resolved Skill:** sprint-scope
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-376, DMS-354, DMS-347, DMS-374, DMS-373, DMS-274, DMS-352, DMS-359, DMS-356, DMS-357, DMS-268, DMS-355, DMS-338, DMS-324, DMS-261, DMS-269, DMS-346, DMS-270, DMS-345, DMS-340, DMS-253, DMS-344, DMS-343, DMS-223, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 26, "task_keys": ["DMS-376", "DMS-354", "DMS-347", "DMS-374", "DMS-373", "DMS-274", "DMS-352", "DMS-359", "DMS-356", "DMS-357", "DMS-268", "DMS-355", "DMS-338", "DMS-324", "DMS-261", "DMS-269", "DMS-346", "DMS-270", "DMS-345", "DMS-340", "DMS-253", "DMS-344", "DMS-343", "DMS-223", "DMS-335", "DMS-341"], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** {"oracle_task_count": 0, "oracle_task_keys": [], "matches_oracle": null}
- **Elapsed Time:** 12918ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-velocity

- **Natural Query:** Покажи скорость спринта DMS-SPRNT-2
- **Resolved Skill:** sprint-velocity
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-376, DMS-354, DMS-347, DMS-374, DMS-373, DMS-274, DMS-352, DMS-359, DMS-356, DMS-357, DMS-268, DMS-355, DMS-338, DMS-324, DMS-261, DMS-269, DMS-346, DMS-270, DMS-345, DMS-340, DMS-253, DMS-344, DMS-343, DMS-223, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** {"oracle_task_count": 0, "oracle_task_keys": [], "matches_oracle": null}
- **Elapsed Time:** 12997ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-throughput

- **Natural Query:** Покажи пропускную способность спринта DMS-SPRNT-2
- **Resolved Skill:** sprint-throughput
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-354, DMS-347, DMS-268, DMS-324, DMS-346, DMS-270, DMS-340, DMS-223
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 12915ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-wip

- **Natural Query:** Покажи WIP в спринте DMS-SPRNT-2
- **Resolved Skill:** sprint-wip
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-376, DMS-373, DMS-274, DMS-352, DMS-356, DMS-355, DMS-338, DMS-261, DMS-345, DMS-253, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 12, "task_keys": ["DMS-376", "DMS-373", "DMS-274", "DMS-352", "DMS-356", "DMS-355", "DMS-338", "DMS-261", "DMS-345", "DMS-253", "DMS-335", "DMS-341"], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 13489ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-cycle-time

- **Natural Query:** Покажи время цикла спринта DMS-SPRNT-2
- **Resolved Skill:** sprint-cycle-time
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-376, DMS-354, DMS-347, DMS-374, DMS-373, DMS-274, DMS-352, DMS-359, DMS-356, DMS-357, DMS-268, DMS-355, DMS-338, DMS-324, DMS-261, DMS-269, DMS-346, DMS-270, DMS-345, DMS-340, DMS-253, DMS-344, DMS-343, DMS-223, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** cycle_time_insufficient_history
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 29014ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-lead-time

- **Natural Query:** Покажи время выполнения спринта DMS-SPRNT-2
- **Resolved Skill:** sprint-lead-time
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-376, DMS-354, DMS-347, DMS-374, DMS-373, DMS-274, DMS-352, DMS-359, DMS-356, DMS-357, DMS-268, DMS-355, DMS-338, DMS-324, DMS-261, DMS-269, DMS-346, DMS-270, DMS-345, DMS-340, DMS-253, DMS-344, DMS-343, DMS-223, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** lead_time_insufficient_history
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 29991ms
- **Classification:** PASS
- **Retry Count:** 0

### sprint-carryover

- **Natural Query:** Покажи перенос спринта DMS-SPRNT-2
- **Resolved Skill:** sprint-carryover
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** source_capability_unavailable
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2ms
- **Classification:** EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE
- **Retry Count:** 0

### sprint-scope-change

- **Natural Query:** Покажи изменения спринта DMS-SPRNT-2
- **Resolved Skill:** sprint-scope-change
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** source_capability_unavailable
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 13973ms
- **Classification:** EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE
- **Retry Count:** 0

### sprint-predictability

- **Natural Query:** Покажи предсказуемость спринта DMS-SPRNT-2
- **Resolved Skill:** sprint-predictability
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-376, DMS-354, DMS-347, DMS-374, DMS-373, DMS-274, DMS-352, DMS-359, DMS-356, DMS-357, DMS-268, DMS-355, DMS-338, DMS-324, DMS-261, DMS-269, DMS-346, DMS-270, DMS-345, DMS-340, DMS-253, DMS-344, DMS-343, DMS-223, DMS-335, DMS-341
- **Response Status:** 200
- **Response Warnings:** authoritative_commitment_baseline_unavailable, current_scope_completion_proxy, learned_policy_applied
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 27696ms
- **Classification:** EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE
- **Retry Count:** 0

### sprint-risk-queue

- **Natural Query:** Покажи задачи, требующие внимания PO в DMS-SPRNT-2
- **Resolved Skill:** sprint-risk-queue
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-352, DMS-335, DMS-253, DMS-261, DMS-341, DMS-345, DMS-338, DMS-269, DMS-274, DMS-355, DMS-343, DMS-344, DMS-356, DMS-357, DMS-359
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 48902ms
- **Classification:** PASS
- **Retry Count:** 0

### team-workload

- **Natural Query:** Покажи нагрузку команды в DMS-SPRNT-2
- **Resolved Skill:** team-workload
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### team-wip

- **Natural Query:** Покажи WIP по членам команды в DMS-SPRNT-2
- **Resolved Skill:** team-wip
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### team-blocked

- **Natural Query:** Покажи заблокированную работу в DMS-SPRNT-2
- **Resolved Skill:** team-blocked
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### team-capacity

- **Natural Query:** Покажи capacity команды в DMS-SPRNT-2
- **Resolved Skill:** team-capacity
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### team-competency-match

- **Natural Query:** Покажи соответствие компетенций для DMS-SPRNT-2
- **Resolved Skill:** team-competency-match
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### team-assignee-recommendation

- **Natural Query:** Порекомендуй исполнителя для задачи DMS-261
- **Resolved Skill:** team-assignee-recommendation
- **Capability Arguments:** {}
- **Evidence IDs:** DMS-261, Bezrukov.P.S
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": true}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 3517ms
- **Classification:** PASS
- **Retry Count:** 0

### team-bottlenecks

- **Natural Query:** Покажи узкие места в DMS-SPRNT-2
- **Resolved Skill:** team-bottlenecks
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### team-distribution

- **Natural Query:** Покажи распределение задач по компетенциям в DMS-SPRNT-2
- **Resolved Skill:** team-distribution
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### release-health

- **Natural Query:** Оцени здоровье релиза 1.6.0 в DMS
- **Resolved Skill:** release-health
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### release-scope

- **Natural Query:** Покажи охват релиза 1.6.0 в DMS
- **Resolved Skill:** release-scope
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### release-progress

- **Natural Query:** Покажи прогресс релиза 1.6.0 в DMS
- **Resolved Skill:** release-progress
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### release-blockers

- **Natural Query:** Покажи блокировки релиза 1.6.0 в DMS
- **Resolved Skill:** release-blockers
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### release-dependencies

- **Natural Query:** Покажи зависимости релиза 1.6.0 в DMS
- **Resolved Skill:** release-dependencies
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### release-risk-queue

- **Natural Query:** Покажи риски релиза 1.6.0 в DMS
- **Resolved Skill:** release-risk-queue
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### release-forecast

- **Natural Query:** Покажи прогноз релиза 1.6.0 в DMS
- **Resolved Skill:** release-forecast
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** source_capability_unavailable
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE
- **Retry Count:** 0

### portfolio-overview

- **Natural Query:** Покажи обзор портфеля
- **Resolved Skill:** portfolio-overview
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": false}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2326ms
- **Classification:** PASS
- **Retry Count:** 0

### po-attention-queue

- **Natural Query:** Покажи очередь внимания PO
- **Resolved Skill:** po-attention-queue
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** None
- **Normalized Business Facts:** {"task_count": 0, "task_keys": [], "has_answer": true, "has_evidence": false}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2223ms
- **Classification:** PASS
- **Retry Count:** 0

### po-daily-brief

- **Natural Query:** Создай ежедневный бриф для PO
- **Resolved Skill:** po-daily-brief
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** llm_unavailable_deterministic_daily_brief
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 2105ms
- **Classification:** EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE
- **Retry Count:** 0

### po-status-report

- **Natural Query:** Создай отчет о статусе релиза 1.6.0
- **Resolved Skill:** po-status-report
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### po-reminder-draft

- **Natural Query:** Создай черновик напоминания для PO
- **Resolved Skill:** po-reminder-draft
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0

### po-local-task-draft

- **Natural Query:** Создай черновик задачи для PO
- **Resolved Skill:** po-local-task-draft
- **Capability Arguments:** {}
- **Evidence IDs:** None
- **Response Status:** 200
- **Response Warnings:** clarification_required, clarification_replay
- **Normalized Business Facts:** {}
- **Oracle B Facts:** N/A
- **Elapsed Time:** 1ms
- **Classification:** EXPECTED_CLARIFICATION
- **Retry Count:** 0
