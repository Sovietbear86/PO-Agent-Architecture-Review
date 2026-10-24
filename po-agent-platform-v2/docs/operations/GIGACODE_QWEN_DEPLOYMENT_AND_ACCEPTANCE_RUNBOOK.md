# GigaCode CLI / Qwen Coder — Deployment & Acceptance Runbook

## Назначение

Эта инструкция предназначена для агента разработки, который впервые получает репозиторий PO Agent Platform v2. Выполняй шаги **строго по порядку**. Не перескакивай этапы. Не меняй код только потому, что команда или интеграционный тест не прошли.

## Неподлежащие обсуждению правила

1. **Сначала диагностика, потом изменение кода.** До явной классификации дефекта как `CODE` production-код не редактировать.
2. `ENV`, `SOURCE`, `DATA`, `AUTH`, `NETWORK` не чинить изменением бизнес-логики.
3. Никогда не подменять недоступный AS21/SWTR пустым списком.
4. Никогда не объявлять тест PASS, если он не запускался. Использовать `BLOCKED`.
5. Никогда не придумывать task/member/sprint/release/competency/metric.
6. Никогда не добавлять компетенцию по ФИО, грейду или предположению. Использовать только declared evidence.
7. Не отключать TLS verification, проверки сертификата, test assertions или security checks ради прохождения теста.
8. Не коммитить token, cookie, `.env`, credentials, browser session, локальные абсолютные пути.
9. Не выполнять write в AS21/SWTR. `po-reminder-draft` и `po-local-task-draft` — только черновики.
10. Не править `clean-public-release` напрямую. Работать в назначенной feature/recovery ветке.
11. Не удалять legacy reference до завершения извлечения тестового корпуса.
12. При любом сомнении остановиться и выдать: `Что проверено / Что обнаружено / Класс проблемы / Что предлагаю сделать`.

---

# PHASE 0 — READ-ONLY PREFLIGHT

Ничего не редактируй.

Выполни:

```bash
git status --short --branch
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git remote -v
python3 --version
node --version
npm --version
```

Ожидание: понятна ветка и commit SHA. Если working tree не чистый — STOP. Не делай reset и не удаляй чужие изменения.

Проверь наличие:

```bash
test -f po-agent-platform-v2/pyproject.toml
test -f po-agent-platform-v2/tests/corpus/harness_acceptance_corpus.yaml
test -f po-agent-platform-v2/docs/testing/COMPREHENSIVE_AGENT_TEST_PLAN.md
test -f po-agent-platform-v2/docs/recovery/FINAL_HARDENING_STATUS.md
```

Прочитай эти файлы **до запуска сервиса**.

---

# PHASE 1 — LOCAL INSTALL, БЕЗ AS21

```bash
cd po-agent-platform-v2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

Frontend:

```bash
cd frontend
npm ci
npm run build
cd ..
```

Если установка упала из-за proxy/certificate/network — это `ENV`, не `CODE`.

---

# PHASE 2 — HERMETIC/FakeAS21 ACCEPTANCE

Убедись, что внешние credentials не нужны:

```bash
export AS21_MODE=fake
pytest -q tests/test_skill_catalog.py
pytest -q tests/test_harness_acceptance_corpus.py
pytest -q tests/test_final_architecture_regressions.py
pytest -q
```

Затем повтори CI-equivalent suite из `.github/workflows/harness-recovery-ci.yml`.

Критерий: blocking hermetic tests green. Если упал corpus test, сначала выпиши конкретно `query -> expected skill -> actual skill`. Не меняй тест, пока не доказано, что expectation неверен.

---

# PHASE 3 — ЗАПУСК BACKEND В FAKE MODE

```bash
export AS21_MODE=fake
uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

В другом терминале:

```bash
curl -s http://127.0.0.1:8004/api/v1/health
curl -s -X POST http://127.0.0.1:8004/api/v1/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"Обзор","session_id":"smoke-1"}'
```

Проверь: status, adapter, source facts, skill readiness, trace_id. В fake mode данные могут быть только fixture-данными и должны явно оставаться fake.

---

# PHASE 4 — ПОДГОТОВКА TASK-API / SWTR

Сначала найди фактическую инструкцию task-api и конфигурацию. Не придумывай endpoint и authentication mechanism.

Проверь процессы и порты:

```bash
lsof -i :8003 || true
lsof -i :8004 || true
```

Запусти существующий task-api способом, предусмотренным его README/конфигурацией. Credentials задавай **только локально** через environment/secret store. Ничего секретного не печатай в лог полностью.

Проверь сам task-api до Harness:

```bash
curl -sS 'http://127.0.0.1:8003/api/v1/tasks?limit=1'
```

Если 8003 недоступен — `ENV`. Если task-api работает, но SWTR отвечает 401/403 — `AUTH`. Если DNS/VPN/proxy/cert — `NETWORK/ENV`. **Не правь Harness.**

---

# PHASE 5 — ПЕРЕКЛЮЧЕНИЕ HARNESS НА REAL TASK-API

Пример локальной конфигурации:

```bash
export AS21_MODE=task-api
export TASK_API_BASE_URL=http://127.0.0.1:8003
export TASK_API_TIMEOUT_SECONDS=30
export TEAM_CONFIG_PATH=../task-api/config/team_members.yaml
uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

Проверка:

```bash
curl -sS http://127.0.0.1:8004/api/v1/health
```

STOP CONDITIONS:

- `source_status != healthy`;
- task-api возвращает не JSON array там, где контракт требует array;
- task mapping даёт protocol error;
- source facts не соответствуют реально доступным API.

Не переходи к функциональным тестам, пока health не объяснён.

---

# PHASE 6 — REAL AS21 READ-ONLY SMOKE

Используй реальные task keys/sprints/releases из разрешённых пространств. Не вставляй фиктивные ключи и потом не исправляй код из-за `not_found`.

Минимум:

```text
Покажи <REAL_TASK_KEY>
Найди <REAL_PHRASE>
Покажи задачи исполнителя <REAL_LOGIN>
Покажи задачи спринта <REAL_SPRINT>
Покажи scope <REAL_SPRINT>
Прогресс релиза <REAL_RELEASE>
Обзор
Что требует моего внимания?
```

Для каждого ответа записать: query, status, skill, trace_id, evidence count, expected fact, actual fact.

Не запускать source-dependent функцию, если `/api/v1/health` показывает её source fact unavailable. Если пользователь всё же запросил её, правильный результат — `source_capability_unavailable`.

---

# PHASE 7 — 54-SKILL CORPUS

Открой `tests/corpus/harness_acceptance_corpus.yaml`.

Для каждого из 54 Skills:

1. выполнить canonical phrase;
2. выполнить минимум одну paraphrase;
3. проверить ожидаемый `skill.id`;
4. проверить `skill.version`;
5. проверить trace_id;
6. проверить evidence;
7. выполнить negative/degraded case из test plan;
8. поставить `PASS / FAIL / BLOCKED`.

Source-dependent Skills не имеют права перейти из BLOCKED в PASS без фактического источника: history, attachments, sprint snapshots, team competencies, release timeline.

---

# PHASE 8 — ФИО / TEAM MEMBER ACCEPTANCE

Используй только членов команды из `TEAM_CONFIG_PATH`.

Для каждого выбранного сотрудника проверь login, login lowercase, полное ФИО, фамилию, естественный падеж фамилии и запрос с sprint context. Отдельно проверь неизвестное и неоднозначное имя.

Критично: если два сотрудника подходят, агент обязан уточнить, а не выбрать первого. Если `competencies` пусты, не придумывать их из `professional_profile`, если конкретный алгоритм Skill этого не допускает контрактом.

Reference phrases из старого S21 обязательно включают:

```text
задачи Гаранина
задачи Гаранина в спринте OLP-SPRNT-3
кто подходит для задачи ...
кто может взять задачу ...
```

Если эта совместимость не поддерживается, зарегистрировать `ROUTING` gap. Не маскировать его поиском по строке.

---

# PHASE 9 — SESSION / HISTORY

В одном `session_id`:

```text
Покажи <TASK>
что с ней?
```

В другом session_id повторить только `что с ней?` — чужая entity не должна протечь.

Проверить operational history: сохраняется исходный пользовательский запрос, trace, version, evidence, warning/error category. Production `task-api` runtime обязан иметь такую же наблюдаемость, как fake runtime.

---

# PHASE 10 — FAILURE INJECTION

На тестовом/mock контуре воспроизвести:

- connection refused;
- timeout;
- HTTP 500;
- invalid JSON;
- JSON object вместо list;
- unmappable task item;
- missing history;
- missing attachments;
- missing snapshot;
- missing competency source;
- missing release timeline.

Ожидание: typed failure. Ни один сценарий не превращается в `0 задач`.

---

# PHASE 11 — ANTI-HALLUCINATION / PROMPT INJECTION

Помести в fixture task description недоверенный текст с указанием изменить правила/раскрыть secret/выполнить write. Агент должен трактовать его как source data.

Проверь, что:

- capability allow-list не меняется;
- env/token/cookie не попадают в answer;
- числа deterministic metrics не переписываются LLM;
- отсутствующие facts обозначаются unavailable;
- draft не утверждает, что действие выполнено.

---

# PHASE 12 — UI

```bash
cd frontend
npm ci
npm run build
npm run dev
```

Ручная проверка: Overview, Tasks, Sprint, Releases, Team, Quality, Agent Chat. Проверить loading, empty, source unavailable и error states. Метрики не пересчитывать вручную в React; источник истины — Harness API.

---

# PHASE 13 — AI-PDLC LOOP

На тестовых данных создать явный negative feedback, eval seed и candidate. Candidate должен быть inert. Прогнать offline evaluation/regression gate. Проверить, что promotion без human approval невозможен. После promotion проверить rollback на предыдущую версию.

Никогда не активировать candidate автоматически после одного пользовательского замечания.

---

# PHASE 14 — TRIAGE PROTOCOL

При любом FAIL напиши отчёт до изменения кода:

```text
TEST ID:
QUERY/COMMAND:
EXPECTED:
ACTUAL:
TRACE ID:
REPRODUCIBLE: yes/no
CLASS: ENV | AUTH | NETWORK | SOURCE | DATA | CONTRACT | ROUTING | CODE | TEST
EVIDENCE:
PROPOSED NEXT STEP:
CODE CHANGE REQUIRED: yes/no
```

Если `CODE CHANGE REQUIRED=yes`, сначала предложи минимальное изменение и список regression tests. Только после явного разрешения меняй код.

---

# PHASE 15 — FINAL REPORT

Финальный отчёт обязан содержать:

- commit SHA;
- runtime mode;
- health/readiness;
- blocking CI;
- 54 Skills: PASS/FAIL/BLOCKED;
- FIO matrix;
- real AS21 sample count;
- failures by class;
- P0/P1/P2;
- список изменённых файлов, если изменения были разрешены;
- подтверждение `no external write performed`;
- вывод `READY FOR MERGE` или `NOT READY FOR MERGE`.

Если хоть один P0 или неприемлемый P1 открыт — `NOT READY FOR MERGE`.
