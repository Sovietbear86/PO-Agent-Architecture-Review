# One-time priority smoke: A230R3.32-SPRINT-UI-FORECAST-REFRESH-SMOKE

This is a **short, single deployment/source check**, NOT another testing marathon. Independently QA-only; do not edit, commit, restart/stop existing services, read/write AS21 outside bounded scopes. Fetch latest Review HEAD first; preserve dirty state. Recent owner updates: Sprint UI Predictability card and its redundant V4 query removed; refresh failure reason displayed; 105-second bounded forecast source HTTP budget to match 90-second history collector; typed error distinguishing a missing task-api forecast route. Frozen Agent Core 6/6.

1. Record `TESTED_HEAD`, actual executable source checkout/commit of existing agent (8004), task-api (8241), Vite (5175), MCP (3000). **Do not assume running processes have auto-reloaded**; inspect process cwd/launch source and current GET API. Never restart user servers without user consent; if stale, report `DEPLOYMENT_STALE`, how owner safely restarts, and STOP smoke.
2. Read-only GET `/api/v1/sprints/DMS-SPRNT-5/delivery-forecast` agent -> corresponding Task API GET `/api/v1/swtr-read/sprints/DMS-SPRNT-5/delivery-forecast`. Compare HTTP code and safe typed reason. Do not reveal actor/task history. Old finished sprint can legitimately return `closure_out_of_scope`; `forecast_route_not_deployed` means stale Task API, not deficient AS21.
3. Browser tab «Спринты» on current source: **no Predictability card and NO predictability query in Network**, card Delivery Forecast localized error, one Refresh produces correct update status and reason. For active DMS-SPRNT-6, if 3+ proven in-window closures, bounded REAL AS21 A/B forecast; otherwise `SOURCE_CONDITIONAL`, never fake a number.
4. Only targeted frontend compile, relevant fast tests, Core hash check. Diagnose cause of the refresh failure from which named query failed (health/velocity/throughput/wip/risks); do not claim bug fixed simply because query was removed. Report `SPRINT_UI_SMOKE_GREEN`, `SPRINT_UI_DEPLOYMENT_STALE`, `SPRINT_UI_SOURCE_CONDITIONAL` or `SPRINT_UI_SMOKE_RED` with first failing source and STOP. One untracked concise report `po-agent-platform-v2/qa_reports/SPRINT_UI_REFRESH_FORECAST_SMOKE.md`, no commits.

### Additional priority gate: QUALITY dashboard incident (same smoke, not another QA cycle)
User's screenshot on `Качество` for `STS-612240` shows `Не удалось обновить (ошибка)` with old snapshot timestamp, while quality=100/100, acceptance=45/100 (4 testable), missing=0 and decision=REWORK. These values can **legitimately disagree** because task-quality and acceptance-testability are separate evaluations; the screenshot **does not prove a source-quality calculation error**. Owner updated `QualityDashboard.tsx`: show refresh error reason, make labels explicit, explain 100 vs 45 mismatch. QA needs to determine why refresh fails and whether the three underlying capabilities use current source.
- On the same existing read-only QA stack/browser, inspect **the actual three `/api/v1/query` calls** `Оцени постановку STS-612240`, `Чего не хватает в задаче STS-612240`, `Покажи критерии приемки STS-612240`. With bounded single-task AS21 read and no writes, report each `status`, `skill.id`, `evidence_count`, `warnings`, `latency_ms`, whether snapshot was freshly replaced, and sanitized network error/HTTP status. No broad scans.
- Compare the real source task content + acceptance criteria to independent B oracle as feasible. Check whether the **same task and same as_of** drive all 3 metrics, whether criteria marked `TESTABLE` are indeed testable, and whether `0 missing requirements` contradicts `45 acceptance` or indicates separate thresholds. Specifically guard against misleading 100/100 on security/CVE task if acceptance contains vague/non-testable conditions. Do not quietly change scoring algorithms as QA.
- Verify browser Refresh reason is now typed (rather than just «ошибка»), keeps last valid cached snapshot visibly timestamped, and does not leak JSON/PII. Validate `TaskDetail` tabs «Резюме/Качество» for this same task, report any acceptance-count inconsistency (P3.3/P3.4).
- If one query is FAILED/NEEDS_CLARIFICATION or 120s timeout, show first failing boundary (frontend→V4→skill→AS21/LLM). If source access not available, verdict `QUALITY_SOURCE_CONDITIONAL` not a fabricated GREEN. Leave `po-agent-platform-v2/qa_reports/QUALITY_REFRESH_SINGLE_TASK_DIAGNOSTIC.md` untracked, no code changes, no commits; one report and STOP. Frontend compile + Core 6/6 required.

After delivering this smoke report **do not automatically start sbeproject discovery**; wait for PO to approve continuing. The saved P3.2 instructions below remain current for the subsequent step.

---

# GigaCode — CURRENT NEXT ACTION

## A230R3.31-P32-SBEPROJECT-RELEASES-SOURCE-CONTRACT-DISCOVERY

### Контекст и цель
P3.5 «Обзор» — `P35_OVERVIEW_GREEN` на `fa3c154`: все 5 реально настроенных пространств проверены независимой сверкой AS21 и браузером, скрытого OLP-only фильтра нет. **Переходим к P3.2 «Релизы»** — крупнейшему запланированному развитию. Система **sbeproject** является мастер-системой релизов, синхронизированной с AS21; у GigaCode уже имеется локальный skill доступа к ней. Сейчас нужен **ОДИН короткий discovery реального интерфейса и схемы источника**, чтобы владелец сразу реализовал целиком адаптер, безопасный API и вкладку «Релизы». Не запускай циклы тестов отдельных файлов.

### Роль и ограничения
Ты — независимый исследователь источника/QA. **Никаких правок исходников, тестов, конфигураций, rules, Agent Core V4, GIGACODE.md или Public; никаких коммитов, push, PR, слияний.** Только авторизованные read-only операции. Не отправляй данные в sbeproject/AS21, не меняй релизы, задачи, права, credentials. Не осуществляй tenant-wide сканирование; сначала смотри существующий локальный скилл/документацию. Не выводи и не копируй токены, PII, полные payload, внутренние URL с секретами. Не останавливай сервисы пользователя, сохрани dirty/untracked файлы. Синхронизируй Review HEAD с origin и зафиксируй TESTED_HEAD, Core V4 = 6/6 vs `6fb335d`.

### 1. Обнаружение подключения sbeproject (не изобретать API)
- Найди **реально существующий** локальный GigaCode skill для sbeproject: путь, SKILL.md, MCP/CLI/HTTP endpoint contracts, права подключения, read-only инструменты, auth/bootstrap (без вывода секретов), ограничения и статус подключения. Если скилл недоступен или доступ требует ручной авторизации — честно `SOURCE_BLOCKED`, не придумывай методы/URL.
- Определи, что в sbeproject является release: канонический ID, display name, связанное пространство/продукт, версии, даты (план/факт), статусы/жизненный цикл, этапы/вехи, ответственные, зависимости, ссылки на AS21. Зафиксируй **реальные имена полей, типы, пустые значения и provenance**. Не подменяй sbeproject обычной выборкой AS21.

### 2. Минимальная ограниченная A/B-сверка
- Если авторизовано, выбери **2–3 конкретных разрешённых релиза**, желательно из DMS и OLP, с лимитом <=20 релизов/страницу и <=100 связанных задач/релиз при наличии этих возможностей; если пагинация/полнота не доказаны, помечай INCOMPLETE.
- A: bounded read-only sbeproject релиз → идентификатор, даты, статус и ссылки на задачи.
- B: независимая bounded read-only AS21 проверка небольшой выборки **канонических task keys** релиза (до 10 на релиз) и статусов; не скачивай все задачи пространства.
- Покажи правила согласования: уникальный идентификатор; различие «релиз в sbeproject» / «задача AS21» / «версия»; 1:N и N:N membership; дубли, переносы, архивные релизы; несовпадения источников, задержка синхронизации; источник истины по каждому полю. Нужны реальные примеры без PII.
- Если доступен только AS21 или только sbeproject, **не объявляй интеграцию доказанной**.

### 3. Аудит текущей вкладки «Релизы»
- Проследи реальный frontend route «Релизы» (не legacy/dead component) → API → skill → adapter → AS21 / sbeproject; найди, какие поля сейчас заполняются, какие являются заглушками, какие данные считаются локально. Зафиксируй конкретные пути/строки и UI-контракты, избегай стороннего рефакторинга.
- Предложи **один реализуемый MVP вертикального среза**: safe bounded sbeproject read-only adapter → GET API → Release view + статус связи с AS21, loading/error/unknown/stale. Исторические релизы без задач/дат не должны становиться «0% готовности». Укажи готовые компоненты, которые можно переиспользовать, и список реально недостающих полей. Никаких fake metrics или tenant-wide reads.
- Корректное поведение при недоступности sbeproject: typed SOURCE_UNAVAILABLE, не переключаться на AS21 незаметно.

### Отчёт и STOP
Единственный артефакт (untracked, без коммита): `po-agent-platform-v2/qa_reports/P32_SBEPROJECT_SOURCE_DISCOVERY.md`:
1. TESTED_HEAD, путь существующего skill, доступность, точные read-only contracts.
2. Таблица `поле релиза | источник истины | тип/пример без PII | полнота | AS21 mapping`.
3. До 3 ограниченных A/B примеров + фактические лимиты/тайминги/ошибки.
4. Текущий UI data-flow, узкие места и **конкретный owner implementation plan из одной законченной вертикали**.
5. Вердикт `P32_DISCOVERY_READY` (подтверждённый контракт) / `P32_SOURCE_BLOCKED` (нет доступа) / `P32_CONTRACT_INCOMPLETE` (существенные поля не доказаны).

**После отчёта остановись. Не начинай самостоятельно разработку или полный регресс. Владелец продукта реализует следующую цельным изменением; затем один финальный независимый E2E.**
