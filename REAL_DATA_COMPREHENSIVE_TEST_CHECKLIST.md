# PO Agent Platform --- Real Data Comprehensive Test Checklist

**Цель:** комплексная приемка Harness/AI-PDLC агента на **реальных
данных S21** из пространств и конфигурации, уже доступных текущему
проекту/legacy `s21-agent`.

> Основная приемка --- READ ONLY. Не создавать, не редактировать и не
> закрывать реальные задачи. Не придумывать space/project IDs, логины,
> статусы, sprint/release IDs. Fixtures использовать только для
> fault-injection и edge cases, которые нельзя безопасно воспроизвести в
> S21.

## 1. Общие правила

1.  Сначала найти фактическую конфигурацию S21 в текущем репозитории
    и/или `s21-agent`: spaces/products, adapter, team config, workflow,
    aliases, auth mode, skills/capabilities.
2.  Реальные сущности для тестов выбирать динамически через
    READ-запросы.
3.  Каждый существенный факт в результате должен иметь evidence.
4.  LLM-ответ не является доказательством PASS; факты сверяются с S21
    или deterministic calculation.
5.  Не исправлять код после первого FAIL: сначала локализовать root
    cause.
6.  После исправления повторить упавший тест и связанный regression
    subset.
7.  Skill/Prompt/Router/Knowledge/Clarification изменения проводить
    через AI-PDLC candidate → eval → shadow → regression gate → human
    approval.
8.  Deterministic code bugs исправлять обычным engineering flow +
    unit/regression tests.
9.  Не ослаблять expected result ради PASS.
10. Не выводить credentials/JSESSIONID/Authorization headers и лишние
    персональные данные в отчеты.

## 2. PRE-FLIGHT и baseline

Агент должен самостоятельно обнаружить и зафиксировать:

-   S21 adapter и transport;
-   configured spaces/products;
-   team/workflow configuration;
-   реальные project/space identifiers;
-   доступные current/recent sprints и releases;
-   активные Skill/Prompt/Router/Metrics/Knowledge versions;
-   способ аутентификации без вывода секрета.

Получить read-only baseline snapshot: число доступных задач,
распределение по статусам, доступные спринты/релизы, исполнители,
встречающиеся типы вложений, диапазон дат.

**PASS:** S21 читается, минимум одно реальное пространство найдено,
реальные задачи проходят canonical mapping.

**Если FAIL:** 401/403 → auth/config; timeout → adapter/network; empty
space → проверить фактический ID; schema mismatch → sanitized raw
sample + mapper; unknown real status → workflow config. Не менять prompt
для transport/data ошибок.

## 3. Реальные функциональные тесты

  -------------------------------------------------------------------------------------------------------------------
  ID                Проверка           Реальный сценарий          PASS
  ----------------- ------------------ -------------------------- ---------------------------------------------------
  T01               Exact task         Выбрать существующий task  key/title/status/assignee/product совпадают с S21
                                       key и попросить найти его  

  T02               Phrase search      Выбрать редкую фразу из    задача найдена, false/hallucinated tasks
                                       реальной title/description отсутствуют

  T03               Excel              Найти реальные             task + filename/type совпадают
                                       `.xls/.xlsx` attachments   

  T04               PDF                Реальные `.pdf`            task + metadata совпадают

  T05               MSG                Реальные `.msg`            task + metadata совпадают

  T06               Summary            Содержательная реальная    goal/what-to-do grounded; ничего не придумано
                                       задача                     

  T07               Task quality       Хорошая/средняя/неполная   deterministic score воспроизводим
                                       реальные задачи            

  T08               Workflow           Задачи в разных реальных   raw → normalized status корректен
                                       статусах                   

  T09               History            Задача с transitions       timeline/time-in-status/reopen/blocked
                                                                  пересчитываются

  T10               Current sprint     Реальный product           current sprint определяется из данных, не LLM

  T11               Sprint health      Current/recent sprint      completion/WIP/blocked/aging/scope/predictability
                                                                  grounded

  T12               Velocity           Реальный sprint            единица измерения явна; task count и effort не
                                                                  смешаны

  T13               Throughput         Реальный период            completed count воспроизводится

  T14               WIP                Current snapshot           учитываются только workflow-active statuses

  T15               Cycle time         Completed tasks с history  значения воспроизводятся из timestamps

  T16               Lead time          Те же/другие completed     соответствует документированной формуле
                                       tasks                      

  T17               Carryover          Завершенный sprint         baseline scope и end scope доказуемы; иначе
                                                                  limitation

  T18               Scope change       Sprint с изменением scope  формула и события воспроизводимы

  T19               Predictability     Реальный sprint            deterministic formula + intermediate values

  T20               Blocked/Aging      Current active tasks       нет completed/cancelled false positives

  T21               Team workload      Реальная команда           active/WIP/blocked/capacity корректны

  T22               Competency match   Реальная task + team       компетенции не придуманы
                                       competencies               

  T23               Release health     Реальный release           scope/done/remaining/blocked/risk/evidence
                                                                  корректны

  T24               Cross-capability   «Почему release под риском controlled plan, evidence aggregation, no recursion
                                       и кто перегружен?»         
  -------------------------------------------------------------------------------------------------------------------

Если реальных вложений нужного типа нет, статус
`NOT_APPLICABLE_REAL_DATA`, а не искусственный PASS.

## 4. Clarification / Context / Memory

  ------------------------------------------------------------------------
  ID                      Проверка                Ожидание
  ----------------------- ----------------------- ------------------------
  T25                     `Покажи velocity` при   `NEEDS_CLARIFICATION`,
                          нескольких products     реальные options

  T26                     Ответить только         продолжает исходный
                          названием product       запрос

  T27                     Follow-up               использует валидную
                          `А что со спринтом?`    Session Memory

  T28                     Явно указать другой     current input overrides
                          product                 session

  T29                     Реально конфликтующие   clarification, не silent
                          entities                choice

  T30                     Полный context          лишний вопрос не
                                                  задается

  T31                     Expired pending request не влияет на новый
                                                  запрос

  T32                     `по всем продуктам`     не спрашивает product,
                                                  если запрос безопасно
                                                  выполним
  ------------------------------------------------------------------------

## 5. Skills / Harness

Для **каждого active Skill** выполнить минимум один real-data happy
path.

Проверить: intent, skill_id/version, required context, allowed
capabilities, workflow steps, typed result, evidence, trace. Любой вызов
capability/tool вне Skill allowlist = **P0**.

Обязательно проверить skills: task_search, task_summary, task_quality,
sprint_health, velocity, team_workload, competency_match,
release_health, help --- либо их фактические эквиваленты из Registry.

## 6. Trace / History / Feedback / AI PDLC

  ------------------------------------------------------------------------------------------------------------------------
  ID                      Проверка                PASS
  ----------------------- ----------------------- ------------------------------------------------------------------------
  T33                     Trace completeness      intent/entities/context/skill/plan/tools/LLM/evidence/latency/versions

  T34                     Operational History     executions ищутся по trace/session/intent/time

  T35                     Feedback                feedback связан с trace + skill/version

  T36                     Eval case               feedback может породить candidate eval, но не active knowledge

  T37                     Failure Miner           классифицирует/группирует failures без изменения runtime

  T38                     Skill candidate         base/proposed version + evidence + rationale + risk

  T39                     Shadow                  candidate результат не показывается пользователю

  T40                     Regression gate         заведомо худший candidate отклоняется

  T41                     Human approval          без approval candidate не active

  T42                     Rollback                безопасная test version возвращается на previous active
  ------------------------------------------------------------------------------------------------------------------------

## 7. Fault injection

**T43 LLM unavailable:** отключить test LLM provider. Search, metrics,
clarification и deterministic formatter должны продолжать работать;
warning обязателен.

**T44 AS21 unavailable:** использовать test adapter/config fault
injection, не устраивать реальный outage. Ожидается controlled
AdapterUnavailable/timeout, trace и отсутствие fabricated fallback data.

**T45 Malformed LLM JSON:** fake LLM возвращает invalid structure →
schema validation + safe fallback.

**T46 Unknown intent:** help/clarification/unsupported; никакого
случайного tool execution.

**T47 Pagination:** выбрать real query/space с \>1 API page → полный
набор без duplicates.

**T48 Cache freshness:** если cache существует, проверить freshness
metadata; stale данные нельзя выдавать как «сейчас».

**T49 Multi-space isolation:** одинаковый тип запроса по каждому
configured space; данные/contexts не смешиваются.

**T50 Security/read-only:** logs/traces не содержат
token/JSESSIONID/Auth headers; во время приемки нет write calls.

## 8. Grounding sampling

Случайно выбрать минимум 10 успешных real-data ответов. Каждый
существенный факт сопоставить с S21 raw data, deterministic metric или
approved config/knowledge. Рассчитать Grounded Answer Rate.

## 9. End-to-End PO сценарии

Выполнить на реальных данных:

1.  **Утро PO:** `Что требует моего внимания сегодня?`
2.  **Sprint review:**
    `Как идет текущий спринт и что рискует не завершиться?`
3.  **Release review:** `Что мешает выпуску текущего релиза?`
4.  **Team review:** `Как распределена нагрузка и где bottleneck?`
5.  **Task investigation:** найти реальную задачу по критерию,
    суммаризировать и оценить качество постановки.

Проверять decomposition, реальные tool calls, evidence и отсутствие
invented conclusions.

## 10. FAIL TRIAGE --- обязательный порядок диагностики

При любом FAIL искать первое место возникновения ошибки **снизу вверх**:

``` text
1 SOURCE DATA
2 AUTH / TRANSPORT
3 RAW S21 RESPONSE
4 MAPPER / CANONICAL MODEL
5 WORKFLOW / STATIC CONFIG
6 DETERMINISTIC METRIC
7 CONTEXT RESOLVER
8 ROUTER / ENTITY EXTRACTION
9 SKILL RESOLVER
10 SKILL EXECUTOR / PLANNER
11 KNOWLEDGE / CURATED MEMORY
12 LLM PROMPT / SYNTHESIS
13 API / UI
```

Исправлять самый нижний слой, где впервые появляется расхождение.

### Failure → действие

  -----------------------------------------------------------------------
  Failure                 Сначала проверить       Не делать
  ----------------------- ----------------------- -----------------------
  S21 data differs        raw API/mapper          менять prompt

  Task missing            search scope/pagination добавлять task в
                                                  knowledge

  Wrong status            mapper/workflow         просить LLM угадать

  Wrong metric            inputs/formula/filter   менять explanation

  Wrong product/entity    context resolver        hardcode phrase

  Wrong Skill             router/Skill            расширять mega-prompt
                          mapping/eval            

  Hallucinated fact       supplied                сохранять hallucination
                          evidence/prompt         в memory

  Unnecessary question    clarification/session   отключать clarification
                                                  globally

  Missing question        required_context policy позволять capability
                                                  угадывать

  Invalid LLM JSON        schema/retry/fallback   silently parse
                                                  arbitrary text

  Stale result            cache/freshness         скрывать timestamp

  Candidate regression    reject candidate        снижать gate без
                                                  причины

  Secret in trace         redaction/logging       просто удалить отчет
  -----------------------------------------------------------------------

## 11. Severity

**P0 / CRITICAL:** invented real task/person/metric; unauthorized write;
secret leakage; wrong deterministic metric как факт; cross-space
leakage; auto-promotion; shadow served as production; corrupted
version/history state.

**P1:** wrong intent/Skill/context; broken clarification; missing
pagination; major missing evidence; incorrect sprint/release analysis.

**P2:** wording/formatting; minor latency; корректный, но неоптимальный
clarification.

Любой P0 блокирует приемку.

## 12. Рекомендуемые acceptance thresholds

``` text
P0 failures                         = 0
Core deterministic tests           = 100%
Real task identity accuracy         = 100%
Metric reproducibility              = 100%
Unauthorized writes                 = 0
Secret leakage                      = 0
Skill allowlist violations          = 0
Clarification resume tests          = 100%
Regression-gate safety tests        = 100%
Grounded Answer Rate                >= 98%
Routing Accuracy                    >= 95%
Skill Selection Accuracy            >= 95%
Context Resolution Accuracy         >= 95%
```

Для маленькой выборки показывать numerator/denominator вместе с
процентом.

## 13. Итоговый отчет

Создать `reports/REAL_DATA_ACCEPTANCE_<timestamp>.md`:

``` text
Environment / active versions
Spaces/products tested
Baseline snapshot

TOTAL / PASS / FAIL / BLOCKED / NOT_APPLICABLE
P0 / P1 / P2

Для каждого теста:
ID
Status
Real entities used
Expected
Actual
Evidence
Trace ID
Failure category
Root cause
Recommended fix
Retest result

AI-PDLC candidates created
Regression status

FINAL:
ACCEPT | ACCEPT WITH CONDITIONS | REJECT
```

Не сохранять secrets.

## 14. Команда для GigaCode

``` text
Прочитай REAL_DATA_COMPREHENSIVE_TEST_CHECKLIST.md полностью.

Проведи комплексное тестирование текущего PO Agent Platform на РЕАЛЬНЫХ данных S21. Пространства, продукты, team/workflow configuration и способ доступа найди самостоятельно в текущем репозитории и доступном legacy s21-agent. Ничего не придумывай.

Основная приемка READ ONLY. Не создавай и не изменяй реальные задачи S21.

Сначала выполни PRE-FLIGHT и baseline snapshot. Подтверди, что читаются реальные задачи из фактически настроенных spaces.

Далее выполняй checklist последовательно. При FAIL:
1) не маскируй ошибку;
2) классифицируй severity/failure category;
3) локализуй root cause по FAIL TRIAGE;
4) предложи минимальное исправление;
5) Skill/Prompt/Router/Knowledge/Clarification changes проводи через AI-PDLC candidate flow;
6) deterministic code bugs исправляй через code + tests;
7) повтори упавший тест и связанный regression subset;
8) не ослабляй expected result ради PASS.

После тестирования создай итоговый REAL_DATA_ACCEPTANCE report.
```

## 15. Definition of Done

Приемка завершена только когда реальные S21 spaces использованы, core
capabilities и все active Skills проверены, metrics независимо
воспроизведены, clarification/session memory/history/trace/feedback
проверены, AI-PDLC candidate/shadow/gate/approval/rollback проверены,
fault injection и multi-space isolation пройдены, P0=0, а каждый FAIL
имеет root cause и retest result.
