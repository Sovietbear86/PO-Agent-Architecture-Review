# PO Agent Platform v2 — Bootstrap для GigaCode CLI / QwenCoder

## Цель

Развернуть актуальную версию PO Agent Platform v2 из GitHub, восстановить рабочие локальные интеграции из уже существующей локальной среды пользователя, подключить QwenCoder и SWTR/AS21, затем выполнить полный hermetic + real-data acceptance с обязательным диагностическим логированием.

Главное правило: **не перепроектировать приложение и не переписывать production-код до доказательства, что ошибка относится к категории CODE.**

---

## 1. Source of truth

Repository:

`Sovietbear86/PO-Agent-Architecture-Review`

Рабочая ветка:

`chatgpt-harness-recovery`

Canonical application:

`po-agent-platform-v2/`

Старая локальная копия проекта может использоваться только как источник:

- уже действующих локальных credentials;
- локальной конфигурации GigaCode/SWTR;
- сведений о том, какие корпоративные endpoints реально использовались;
- reference поведения старых S21 agents.

Она **не является source of truth для кода новой версии**.

---

## 2. Сначала прочитать документацию

До любых изменений полностью прочитать:

1. `PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md`
2. `po-agent-platform-v2/docs/architecture/HARNESS_DIALOGUE_LEARNING_CONTRACT.md`
3. `po-agent-platform-v2/docs/testing/COMPREHENSIVE_AGENT_TEST_PLAN.md`
4. `po-agent-platform-v2/docs/testing/GIGACODE_QWENCODER_REAL_DATA_RUNBOOK.md`
5. `po-agent-platform-v2/docs/operations/REAL_DATA_PILOT_ACCEPTANCE_CHECKLIST.md`
6. `po-agent-platform-v2/docs/review/FINAL_CODE_ARCHITECTURE_REVIEW.md`
7. корневой `README.md`

После чтения вывести краткое подтверждение:

`ARCHITECTURE UNDERSTOOD: YES`

и перечислить:

- Dialogue Harness;
- LLM semantic interpreter;
- source-backed grounding;
- clarification gate;
- versioned Skills;
- deterministic capabilities/metrics;
- TaskApiAS21Adapter / task-api / SWTR boundary;
- feedback + AI-PDLC learning loop.

До этого production-код не менять.

---

## 3. Получить актуальную ветку

Если репозитория локально нет:

```bash
git clone <repository-url>
cd PO-Agent-Architecture-Review
```

Если репозиторий уже есть:

```bash
git fetch --all --prune
git checkout chatgpt-harness-recovery
git pull --ff-only origin chatgpt-harness-recovery
```

Показать:

```bash
git status
git branch --show-current
git rev-parse HEAD
```

Рабочее дерево до начала должно быть чистым.

Если есть локальные изменения — не удалять их автоматически. Сначала вывести список и определить, не являются ли они локальными credentials/configuration.

---

## 4. Credentials: использовать уже действующие локальные

Пользователь **не будет вручную обновлять или перевыпускать токены в рамках этого запуска**.

Поэтому необходимо выполнить READ-ONLY discovery текущей локальной среды и найти **уже действующие credentials**, которыми пользовались прежняя локальная копия проекта, GigaCode CLI, task-api или SWTR tooling.

Разрешено проверять:

- environment variables;
- `~/.config/`;
- `~/.config/swtr/`;
- `~/.gigacode/`;
- user-level GigaCode configuration;
- локальные `.env` в старой рабочей копии проекта;
- другие локальные ignored config-файлы старой рабочей копии;
- локальные MCP settings, если они не находятся в Git и используются текущей машиной.

Если в старой **локальной рабочей копии** найден credential, который реально проходит read-only проверку, его разрешено переиспользовать в новой локальной конфигурации.

### Запрещено

- брать credential из GitHub history;
- восстанавливать секрет из удалённого файла публичного репозитория;
- commit-ить токен/JWT/cookie/API key;
- печатать полный secret в терминал;
- писать secret в `sanitized.log`;
- отправлять secret в ChatGPT;
- переносить secret в tracked config-файл.

### Безопасный вывод discovery

Для каждого найденного credential выводить только:

```text
SWTR_TOKEN: FOUND | NOT FOUND
SWTR_TOKEN_LENGTH: <n>
SWTR_TOKEN_SUFFIX: <last 4 chars>
SWTR_TOKEN_VALIDATION: PASS | FAIL | NOT_TESTED

QWEN_API_KEY: FOUND | NOT FOUND
QWEN_API_KEY_LENGTH: <n>
QWEN_API_KEY_SUFFIX: <last 4 chars>
QWEN_API_KEY_VALIDATION: PASS | FAIL | NOT_TESTED

PLATFORM_SESSION: FOUND | NOT FOUND
PLATFORM_SESSION_VALIDATION: PASS | FAIL | NOT_TESTED
```

Полное значение не выводить.

### Как определить, что credential действующий

Проверять только минимальным read-only запросом.

Если несколько локальных credentials — выбрать тот, который:

1. проходит auth;
2. относится к нужному endpoint;
3. используется текущей рабочей средой;
4. не требует изменения production-кода.

Если найденный credential истёк или возвращает 401/403, классифицировать это как `AUTH` и остановить соответствующую интеграционную ветку тестирования. Не пытаться маскировать проблему кодом.

---

## 5. Куда поместить найденные действующие credentials

Допустимые места:

- environment variables;
- локальный `.env`, который находится под `.gitignore`;
- `~/.config/...`;
- user-level GigaCode config;
- иной локальный ignored secret store.

Перед продолжением проверить:

```bash
git status
git check-ignore .env
```

Если используется `.env`, создавать его на основании `.env.example`, но никогда не commit-ить.

---

## 6. Не возвращать старую архитектуру

Запрещено:

- делать `POOrchestratorV1` production runtime;
- заменять semantic interpreter большим набором regex;
- писать таблицы всех склонений ФИО;
- давать LLM право подтверждать существование task/member/sprint/release без source grounding;
- считать PO-метрики через LLM;
- превращать отказ SWTR в пустой список задач;
- создавать fake entity, если реальный source её не подтвердил.

Canonical flow:

`User → Dialogue Harness → LLM Semantic Interpreter → Grounding → Clarification Gate → Skill → Deterministic Capability → Evidence → Response → Feedback → AI-PDLC`

---

## 7. Backend setup

```bash
cd po-agent-platform-v2
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

Если установка зависимостей падает — сначала `ENV`, а не CODE.

---

## 8. Frontend setup

```bash
cd frontend
npm ci
npm run build
cd ..
```

Если build зелёный — не обновлять зависимости «на всякий случай».

---

## 9. Hermetic baseline — до реального SWTR

Запускать через diagnostic runner:

```bash
python tools/diagnostic_runner.py \
  --name hermetic-baseline \
  -- pytest -q \
  --ignore=tests/test_integration_real_services.py \
  --ignore=tests/test_llm_real_integration.py \
  --ignore=tests/test_agent_full_integration.py \
  --ignore=tests/test_orchestrator_skill_integration.py \
  --ignore=tests/test_frontend_config.py
```

Ожидание: `PASS`.

Если FAIL — не переходить к реальному SWTR, пока причина не классифицирована.

---

## 10. Diagnostic runner обязателен

Каждый значимый этап запускать через:

`tools/diagnostic_runner.py`

Он создаёт:

`.artifacts/diagnostics/<RUN_ID>/`

с файлами:

- `raw.log` — локальный, не передавать;
- `sanitized.log` — для анализа;
- `summary.json` — структурированная сводка.

После каждого FAIL/BLOCKED вывести:

```text
RUN_ID:
TEST_STAGE:
RESULT:
PRIMARY_CLASS:
SECONDARY_CLASSES:
FIRST_FAILED_OPERATION:
PRODUCTION_CODE_CHANGE_NEEDED:
NEXT_SAFE_CHECK:
```

Допустимые классы:

`ENV / AUTH / NETWORK / SOURCE / DATA / CODE / UNKNOWN`

Production-код разрешено менять только при доказанном `CODE`.

---

## 11. Проверка Qwen semantic layer

Нужно доказать, что используется реальный QwenCoder, а не regex как основной NLP слой.

Проверить:

- модель отвечает;
- SemanticFrame валиден;
- confidence возвращается;
- malformed response обрабатывается безопасно;
- LLM не считает deterministic metrics;
- LLM не подтверждает entity без source;
- при неоднозначности возникает clarification.

Ключевой тест:

`Покажи открытые задачи Гаранина в спринте OLP 4`

Ожидаемое поведение:

- определить task-search intent;
- выделить person candidate;
- выделить sprint candidate;
- выделить бизнес-семантику «открытые»;
- проверить person/sprint/status semantics по source/config;
- если что-то неоднозначно — задать вопрос;
- после ответа пользователя продолжить исходный запрос без повторного ввода.

Молчаливое угадывание = FAIL.

---

## 12. Проверка SWTR/AS21

Использовать найденный действующий локальный credential.

Начинать только с read-only минимальных операций:

1. endpoint reachable;
2. TLS/connectivity;
3. auth;
4. single task read;
5. небольшой task search;
6. status values;
7. assignee/FIO/login structure;
8. sprint data;
9. release data;
10. comments/attachments/history capabilities.

Для каждого этапа — отдельный RUN_ID.

Если 401/403 → `AUTH`.
Если timeout/VPN/DNS → `NETWORK`.
Если endpoint/capability реально отсутствует → `SOURCE`.
Если entity отсутствует в данных → `DATA`.

---

## 13. task-api boundary

Запустить task-api отдельно и проверить health.

Далее проверить путь:

`Harness → TaskApiAS21Adapter → task-api → SWTR`

Не встраивать прямые SWTR вызовы в отдельные Skills.

---

## 14. Source Readiness

```bash
python tools/diagnostic_runner.py \
  --name source-readiness \
  -- pytest -q \
  tests/test_harness_source_readiness.py \
  tests/test_harness_source_contracts.py \
  tests/test_task_api_as21_adapter.py
```

Главный принцип:

`implemented != source-ready`

Если нужной source capability нет — Skill должен честно стать `unavailable`, а не генерировать правдоподобный ответ.

---

## 15. Полный 54-Skill acceptance

Canonical corpus:

`tests/corpus/harness_acceptance_corpus.yaml`

Для каждого сценария проверять:

- intent;
- выбранный Skill;
- entity grounding;
- clarification;
- evidence;
- deterministic metric correctness;
- no hallucination;
- feedback prompt.

---

## 16. Обязательные многоходовые диалоги

### Сценарий 1 — неоднозначная семантика

Пользователь:

`Покажи открытые задачи Гаранина в спринте OLP 4`

Если «открытые» не определено правилами команды — агент спрашивает, какие статусы считать открытыми.

Пользователь:

`Все незавершённые.`

Агент продолжает исходный запрос.

### Сценарий 2 — неоднозначный человек

Если source находит нескольких кандидатов по фамилии — агент предлагает grounded варианты и просит выбрать.

### Сценарий 3 — сохранение контекста

Пользователь:

`Покажи задачи Гаранина.`

Затем:

`А из них какие заблокированы?`

Агент сохраняет previous scope.

### Сценарий 4 — learning

Пользователь исправляет семантику:

`Нет, под открытыми у нас всегда понимаются все задачи кроме Closed и Resolved.`

Агент не переписывает Python. Он создаёт feedback / config-learning candidate / regression eval и применяет изменение только по governance.

---

## 17. Anti-hallucination gate

Отдельно проверить:

- выдуманный login;
- несуществующий task;
- несуществующий sprint;
- несуществующий release;
- несуществующий status.

Даже если LLM уверенно предложила entity, source должен подтвердить её существование.

Нет подтверждения → clarification / not found / unavailable.

Молчаливое принятие выдуманной entity = FAIL.

---

## 18. Feedback и self-learning

После полезного ответа агент должен запросить ОС.

Проверить:

- positive feedback;
- negative feedback;
- corrective feedback.

Corrective feedback должен:

- сохраняться в history;
- создавать eval/improvement candidate;
- при необходимости создавать configuration candidate;
- создавать regression case;
- не менять production-код самостоятельно;
- при конфликте правил не активировать новую семантику без governance.

---

## 19. Real-data evidence

Реальные ФИО, внутренние task IDs, ответы SWTR и прочая внутренняя информация не должны попадать в публичный test corpus.

Real-data diagnostics хранить только локально в:

`.artifacts/diagnostics/`

Эта директория не должна коммититься.

---

## 20. Что передать ChatGPT после тестирования

Создать локально:

`.artifacts/diagnostics/FINAL_ACCEPTANCE/`

Поместить туда только безопасные материалы:

- `FINAL_ACCEPTANCE_REPORT.md`;
- `summary.json` каждого FAIL/BLOCKED;
- `sanitized.log` каждого FAIL/BLOCKED.

В итоговом отчёте указать:

```text
Git SHA
OS
Python version
Node version
Qwen model
Qwen connectivity: PASS/FAIL
SWTR connectivity: PASS/FAIL
Task-api connectivity: PASS/FAIL
54 Skills: PASS/FAIL/BLOCKED
Dialogue scenarios: PASS/FAIL/BLOCKED
Grounding: PASS/FAIL
Clarification: PASS/FAIL
Anti-hallucination: PASS/FAIL
Feedback: PASS/FAIL
Learning lifecycle: PASS/FAIL
Frontend: PASS/FAIL
```

Таблица проблем:

```text
ID
RUN_ID
STAGE
CLASS
DESCRIPTION
REPRODUCIBLE
CODE_CHANGE_REQUIRED
PROPOSED_NEXT_ACTION
```

Перед передачей ещё раз убедиться, что в `sanitized.log` и отчёте нет секретов.

---

## 21. Stop conditions

Если:

- действующий локальный SWTR credential не найден;
- найденный credential возвращает 401/403;
- отсутствует VPN/network route;
- Qwen credential недействителен;
- SWTR API возвращает новый неизвестный контракт;

то:

1. собрать diagnostics;
2. классифицировать ошибку;
3. не переписывать production-код;
4. остановить только зависимую ветку real-data тестов;
5. продолжить те hermetic/локальные проверки, которые не зависят от проблемы.

---

## 22. Definition of Done для real-data pilot

Pilot можно считать успешно завершённым только если:

- hermetic baseline PASS;
- frontend PASS;
- real Qwen semantic layer PASS;
- найден и успешно использован действующий локальный SWTR credential;
- task-api PASS;
- source readiness соответствует реальным capabilities;
- 54 Skills корректно разделяются на available/unavailable;
- clarification работает многоходово;
- session context сохраняется;
- hallucinated entities отклоняются;
- metrics deterministic;
- evidence присутствует;
- feedback записывается;
- learning идёт через governed configuration/eval lifecycle;
- secrets не попали в Git;
- все FAIL/BLOCKED имеют классификацию и diagnostics.

После этого **не выполнять merge автоматически**.

Сначала передать `FINAL_ACCEPTANCE_REPORT.md`, `summary.json` и `sanitized.log` в ChatGPT для финального независимого review.
