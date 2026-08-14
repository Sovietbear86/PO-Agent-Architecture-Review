# PO Agent Platform v2.1 — ADDENDUM 01
## Clarification Engine + Skill Registry + Skill Evolution

**Status:** обязательное дополнение к уже реализованному v2.1.  
**Цель:** добавить уточняющие вопросы, явные версионируемые skills и их контролируемую эволюцию через существующий AI PDLC. Старое приложение и уже реализованные шаги не пересоздавать.

# 1. Целевая схема

```text
User Request
  -> Intent Router
  -> Context Resolver
       -> если данных недостаточно: Clarification Engine
          -> Session Memory / Pending Request
          -> ответ пользователя
          -> повторный Context Resolve
       -> если данных достаточно: Skill Resolver
  -> Skill Executor
  -> Existing Capabilities
  -> Result
  -> Trace / History / Feedback / Eval
  -> Failure Miner
  -> Skill Improvement Candidate
  -> Shadow Eval
  -> Regression Gate
  -> Human Approval
  -> Skill Registry vN+1
```

# 2. Context Resolver

Добавить явную модель `ResolvedContext`: product, sprint_id, release_id, task_id, member_login, date range, attachment type и другие уже существующие сущности. Для каждого значения желательно хранить источник: `current_request`, `clarification_answer`, `session_memory`, `deterministic_lookup`, `approved_curated_memory`.

Приоритет:
`явный текущий ввод > ответ на уточнение > валидная session memory > approved curated memory/default > unknown`.

Старый session context никогда не должен переопределять явный текущий запрос.

Результат resolver должен содержать: resolved context, missing_fields, ambiguous_fields, conflicts, confidence и needs_clarification. Для обязательных полей policy важнее confidence LLM.

# 3. Clarification Engine

Если обязательный контекст отсутствует или неоднозначен, Orchestrator не должен гадать. Возвращать нормальный статус `NEEDS_CLARIFICATION`, а не ошибку.

`ClarificationRequest` должен содержать: clarification_id, reason, missing_fields, question, optional deterministic options, original_intent, original_query.

Вопросы короткие и предметные. Например: «По какому продукту показать velocity — OLP или DataMarts?». Если допустимые варианты можно получить кодом, использовать их; LLM не должен придумывать варианты.

Не спрашивать, если ответ безопасно дать по всем объектам, существует документированный harmless default, значение явно известно из текущей session memory или недостающий параметр не влияет на корректность.

# 4. Clarification Loop и Pending Request

Поддержать:
`request -> NEEDS_CLARIFICATION -> user answer -> merge with pending request -> resolve -> execute`.

Пользователь не должен повторять исходный запрос.

Session Memory расширить `pending_request`: original_query, intent, extracted_entities, missing_fields, clarification_id, created_at, expires_at. После успешного выполнения pending state закрывается. Просроченное состояние не влияет на новые запросы.

Явные ответы на уточнение могут временно обновлять current_product/current_sprint/current_release, но не должны автоматически попадать в Curated Memory.

# 5. Skill Model

Skill — не prompt, а версионируемое декларативное описание способа решения класса задач.

Минимальные поля:
- skill_id
- name
- version
- status: candidate/active/deprecated/rejected
- intents
- description
- required_context
- optional_context
- clarification policy
- allowed capabilities
- workflow
- output contract
- prompt references
- fallback policy
- eval tags/version metadata

Пример логики skill `sprint_health`: resolve_context -> load_sprint -> calculate_metrics -> evaluate_risks -> synthesize_response. Расчёты остаются в существующих deterministic capabilities.

Создать initial skills минимум для: task_search, task_summary, task_quality, sprint_health, velocity, team_workload, competency_match, release_health, help.

# 6. Skill Registry / Resolver / Executor

Skill Registry загружает и валидирует определения, хранит версии и active version.

Skill Resolver предпочитает deterministic `intent -> skill`. LLM допускается только при реально неоднозначном высокоуровневом запросе и выбирает строго из allowlist.

Skill Executor:
1. получает валидированный Skill;
2. проверяет required context;
3. разрешает только declared capabilities;
4. исполняет workflow;
5. собирает evidence;
6. возвращает typed result;
7. пишет skill_id/version в trace.

LLM не может сгенерировать произвольный tool/capability для исполнения.

# 7. Trace, Feedback и Failure Taxonomy

Расширить trace:
- skill_id
- skill_version
- context_sources
- clarification_count
- clarification_ids
- pending_request_used
- skill_execution_steps

Расширить feedback/failures:
- CONTEXT_RESOLUTION_ERROR
- MISSING_CLARIFICATION
- UNNECESSARY_CLARIFICATION
- CLARIFICATION_LOOP_ERROR
- SKILL_SELECTION_ERROR
- SKILL_CONTRACT_ERROR
- SKILL_WORKFLOW_ERROR
- SKILL_KNOWLEDGE_GAP

Feedback должен ссылаться на trace_id, skill_id и skill_version.

# 8. Skill Evolution через AI PDLC

Разрешённые Improvement Candidates:
- required/optional context change
- clarification policy
- intent/alias mapping
- workflow step
- capability allowlist
- prompt reference
- output constraint
- example/eval
- новый skill

Нельзя изменять active Skill непосредственно во время runtime.

`SkillImprovementCandidate`: candidate_id, skill_id, base_version, proposed_version, linked traces/evals, failure categories, change_type, rationale, proposed_definition, expected_benefit, risk_level, status.

Не создавать candidate после каждого dislike. Использовать настраиваемые триггеры: повторяющийся failure cluster, high severity failure, несколько похожих feedback, явная команда владельца или eval evidence.

# 9. Skill Eval / Shadow / Promotion

Каждый Skill должен иметь eval cases: happy path, missing/ambiguous context, session reuse, explicit override, LLM unavailable, adapter unavailable, empty result, unknown entity.

Для clarification skills дополнительно: question asked, answer resumes request, no duplicate question, expired pending request, conflicting context.

Candidate skill работает в shadow: тот же normalized input, результат пользователю не показывается, external writes запрещены.

Сравнивать: task success, skill selection, context resolution, clarification necessity/count, structured correctness, evidence coverage, latency, LLM calls, capability errors.

Promotion gate: critical golden tests pass; нет deterministic metric regression; нет новых critical failures; context/clarification/task-success не хуже baseline; нет unauthorized tool use; обязательно human approval. Fail closed. Должен существовать rollback.

# 10. Curated Memory != Skill

Curated Memory хранит проверенные факты/конвенции, например alias `DM -> DataMarts`.
Skill хранит алгоритм решения класса задачи.

Диалог может породить candidate memory/skill change только по цепочке:
`traces -> repeated pattern -> candidate -> eval -> shadow -> approval -> active`.
Один пользовательский ответ никогда напрямую не переписывает active skill.

# 11. Метрики качества

Добавить:
- Task Success Rate
- First-pass Correctness
- Clarification Success Rate
- Context Resolution Accuracy
- Skill Selection Accuracy
- Skill Success Rate
- Human Correction Rate
- Grounded Answer Rate
- Deterministic Fast-path Rate
- Regression Escape Rate
- duplicate/unnecessary clarification rate
- abandonment after clarification

# 12. API/UI

Query API должен поддерживать `COMPLETED`, `NEEDS_CLARIFICATION`, `PARTIAL`, `FAILED`.

Clarification response содержит минимум status, clarification_id, question, optional options, trace_id.

В UI clarification показывается как нормальная часть диалога, не ошибка. Deterministic options можно показывать кнопками, но свободный текст всегда разрешён.

В AI-PDLC/admin UI добавить active Skills, versions, success/failures, candidates, eval score, shadow comparison, promotion status и rollback history.

# 13. План внедрения в уже готовый v2.1

## ADD-STEP 01 — Audit
Изучить текущие router/orchestrator/session memory/trace/feedback/evaluation/version registry/improvement pipeline/API/UI. Создать `docs/architecture/ADDENDUM_SKILL_CLARIFICATION_INTEGRATION.md`: requirement -> existing component -> reuse/change/new -> target files -> risk. Production behavior не менять. STOP.

## ADD-STEP 02 — Context Resolver
Models + resolver + precedence/conflict policy + tests. STOP.

## ADD-STEP 03 — Clarification Engine
NEEDS_CLARIFICATION + pending request + resume flow + Session Memory integration + golden tests. STOP.

## ADD-STEP 04 — Skill Model & Registry
Schema + loader + validation + registry + initial skill definitions из существующих capabilities. STOP.

## ADD-STEP 05 — Skill Resolver & Executor
Интегрировать `router -> context resolver -> skill resolver -> skill executor`, не дублируя capability logic. STOP.

## ADD-STEP 06 — Trace/Feedback/Eval Integration
Skill/clarification metadata, failure taxonomy, безопасная миграция storage schema. STOP.

## ADD-STEP 07 — Skill Evolution
Improvement candidate + failure cluster -> candidate; никакой auto activation. STOP.

## ADD-STEP 08 — Shadow & Regression
Candidate skill -> shadow -> comparison -> regression gate -> human approval -> version registry -> rollback. STOP.

## ADD-STEP 09 — API/UI Clarification
NEEDS_CLARIFICATION, resume flow, conversational UI, deterministic quick choices. STOP.

## ADD-STEP 10 — Skill AI-PDLC UI
Skill lifecycle в quality/admin UI. STOP.

## ADD-STEP 11 — Full Regression
Запустить старый regression suite плюс новые обязательные кейсы:
1. missing product -> clarification;
2. missing sprint -> clarification;
3. answer resumes original request;
4. session avoids duplicate question;
5. explicit current input overrides session;
6. conflict triggers clarification;
7. complete context -> no clarification;
8. safe all-products -> no clarification;
9. correct skill selected;
10. trace stores skill version;
11. feedback links to skill;
12. eligible failure cluster -> candidate;
13. no auto-promotion;
14. shadow result not served;
15. worse candidate rejected;
16. approved candidate active;
17. rollback restores previous;
18. curated memory cannot bypass approval;
19. expired pending state does not leak;
20. LLM unavailable still permits deterministic clarification/execution.

# 14. Правила GigaCode/Qwen

Перед каждым ADD-STEP вывести:
`CURRENT ADD-STEP`, `FILES TO READ`, `FILES TO CREATE`, `FILES TO MODIFY`, `FILES NOT TO TOUCH`, `EXPECTED TESTS`.

Не пересоздавать приложение. Не повторять старые steps. Если текущая архитектура отличается от предположений — адаптировать дополнение к фактическим контрактам, не создавать параллельные дубли.

После каждого шага вывести:
`ADD-STEP`, `STATUS`, `CREATED`, `MODIFIED`, `REUSED`, `TESTS`, `INTEGRATION`, `BEHAVIOR ADDED`, `REGRESSIONS`, `RISKS`, `OWNER ACTION`, `NEXT ADD-STEP`, `STOPPED: YES`.

# 15. Первая команда GigaCode

```text
Прочитай PO_AGENT_PLATFORM_V2_ADDENDUM_SKILLS_CLARIFICATION.md полностью.

Это дополнение к уже реализованному PO Agent Platform v2.1.
Не пересоздавай приложение и не повторяй старые шаги.

Выполни только ADD-STEP 01 — CURRENT IMPLEMENTATION AUDIT.
Изучи фактические router/orchestrator/session memory/trace/feedback/evaluation/version registry/improvement pipeline/API/UI.
Создай docs/architecture/ADDENDUM_SKILL_CLARIFICATION_INTEGRATION.md с картой интеграции.
Production behavior не меняй.
После аудита выдай отчёт по правилам этого ADDENDUM и остановись.
```

# 16. Definition of Done

Дополнение завершено, когда агент:
- спрашивает, а не угадывает критически недостающий context;
- продолжает исходный запрос после ответа;
- не задаёт повторно уже разрешённый вопрос;
- отдаёт приоритет явному текущему вводу над старой memory;
- использует явные versioned Skills;
- ограничивает capability/tool execution Skill allowlist;
- пишет skill/context/clarification metadata в traces;
- превращает повторяющиеся failures в candidate improvements;
- проверяет candidate skills через eval + shadow + regression;
- требует human approval;
- умеет rollback;
- не смешивает Curated Memory и Skills;
- не переписывает active Skill по одному диалогу;
- проходит старый и новый regression suite.

**Принцип:** `ask when necessary > guess`, `explicit skill > hidden mega-prompt`, `versioned evolution > silent mutation`, `eval + shadow + approval > autonomous self-promotion`.
