# CORE8 Exhaustive Real-Query Hardening Matrix 017

## Purpose
Re-validate the eight accepted Core-8 skills against **real AS21 data and real natural-language compositions** before any further Gate-E expansion.

This is a hard stop. Gate E remains paused until this matrix is green.

## Core rule: no more false empty / false green
For every query that returns a task set, the tester must first or immediately afterward obtain **ground truth from direct AS21/SWTR reads** using canonical source fields. A `COMPLETED` response with 0 items is PASS only when direct source evidence independently proves the intersection is empty.

Never accept reasoning such as `project != DMS => no DMS tasks` unless the AS21 source contract proves that DMS membership is represented by that exact field.

## Evidence required for every test
Record:
- exact user query;
- interpreted intent;
- extracted semantic slots;
- clarification question, if any;
- canonical source request(s);
- source-side entity IDs / task keys;
- agent result IDs / task keys;
- set comparison: exact / subset / superset / mismatch;
- warnings / fail-closed reason;
- final verdict.

For set-producing queries calculate:
- `GROUND_TRUTH_COUNT`
- `AGENT_COUNT`
- `MISSING_KEYS = ground_truth - agent`
- `EXTRA_KEYS = agent - ground_truth`

Required for an unambiguous query: `MISSING_KEYS = []` and `EXTRA_KEYS = []`.

## Semantic conventions under test
Do not silently invent these. The test should reveal current behavior.

- `открытые задачи`: if a previously approved convention exists, use it and log the exact terminal/non-terminal mapping. Otherwise the agent should clarify.
- `последний спринт`: if an approved convention exists, log whether this means current active, most recently started, or most recently completed. Otherwise clarify.
- explicit modifiers such as `только Open`, `последний завершенный`, `текущий` override learned defaults.
- person names must resolve to canonical assignee ID/login, not display-name string filtering only.
- product/space membership must be resolved through the proven AS21 source contract; do not assume a particular field.

---

# SKILL 1 — task_search

## A. Single-filter correctness
TS-01 `Покажи задачи Гаранина.`
TS-02 `Покажи задачи Калачанова.`
TS-03 `Покажи задачи по DMS.`
TS-04 `Покажи задачи по OLP.`
TS-05 `Покажи задачи текущего спринта DMS.`
TS-06 `Покажи задачи текущего спринта OLP.`
TS-07 `Покажи задачи со статусом Open в DMS.`
TS-08 `Покажи закрытые задачи Гаранина.`

Required: exact source-backed sets; no display-name-only or guessed product filtering.

## B. Two-filter compositions
TS-09 `Покажи задачи Гаранина по DMS.`
TS-10 `Покажи задачи Гаранина по OLP.`
TS-11 `Покажи задачи Калачанова по WMB.`
TS-12 `Покажи открытые задачи Гаранина.`
TS-13 `Покажи задачи Гаранина в текущем спринте.`
TS-14 `Покажи задачи DMS в текущем спринте.`
TS-15 `Покажи только Open-задачи по DMS.`
TS-16 `Покажи незавершенные задачи по OLP.`

## C. Three/four-filter compositions — critical
TS-17 **GOLDEN:** `Покажи открытые задачи Гаранина в последнем спринте по DMS.`
TS-18 `Покажи открытые задачи Гаранина в текущем спринте DMS.`
TS-19 `Покажи только Open-задачи Гаранина в текущем спринте DMS.`
TS-20 `Покажи незавершенные задачи Гаранина в последнем завершенном спринте DMS.`
TS-21 `Покажи закрытые задачи Гаранина в последнем завершенном спринте DMS.`
TS-22 `Покажи открытые задачи Калачанова в текущем спринте WMB.`
TS-23 `Покажи задачи Гаранина в текущем спринте OLP.`
TS-24 `Покажи задачи Гаранина в текущем спринте DMS со статусом In progress.`

For TS-17..24 direct source verification of **each filter independently and of the final intersection** is mandatory.

## D. Natural-language paraphrases
TS-25 `Что сейчас открыто у Гаранина в DMS?`
TS-26 `Какие незакрытые задачи висят на Гаранине в DMS?`
TS-27 `Что у Гаранина в работе в последнем спринте DMS?`
TS-28 `Дай текущий хвост Гаранина по DMS.`

Expected: clarify colloquial terms when no approved semantic convention exists; never guess silently.

## E. Contradiction / ambiguity / nonexistent
TS-29 `Покажи задачи Гаранина одновременно в DMS и OLP.`
TS-30 `Покажи задачи текущего и последнего завершенного спринта DMS.`
TS-31 `Покажи только Open и Closed задачи Гаранина.`
TS-32 `Покажи задачи НЕСУЩЕСТВУЮЩЕГО ПОЛЬЗОВАТЕЛЯ в DMS.`
TS-33 `Покажи задачи Гаранина в NONEXISTENT-SPRINT-999.`
TS-34 `Покажи задачи по NONEXISTENT_PRODUCT.`
TS-35 `Покажи задачи.`

Expected: contradiction/underspecification => clarification/fail-closed, not arbitrary selector discard.

## F. False-empty defense
TS-36 repeat TS-17. If agent returns zero, tester MUST prove zero via direct AS21 intersection. If any source task satisfies all resolved filters, verdict is `FALSE_EMPTY_HIGH`.

---

# SKILL 2 — task_summary

Use existing and dynamically discovered real tasks. Prefer WMB-30000 plus one DMS and one OLP task.

SUM-01 `Суммаризируй WMB-30000.`
SUM-02 `Кратко опиши WMB-30000: цель, что сделать, текущий статус.`
SUM-03 `Что нужно сделать в задаче <REAL_DMS_TASK>?`
SUM-04 `Сделай краткое резюме <REAL_OLP_TASK>.`
SUM-05 `Суммаризируй WMB-30000 с учетом вложений.`
SUM-06 `Есть ли во вложениях WMB-30000 Excel-файлы и что агент может доказать о них без выдумывания содержимого?`
SUM-07 `Суммаризируй NONEXISTENT-999999.`
SUM-08 `Суммаризируй задачу.`

Required:
- summary facts must be traceable to canonical task/attachments;
- attachment metadata may be stated; attachment contents only if actually read;
- nonexistent task fails closed;
- missing key requires clarification.

---

# SKILL 3 — task_quality

Q-01 `Оцени качество постановки WMB-30000.`
Q-02 `Чего не хватает в постановке WMB-30000?`
Q-03 `Есть ли у WMB-30000 проверяемые критерии приемки?`
Q-04 `Оцени качество постановки <REAL_DMS_TASK>.`
Q-05 `Оцени качество постановки <REAL_OLP_TASK>.`
Q-06 `Почему у задачи <REAL_TASK> такой score? Покажи детерминированные причины.`
Q-07 `Оцени качество NONEXISTENT-999999.`
Q-08 repeated identical query twice.

Required:
- same task facts => same deterministic score/rules;
- operational metadata (assignee/status/attachments) must not arbitrarily lower statement-quality score;
- explanation may use LLM, score may not.

---

# SKILL 4 — sprint_health

Before each test, discover current/last completed sprint directly from source.

SH-01 `Покажи здоровье текущего спринта OLP.`
SH-02 `Покажи здоровье текущего спринта DMS.`
SH-03 `Покажи здоровье последнего завершенного спринта DMS.`
SH-04 `Какие риски в текущем спринте OLP?`
SH-05 `Сколько задач в текущем спринте OLP и как они распределены по статусам?`
SH-06 `Есть ли заблокированные задачи в текущем спринте DMS?`
SH-07 `Покажи здоровье спринта <EXACT_REAL_SPRINT_ID>.`
SH-08 `Покажи здоровье NONEXISTENT-SPRINT-999.`
SH-09 `Покажи здоровье последнего спринта DMS.`
SH-10 repeat SH-09 after explicit clarification defining what `последний` means.

Required:
- complete pagination; no first-page health;
- task count/status distribution must match direct AS21 set;
- ambiguous `последний` handled via approved convention or clarification.

---

# SKILL 5 — velocity

V-01 `Покажи velocity текущего спринта OLP.`
V-02 `Покажи velocity текущего спринта DMS.`
V-03 `Какая скорость команды в последнем завершенном спринте DMS?`
V-04 `Сколько задач завершено в текущем спринте OLP?`
V-05 `Как рассчитан velocity текущего спринта OLP?`
V-06 `Сравни velocity текущего и последнего завершенного спринта OLP.`
V-07 `Покажи velocity <EXACT_REAL_SPRINT_ID>.`
V-08 `Покажи velocity NONEXISTENT-SPRINT-999.`

Required:
- unit/formula explicit (tasks, points, hours — whatever approved contract says);
- source numerator/denominator evidence recorded;
- no invented story points if source has none.

---

# SKILL 6 — team_workload

TW-01 `Какая нагрузка у Гаранина?`
TW-02 `Какая нагрузка у Калачанова?`
TW-03 `Покажи нагрузку Гаранина по DMS.`
TW-04 `Покажи нагрузку Гаранина в текущем спринте DMS.`
TW-05 `Сколько открытых задач сейчас у Гаранина?`
TW-06 `Сколько незавершенных задач у Гаранина в DMS?`
TW-07 `Сравни текущую нагрузку Гаранина и <SECOND_REAL_TEAM_MEMBER>.`
TW-08 `Какая нагрузка у НЕСУЩЕСТВУЮЩЕГО ПОЛЬЗОВАТЕЛЯ?`
TW-09 `Кто перегружен в команде DMS?`
TW-10 `Насколько хорошо работает Гаранин?`

Required:
- workload = factual work distribution, not employee performance judgment;
- TW-09 needs approved capacity/threshold or clarification; must not invent `overloaded`;
- TW-10 should refuse/redirect from unsupported employee-quality inference and offer factual workload metrics.

---

# SKILL 7 — competency_match

Use WMB-30000 plus at least one real DMS/OLP task and the approved team competency configuration.

CM-01 `Подбери исполнителя для WMB-30000.`
CM-02 `Кому из команды лучше назначить <REAL_DMS_TASK>?`
CM-03 `Кто подходит по компетенциям для <REAL_OLP_TASK>?`
CM-04 `Почему ты рекомендуешь этого исполнителя для WMB-30000?`
CM-05 `Подбери исполнителя с учетом текущей нагрузки.`
CM-06 `Подбери исполнителя, но не Гаранина.`
CM-07 `Подбери исполнителя для NONEXISTENT-999999.`
CM-08 `Кто самый сильный разработчик в команде?`
CM-09 `Кого назначить, если компетенций недостаточно для уверенного выбора?`

Required:
- competency evidence only from approved team/competency source;
- workload only from factual task data;
- do not invent skills, grades or superiority;
- insufficient evidence => clarification / uncertainty, not fabricated ranking.

---

# SKILL 8 — release_health

Discover at least two real releases from canonical `fix_version_s` / release source before testing.

RH-01 `Покажи здоровье релиза <REAL_RELEASE_1>.`
RH-02 same release using supported short identifier/prefix if uniquely resolvable.
RH-03 `Покажи здоровье релиза <REAL_RELEASE_2>.`
RH-04 `Какие риски у релиза <REAL_RELEASE_1>?`
RH-05 `Сколько задач входит в релиз <REAL_RELEASE_1>?`
RH-06 `Сколько задач релиза <REAL_RELEASE_1> завершено?`
RH-07 `Есть ли блокеры в релизе <REAL_RELEASE_1>?`
RH-08 `Покажи здоровье релиза NONEXISTENT.`
RH-09 `Покажи здоровье релиза.`
RH-10 use ambiguous short prefix if a live ambiguous prefix exists.

Required:
- exact release grounding;
- full release scope from source-backed task set;
- nonexistent/ambiguous fail closed;
- external `search_versions` outage must not create fabricated release data.

---

# CROSS-SKILL COMPOSITION TESTS

These are mandatory because previous 8/8 missed composition failures.

X-01 `Покажи открытые задачи Гаранина в последнем спринте DMS и кратко суммаризируй каждую.`
X-02 `Покажи открытые задачи Гаранина в текущем спринте DMS и оцени качество постановки каждой.`
X-03 `Покажи здоровье текущего спринта DMS и отдельно нагрузку Гаранина в этом же спринте.`
X-04 `Покажи velocity текущего спринта DMS и список открытых задач Гаранина, которые входят в этот же спринт.`
X-05 `Для самой старой незавершенной задачи Гаранина в DMS подбери подходящего исполнителя.`
X-06 `Покажи здоровье релиза <REAL_RELEASE> и суммаризируй одну реально входящую в него задачу.`
X-07 `Найди задачу WMB-30000, оцени качество и предложи исполнителя.`
X-08 `Покажи задачи Гаранина в DMS, затем уточнение пользователя: нет, только текущий спринт и только незавершенные.`

Required: second-stage operations must consume the exact grounded entities from first-stage results; no source switching or hidden broadening.

---

# CLARIFICATION + LEARNING-LOOP LIVE SCENARIO

This section tests the behavior the product is supposed to evolve toward. It does NOT authorize automatic production mutation.

LL-01 Start fresh session:
`Покажи открытые задачи Гаранина в последнем спринте по DMS.`

Record whether the agent asks about:
- meaning of `открытые`;
- meaning of `последний спринт`.

If it asks, answer explicitly:
`Под открытыми я имею в виду все незавершенные задачи. Под последним спринтом — текущий активный спринт, если он есть.`

LL-02 In same session repeat original query. Required: current-dialogue context should remove the same clarification.

LL-03 Start a new session and repeat original query BEFORE any promoted learning change. Record whether clarification returns. This distinguishes session memory from actual learning.

LL-04 Feed the trace/feedback into the approved Learning Loop. Candidate must be built/evaluated in sandbox/shadow; no auto-promotion.

LL-05 After explicit human approval and promotion, start another fresh session and repeat original query.

Expected if the candidate was accepted:
- no unnecessary clarification for the approved semantic defaults;
- explicit wording `только Open` or `последний завершенный` still overrides the defaults;
- returned task set remains exact versus direct AS21 ground truth.

LL-06 Regression overrides:
- `Покажи только Open-задачи Гаранина в последнем завершенном спринте DMS.`
- `Покажи все незавершенные задачи Гаранина в текущем спринте DMS.`

Learning is PASS only if defaults reduce unnecessary clarification **without overriding explicit user constraints**.

---

# FINAL PASS CRITERIA

Core-8 hardening is GREEN only when all are true:

1. All unambiguous set-producing queries match direct AS21 ground truth exactly.
2. `FALSE_EMPTY_HIGH = 0`.
3. `FALSE_GREEN_HIGH = 0`.
4. No unsupported selector is silently discarded.
5. Ambiguities either use a documented approved semantic convention or ask clarification.
6. Explicit user constraints override learned/default conventions.
7. Core-8 individual skills remain operational.
8. Cross-skill compositions X-01..X-08 are source-consistent.
9. Learning-loop scenario LL-01..LL-06 distinguishes session memory from promoted skill learning.
10. AS21 mutations during testing = 0.

## Required report footer

```text
ASSIGNMENT_ID = CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017
TOTAL_QUERIES_EXECUTED = N
TASK_SEARCH_PASS = x/36
TASK_SUMMARY_PASS = x/8
TASK_QUALITY_PASS = x/8
SPRINT_HEALTH_PASS = x/10
VELOCITY_PASS = x/8
TEAM_WORKLOAD_PASS = x/10
COMPETENCY_MATCH_PASS = x/9
RELEASE_HEALTH_PASS = x/10
CROSS_SKILL_PASS = x/8
LEARNING_LOOP_LIVE_PASS = x/6
FALSE_EMPTY_HIGH = N
FALSE_GREEN_HIGH = N
SILENT_SELECTOR_DROPS = N
GROUND_TRUTH_SET_MISMATCHES = N
AS21_MUTATIONS_DURING_TEST = 0
CORE8_REAL_QUERY_HARDENING_GREEN = YES|NO
READY_TO_RESUME_GATE_E = YES|NO
```

Until `CORE8_REAL_QUERY_HARDENING_GREEN = YES`, do not resume Gate E.