---
name: public-health-check
description: Многоуровневая проверка работоспособности публичного PO Agent: Task API, MCP-SWTR, 48 инструментов, REAL AS21, Agent Core V4, OpenAI-compatible LLM и UI. Используй после public-deploy, при пустых данных AS21, 502/503 и проверке готовности релиза.
---

# Public Health Check — GigaCode skill

## Контракт

**Health-check не равен ping.** HTTP 200 на `/health` подтверждает только соответствующий слой. Источник REAL AS21 подтверждается только ограниченным чтением **заведомо доступной** задачи; корректная работа LLM — отдельным агентным запросом с проверкой доказательств. Никогда не объявляй `GREEN` только потому, что процессы запустились или MCP зарегистрировал инструменты.

Только READ-ONLY HTTP/AS21 и локальная диагностика. Запрещено менять исходники, тесты, Core V4, конфигурации, токены и состояния AS21. Нельзя запускать `create_*`, `update_*`, `delete_*` MCP tools или массовую синхронизацию. Не открывай raw MCP для браузера. Никакого самостоятельного fallback в fake/local.

## Быстрая команда

Из корня **публичного** репозитория:

```bash
python3 scripts/public_health_check.py --task-code PAY-123 --probe-agent
```

`PAY-123` — ТОЛЬКО пример формата. Заменить на реально существующую задачу, к которой пользователь имеет доступ. Сценарий не должен притворяться, что демонстрационный код существует.

Команда выполняет проверки с заданными локальными портами 8003/8004/5175. Можно уточнить URL и таймаут:

```bash
python3 scripts/public_health_check.py \
  --task-api-url http://127.0.0.1:8003 \
  --agent-url http://127.0.0.1:8004 \
  --frontend-url http://127.0.0.1:5175 \
  --task-code PAY-123 --probe-agent --agent-timeout 180 --json
```

Не передавать токены в аргументах. Вывод скрипта должен содержать только технические статусы и классы ошибок, не сырые ответы источников.

## Уровни проверки

| Уровень | Доказательство | Ошибки |
|---|---|---|
| H0 — Prerequisites | Наличие public checkout, MCP Python 3.13 и настроенных локальных env **без их отображения** | отсутствует MCP runtime/неверный путь/нет Python |
| H1 — Task API | `GET http://127.0.0.1:8003/health` и `status=healthy` | процесс не запущен/порт/503 |
| H2 — MCP | `GET http://127.0.0.1:8003/api/v1/swtr-read/health` → `status=connected`, рабочие read capabilities; ожидаем порядка 48 инструментов (изменения — сравнить с версией) | stdio wrapper/отсутствует TOKEN или BASE_URL/SSE не подключён |
| H3 — Agent V4 | `GET http://127.0.0.1:8004/api/v1/health` → `status=healthy`, `adapter=task-api`, `agent_core_v4_ready=true`, `source_status=healthy` | fake mode, неинициализирован Core V4, падение адаптера |
| H4 — UI | `GET http://127.0.0.1:5175/` → HTML Vite; отдельно браузерный smoke | Vite/proxy на 8004/ошибки браузера |
| H5 — REAL AS21 | `GET /api/v1/swtr-read/tasks/{task_code}`; код ответа совпадает, `unit.code` подтверждён источником | 401/403 token, VPN/DNS, 404 область доступа, 502 источник |
| H6 — LLM + агент | `POST /api/v1/query` с ограниченным текстом о той же задаче; ожидается `COMPLETED` и ненулевая source evidence | LLM 429/таймаут, FAILED/PARTIAL/NEEDS_CLARIFICATION, hallucination/no evidence |

**Статусы:** `GREEN` только H1–H6, H0 и ручная проверка UI подтверждены; `INCOMPLETE`, если нет кода задачи или не запускался LLM-пробник; `RED`, если обязательная проверка упала. Скрипт кодирует это exit 0/2/1. Нет ложного GREEN при отсутствии REAL AS21.

## Диагностика «нет данных из AS21»

Проверяй первую сломанную границу в порядке:
1. H1 RED → Task API не слушает порт, DNS/порт локального сервиса, неверная виртуальная среда.
2. H2 RED → комплектный `mcp-swtr/`, Python 3.13, `mcp-swtr-wrapper.sh`, `SWTR_MCP_TRANSPORT`, переменные `SWTR_TOKEN`/`SWTR_MCP_BASE_URL` (проверить наличие, **не значение**), SSE URL.
3. H2 GREEN, H5 RED → сетевой доступ/корпоративный VPN, токен/роли/пространство, ограничения AS21. Не заменять FAILED пустым списком.
4. H5 GREEN, H3 RED → настройка `AS21_MODE=task-api`, `TASK_API_BASE_URL`, V4; не маскировать fake.
5. H5/H3 GREEN, H6 RED → LLM endpoint/model/key, запрос/планирование/grounding, таймаут, state; не чинить Core ради deployment.
6. H1–H6 GREEN, UI не работает → Vite proxy /api на 8004, браузерная консоль/Network; никакого прямого MCP в браузере.

**Осторожно:** статус MCP `connected` доказывает регистрацию инструментов, но ещё не права на чтение реальной задачи; статус Agent `healthy` не доказывает доступность внешней LLM, поэтому H5/H6 обязательны.

## Финальный отчёт

Укажи `TESTED_HEAD`, время, transport, технические HTTP-коды/задержки, H0–H6 по отдельности, счетчик MCP tools, REAL AS21 oracle YES/NO, Agent evidence count, первый failing boundary, результат `GREEN/INCOMPLETE/RED`, безопасные рекомендации. Скрывай тела ответов, токены, персональные данные, полные URL с секретами. Не создавай фиктивный QA-отчёт GREEN без фактического запуска.
