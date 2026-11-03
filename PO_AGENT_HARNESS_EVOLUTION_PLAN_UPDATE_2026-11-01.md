# PO Agent Harness — актуализация плана эволюции (01.11.2026)

**Статус:** утверждённые продуктовые приоритеты / работа по этапам, не автоматическое разрешение релиза.  
**Основной план:** `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`. Этот документ дополняет, но не отменяет архитектурные ограничения и исторические QA-гейты.  
**Репозитории:** Review `feat/core8-real-query-hardening-v2`; Public `main` + Draft PR #3 (deploy/health) + Draft PR #4 (A230R3 community migration).  
**Правило:** шесть замороженных файлов Agent Core V4 не изменять; новые навыки — через plugin/capability, ограниченные read-only источники, Task API/Frontend. GigaCode — независимый QA, не разработчик. После изменения кода полный регресс A (Agent) / B (прямой авторизованный source oracle) / C (браузер). Никаких фиктивных метрик, скрытого fallback, широких сканирований и несанкционированных записей в AS21/sbeproject.

## Приоритеты и порядок

| Этап | Приоритет | Статус на 01.11.2026 | Критерий выхода |
|---|---|---|---|
| P0. Стабильность рабочего Review | Критический | Диагностика выполнена, frontend fail-closed патч A230R3.10 ожидает независимый QA | Надёжные запросы и обновление Overview; честные ошибки и свежесть; A/B/C + полный регресс GREEN |
| P1. Перенос в Public | Высокий | PR #3/#4 Draft; A230R3.9-R2 PUBLIC_RELEASE_GREEN в проверенной конфигурации, но ещё не объединены | Безопасная поэтапная публикация, CI/security/build GREEN, без секретов и без Core drift |
| P2. Public Deploy / Health Skills / инструкции | Высокий | H0–H6, холодный/тёплый запуск и браузер проверены на изолированном macOS-окружении; Windows пользовательский сценарий не сертифицирован | Fresh-clone Windows и macOS, понятные инструкции и воспроизводимый health; без доступа к внутренним конфигам |
| P3.1. Predictability спринтов | Средне-высокий | Н/Д корректно для исторической committed-baseline метрики, новая модель не разработана | В UI есть прозрачная вычисляемая оценка и/или честное «недостаточно данных»; без подмены исторического показателя |
| P3.2. «Релизы» + sbeproject | Высокий, крупный эпик | Discovery / интеграционная спецификация отсутствует | REAL sbeproject ↔ AS21, точные membership/status/dates/dependencies, A/B/C и права доступа |
| P3.3. «Резюме» vs «Качество» | Высокий UX/семантика | Наблюдается противоречие на STS-612240 | Оба экрана согласованы по каноническому полю и доказательствам, без ложных утверждений |
| P3.4. Аудит «Качества» | Высокий | 100/100 за формальную полноту не доказывает пригодность acceptance criteria | Корректная рубрика качества и честные срезы; независимая ручная оценка кейсов |

Порядок исполнения: **P0 → P1 → P2**, параллельно допускается только дизайн/discovery P3.1–P3.4. Внедрение P3.x после стабилизации или в изолированной ветке со своим регрессом. Не смешивать исправление UX и замену бизнес-метрики в одном коммите.

## P0. Стабилизация рабочего приложения Review

**Наблюдения:** запрос исполнителя+пространства+даты `STS с 20.10.2026` ранее `FAILED` за ~80 с без evidence; поздний независимый запуск того же класса запроса вернул 46/46 EXACT. Planner LLM мог исчерпать ограниченные repair steps во время деградации эндпоинта; старый trace недоступен, поэтому 429 как причина исходного события **не доказан**. У «Обзора» три snapshot-запроса, глобальная параллельность 2, клиентский лимит 120 с; предыдущий 18/36=50% был своевременно помеченным кешем, а свежий срез на тот момент 18/35=51.4%. Predictability Н/Д отражал отсутствие baseline. Source AS21 в независимой диагностике был доступен.

**Работы:**
1. Закончить A230R3.10 QA frontend-only fail-closed: `FAILED/PARTIAL/NEEDS_CLARIFICATION` не перезаписывают последний успешный снимок; таймаут/429/сеть/источник/отказ агента отображаются понятными, неперсональными причинами; после восстановления кеш обновляется. Проследить, чтобы отображение старого снимка было явным.
2. Разделить SLI: LLM planning errors/429/latency, AS21/MCP source-health, Task API 401/403/429/5xx, очередь, UI Promise.race timeout, cache freshness; измерять per-stage latency + correlation_id/trace_id без секретов. Реальный отказ не превращать в «0 задач».
3. Проверить очереди и budget: три запроса Overview, шесть Sprint — отсутствие зависания и массовых вызовов при рефреше; безопасный backoff/jitter лишь для подтверждённых временных ошибок, без бесконтрольных повторов. По возможности общий ограниченный budget/отмена запросов; менять только вне Core, если доказано.
4. Доработать грамматику периода создания задач (`2 недели`, `за вчера`, относительный/открытый период) через универсальный typed date-range parser + контракт извлечения аргументов; **без хардкода конкретных фраз**. Для типов периодов различать created_at, worklog date и sprint calendar.
5. Ведение лога регрессий: сценарии с реальными именами/пространствами только в приватном QA, публичные тесты — синтетические. Контроль предсказуемости UI/источников, изоляция сеансов и запрет leaking raw JSON.

**DoD:** фронтенд build + сценарии кеша/ошибок + V4 full + Task API + реальные A/B ограниченные запросы + Playwright UI; Core 6/6; отсутствие нового source/tenant scan. В случае нехватки логов «root cause unverified», не выдавать гипотезу за доказанную причину.

## P1. Перенос изменений Review → Public

1. Сохранить результаты независимого A230R3.9-R2 `PUBLIC_RELEASE_GREEN` для **конкретного** HEAD Public PR #4 `f27fea7`: H0–H6 (холодный/тёплый), 49 MCP, CI 6/6, независимый bounded REAL AS21 A/B, Chromium DOM, Core 6/6. Это не означает промышленной сертификации многопользовательского deployment.
2. Проверить PR #3 (public-deploy/public-health-check) и PR #4 как stacked PR. Предлагаемый порядок: QA #3 → merge #3 в main → перенастроить base #4 на main → перепроверить diff/CI/security → merge #4. **Только с явным решением владельца**, без автоматического merge.
3. Публиковать только очищенные изменения; не перетаскивать внутренние Git history, credentials, .env, реальные имена/logins, внутренние AS21 dumps и корпоративные hosts. Не заменять Public `products.yaml` и public Core приватными версиями.
4. После A230R3.10 и других исправлений Review выполнять отдельный файл-за-файлом sanitized delta → отдельный PR и независимый A/B/C регресс. Изменения, ещё не протестированные, не примешивать к ранее прошедшему HEAD.
5. Блокеры многопользовательского использования: principal-bound session/clarification auth/ownership; запрещать remote/multi-user развёртывание флагов continuation до разрешения security gate. Публикация кода с flags OFF ≠ разрешение публичного многопользовательского сервиса.

**DoD:** public fresh clone, security scan, CI 6/6, health H0–H6, 49 MCP, UI/browser and source oracle. Core frozen. Документированные известные ограничения и откат.

## P2. Skills развертывания и Health Check + инструкции коллегам (Windows / macOS)

**Два продукта:** `.gigacode/skills/public-deploy/SKILL.md` и `.gigacode/skills/public-health-check/SKILL.md` + `DEPLOYMENT.md`, `scripts/public_health_check.py`. Цель — коллега получает рабочий автономный Public без GitVerse/Review и без скрытых зависимостей.

**Проверка Skills:**
- Чистый clone; Python/venv, Node/npm, MCP server as own process, Task API, Agent, Vite; зависимости из lock/requirements; safe placeholders.
- Windows: PowerShell 7 и Windows 11, пути/пробелы, создание `.venv` и активация, `py -3`/python, разрешения execution policy (без небезопасных глобальных ослаблений), переменные среды, процессы/порты, UTF-8, установленный Python 3.13 для stdio MCP. Не предполагать поддержку Windows до реального теста.
- macOS: zsh, Python 3.13 MCP, venv/Homebrew при необходимости, Node/npm, chmod, возможные Apple Silicon/Intel отличия, проброс env в дочерние процессы.
- Оба: настройка конфигурации продуктов/пространств и команды **без секретов в репозитории**; ephemeral local secrets, не распечатывать значения, сетевые предпосылки/VPN объяснить.
- Health H0–H6: где ожидается 49 tools, cold start source/outer budget (15s/20s, мониторинг запаса), fail-closed источник, schema/authorization, health errors; H4 HTML smoke **не равен** E2E DOM; отдельный браузерный тест, независимое происхождение данных.
- Коллизии портов и `Vite /api` → **собственный** Agent, конфигурируемые loopback ports, корректная остановка только своих процессов; диагностика 429/AS21/MCP и safe rollback.
- Валидация user journey: инженер без поддержки автора следует инструкции и запускает stack; затем 1–2 bounded теста, health GREEN, сравнение с источником, скрин браузера без PII; отдельные таблички macOS/Windows commands, Troubleshooting FAQ.

**Deliverables:** переработанный `DEPLOYMENT.md` (платформенные подразделы), `WINDOWS_SETUP.md` и `MACOS_SETUP.md` при необходимости; обновлённые Skills, quick-start + prerequisites + upgrade/rollback + known limitations; автоматические smoke-проверки для обеих платформ. Сначала документировать, затем independently validate — не объявлять Win GREEN по Mac.

## P3.1. Sprint predictability: от вечного «н/д» к полезной прогнозной модели

**Контракт:** исторический predictability = `completed_committed_at_start / committed_at_start` (или иная документированная baseline-based формула) **НЕ ВЫЧИСЛЯТЬ без baseline**. В AS21 нет гарантированного committed snapshot на начало спринта. Нельзя приписывать новой прогнозной эвристике историческое «predictability».

**Предложение:** оставить `Committed Predictability: Н/Д (нет baseline)` и рядом добавить самостоятельную метрику **«Прогноз завершения спринта / Delivery Forecast»**, с методологией и доверительным статусом.
- Сигналы: elapsed working days / remaining days по фактическим датам спринта; текущий committed/live scope; done count & closure timestamps; throughput завершённых задач в сопоставимых последних N спринтах и в текущем; WIP (НЕ «whip») и aging/WIP/blocked; scope churn (новые/удалённые задачи); для прогнозирования исторические сроки закрытия — по авторитетным timestamp, не по сегодняшнему snapshot.
- Формула MVP без магических весов: `remaining = open_in_scope`, `throughput_rate = closed_tasks / elapsed_workdays` (или weighted recent historical rate с прозрачными периодами), `ETA_days = remaining / rate` при `rate>0`; `forecast_completion_by_end = min(1, predicted_closed_by_deadline / current_scope)` как **оценка**, а не обещание. Если нет достоверных дат/истории или rate=0 → `insufficient_evidence` (не 0% и не 100%). Показать сценарии optimistic/base/conservative через явно указанные диапазоны исторической скорости, без искусственных confidence %.
- Для DMS-SPRNT-5: собрать source-backed start/end, ежедневную историю scope/status/closed_at, сколько задач было на старте и стало сейчас, throughput предыдущих 3–5 сравнимых спринтов, WIP и возраст; проверить допустимость ретроспективного восстановления из event history AS21. Ранее были разные snapshots (36→35 задач), использовать **датированные** срезы, а не фиксировать 35/36 как норматив.
- Показать `rate`, `remaining`, `forecast_date`, риск неуспеть и `computed_at`, provenance; отделять наблюдаемое от оценочного. Сравнить прогноз с фактическим завершением N прошлых спринтов (backtest), калибровать ошибку и устойчивость к scope churn.
- Навык/plugin `sprint.delivery_forecast` и отдельный UI card, не переписывать существующий `sprint.predictability` без решения о переименовании; без Core.

**DoD:** подтверждённые source timestamps, прозрачно воспроизводимые расчёты, backtest, no-baseline остаётся честным Н/Д, никаких fake data. Результат A/B/C GREEN.

## P3.2. «Релизы» — новый крупный эпик интеграции с sbeproject

**Discovery сначала:** GigaCode по утверждению владельца имеет Skill доступа к **sbeproject** (мастер-система релизов, синхронизируется с AS21). Наличие и работоспособность самого Skills/API, разрешённые scopes, schema, rate limits и правила синхронизации **сначала проверить**, не утверждать, что текущий агент уже к нему подключён. Не строить предположительные эндпоинты.

**Source of Truth:**
- `sbeproject`: релизная идентичность, версия, план/факт дат, стадии/статусы, релизные вехи, зависимости и релизная принадлежность, если подтверждены контрактом.
- `AS21`: точные задачи релиза, статусы, исполнители, типы, блокеры, связи, история изменений, трудозатраты — с реальными authorizations.
- Идентификация releases-to-AS21 join: stable release id ↔ AS21 release/task keys, единая схема и конфликтные ситуации; асинхронная синхронизация может давать lag, поэтому показывать `source_updated_at`, `sync_lag`, `incomplete`, `conflict`, не скрывать расхождения.

**Подэтапы:**
- R0: inventory sbeproject skill/API, auth/read-only, проверка схемы с реальным **ограниченным** релизом PV DataMarts или PV OLAP Analytics; A/B delta matching, безопасность, acceptance schema.
- R1: source adapters / Task API read facade `release.list`, `release.detail`, `release.tasks` с bounds и typed provenance, фильтры по продукту/дате/статусу.
- R2: UI «Релизы»: таблица релизов, план/факт, progress, coverage, dependencies/blockers, фильтрация, drill-down к задачам AS21; статусы источника, дата обновления, пусто vs недоступно.
- R3: аналитика release scope changes, burn-up, throughput/lead time, commitment vs done, release readiness/quality gates и прогноз даты только если хватит реальной истории.
- R4: А/В/С full e2e, ownership, RBAC, long-sync divergence, cancellation/timeouts, negative tests, scaling/limited pagination.

**Особое требование:** изменения в sbeproject/AS21 не разрешены — только bounded read. Dedupe задач по canonical key, reconciliation логировать без PII. Release plan — не QA-факт до independent oracle проверки.

## P3.3. «Резюме» против «Качество»: согласованность criteria

**Наблюдение по STS-612240 на скриншотах:** «Резюме» сообщает, что нет критериев приёмки, тогда как «Качество» ставит 100/100 и отмечает критерии. Требуется проверить, какие **поля и слои** каждый экран использует: structured acceptance criteria в карточке AS21; текст описания и goal; внешние комментарии/документы; inferred acceptance markers. «100/100 формальное качество постановки» не равно «структурированные критерии подтверждены».

**Задачи:**
1. Получить одинаковый исходный task payload в один момент; сравнить `source_data`, `description`, `goal`, dedicated acceptance criteria field, нормализацию и результаты обеих вкладок с trace IDs.
2. Единый typed `acceptance_evidence` (status: explicit_structured / explicit_text / inferred / missing / source_unavailable; evidence field/path + origin + timestamp). Не переписывать source record. Вывести в обе вкладки одинаковую формулировку для одинакового статуса.
3. Если критерии присутствуют только как текстовое условие (например, «если False Positive… закрыть по инструкции») — назвать «проверяемые условия в описании», но не приравнивать к формально заведённым acceptance criteria. Список open questions ≠ автоматически критерии приёмки.
4. Уточнить правила rubric: качество формулировки vs полнота structured карточки vs техническая корректность решения разделены. Один 100/100 не может доказывать наличие всех evidence без source field.
5. Позитивные/негативные тесты на STS-612240 (приватный oracle), synthetic equivalents Public, с/без структурированных критериев, с текстовыми критериями и без них, источник unavailable, cross-screen browser A/B/C.

**DoD:** обе вкладки не противоречат друг другу; каждый вывод объясним evidence; нет «100%» по отсутствующему полю по одному случайному keyword; no raw JSON в UI.

## P3.4. Аудит алгоритма качества задач

Отдельно проверить, насколько правильно `task.quality` и вкладка «Качество» оценивают **постановку**, а не подтверждение выполнения технических требований. На кейсе STS-612240 уязвимость `follow-redirects` и сложная цепочка воспроизведения/False Positive требуют проверки того, что алгоритм не подменяет техническую оценку эвристической полнотой текста.

**План проверки:**
1. Inventory `analysis/task_quality.py`, `task.quality`, UI `QualityPage`, схемы `rules/penalty/evidence`. Отследить исходные поля, дублирование синтетических итогов и прежнюю проблему служебного `JSON.stringify(result.data)` в «Качестве».
2. Два независимых измерения: **Statement Completeness** (название/цель/условия/проверяемость/зависимости) и **Acceptance Testability** (конкретные входы, ожидаемый результат, окружение, шаги воспроизведения, измеримые граничные условия). Полевой quality score (если сохраняем 0–100) не должен выдаваться за «реальная уязвимость подтверждена».
3. Спроектировать явные критерии по task type: bug/defect, security/CVE, story/feature, tech debt; необязательные поля не штрафовать без связи с типом. Содержательные валидации через факты, LLM объясняет, но не без доказательств изменяет deterministic score.
4. Собрать независимую размеченную выборку реальных задач (с согласованным read-only доступом), плюс синтетическую Public: заведомо хорошие/плохие/спорные, отсутствуют критерии, ложноположительные security cases, длинное описание без проверяемого результата, разные локали.
5. Сравнить оценку агента с двумя независимыми экспертными разметками (inter-rater agreement; false pass 100/100; false missing-criteria); QA не подгонять правила под один STS task. Выводить explainable feedback и ссылки на конкретные поля/evidence.
6. Нормализовать UI «Качество»: компактный список rules/score с раскрываемым evidence, без raw service JSON, без внутренних planner payload. Документировать методологию для коллег.

**DoD:** обоснованные правила, подтверждение на representative corpus, нет противоречий с «Резюме», нет ложной абсолютной уверенности (100/100) на недостаточных данных, повторяемый автоматический регресс.

## Управление работой и release gates

- По одному активному owner assignment; `GIGACODE_NEXT_ACTION.md` всегда указывает актуальный **QA-only** gate на конкретном HEAD. GigaCode не исправляет production и не ставит «все GREEN» по чужому прогону.
- Сначала product discovery/ADR → smallest outside-Core patch → независимые unit + AS21 oracle B + browser C → full V4 & Task API regression → security → PUBLIC selective sanitized delta.
- DoD каждой доработки: what changed, source origin, exact test head, no Core 6/6 drift, performance budget, clean error/fail-closed, provenance, no user-facing internal JSON, no fake data, rollback.
- Текущие отдельные OPEN риски: недоказанный root cause исторического LLM FAILED; source probe cold latency margin; created-period grammar; task quality JSON leak; session ownership/auth for multi-user; отсутствие настоящего baseline committed predictability.


## P3.5. «Обзор» — аудит охвата пространств и исключение скрытого OLP-only фильтра (добавлено 2026-11-02)

**Наблюдение владельца:** на вкладке «Обзор» в очереди внимания PO преобладают задачи OLP, поэтому необходимо проверить, не применяется ли при расчёте сводных метрик, Daily Brief, очереди внимания и таблицы «Задачи по пространствам» скрытый или унаследованный фильтр **только по OLP**. Наличие OLP-задач на скриншоте **не доказывает**, что фильтр существует: это гипотеза для независимого A/B-аудита. **Требуемая семантика:** «Обзор» охватывает все доступные настроенные пространства продукта/команды (OLP, DMS, WMB, CRPV, STS и др. по конфигурации и правам), а не исключительно OLP. Не вводить исключение OLP из расчёта.

**Диагностика:**
1. Проследить полный data lineage по четырём карточкам («Активно», «Завершено», «Заблокировано», «Готовность портфеля»), `po_attention_queue`, Daily Brief, таблице по пространствам, snapshot/cache/refresh, роутам Task API, skill filters, team_members.yaml/products.yaml и AS21 source requests. Отдельно сверить параметры `space`, `spaces`, `project`, `assignee`, статус и возможные fallback/default `OLP`.
2. Независимый bounded **A/B/C oracle**: A — ответы приложения на одном snapshot/as_of; B — прямые scoped REAL AS21 read-only запросы по каждому настроенному пространству с ограниченной пагинацией и явным completeness; C — UI/DOM и network evidence. Для OLP, DMS, WMB, CRPV, STS отметить источник, права и возможное `source_unavailable`. Не выполнять tenant-wide scan.
3. Сверить единый знаменатель и **одинаковую область учёта** для всех показателей. Определить, считаются ли только задачи участников команды из `team_members.yaml`, и явно показать эту границу: «по пространствам» и «по команде» — разные срезы. Проверить dedupe canonical task key при пересечении назначений, отсутствие пропуска задач других пространств, лимиты выборки и правильную интерпретацию завершённых/заблокированных статусов.
4. Проверить, что очередь внимания PO при сортировке priority/aging/top-N **не маскирует** задачи других пространств без объяснения: отдельно рассчитать полное число подходящих задач, число показанных элементов и покрытие по пространствам. Большое количество OLP-задач может быть корректным результатом ранжирования, а не фильтром.
5. Проверить snapshot freshness/refresh и fail-closed: при сбое AS21/LLM/таймауте старые метрики должны быть явно помечены как кешированный снимок с временем, а не смешаны с новыми; при неполном источнике не выводить ложные 0 или 100%.
6. Если обнаружен OLP-only hardcode/default, исправлять **только вне замороженного Agent Core V4**, минимальным owner patch с регрессом всех метрик; не менять формулы без подтверждённого источника и спецификации.

**DoD:** доказан и документирован охват всех настроенных пространств и согласованность карточек/очереди/Daily Brief; независимое AS21 A/B и UI C parity с источником/временем; отсутствие скрытого OLP-only фильтра и недостоверных 0; корректная маркировка ограничений ролей/команды/топ-N; Core V4 6/6, полный V4/Task API/UI регресс GREEN. **Приоритет:** P3.5 — после завершения текущего P3.1 Delivery Forecast gate, до широких UI-улучшений P3.2–P3.4, если аудит не выявит критическую ошибку раньше.


## P3.1 — Delivery Forecast v1: end-to-end implementation submitted to integrated QA (2026-11-03)

**PO decision (approved):** `workflow_status.statusType=done` is terminal, Monday–Friday working week (holidays not modeled), timezone `Europe/Moscow`; observed throughput is an **operational projection of the currently visible sprint scope**, not committed Predictability. Approval is recorded in `task-api/config/sprint_forecast_policy.json` and must not be generalized to multi-tenant policy/authorization.

**Production vertical slice prepared in Review:**
- Source-verified bounded sprint membership and per-task workflow history, statusType/provenance/timestamp checks, reopened tasks, fail-closed validation, real sprint start/end from AS21.
- Local approved policy + scalar-only `GET /api/v1/swtr-read/sprints/{id}/delivery-forecast`; existing counts-only source-evidence endpoint preserved. Agent-side `GET /api/v1/sprints/{id}/delivery-forecast` uses typed source adapter.
- Additive, registry-discovered V4 Plugin Skill `sprint.delivery_forecast` without modification of the six frozen Core V4 files.
- «Спринты»: Delivery Forecast is the primary metric with loading/unknown states; historical committed Predictability remains a separate secondary card (N/A without source baseline).
- Implementation-stage synthetic tests for approved policy/typed forecasts/plugin; **NOT yet certified** by independent end-to-end QA; do not claim live forecast until REAL AS21 A/B + browser acceptance is GREEN.

**Acceptance:** one integrated independent GigaCode QA `A230R3.29-P31-DELIVERY-FORECAST-VERTICAL-E2E-QA` from `GIGACODE_NEXT_ACTION.md`. Verify real DMS-SPRNT-5, exact scope/date math, UI/browser & plugin, typed error states, data privacy, all V4/Task API/UI regressions, frozen Core 6/6. If GREEN, close P3.1 and proceed to P3.5 Overview cross-space audit; if RED, owner fixes only the demonstrated first failing boundary, then rerun this same integrated gate (do not spawn per-file QA loops).
