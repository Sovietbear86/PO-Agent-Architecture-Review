# @abac/mcp-swtr (Node / npx)

MCP-сервер для **SberWorks Task Tracker**: те же инструменты, что в Python-версии, запуск через `npx` и stdio (Cursor, OpenCode, Roo Code).

## Требования

- Node.js **20+**
- `BASE_URL` и `TOKEN` для SWTR API
- Корпоративный npm registry — только если ставите **опубликованный** пакет (`mcp-swtr@version`). Без registry: **[LOCAL_SETUP.md](LOCAL_SETUP.md)**

## Переменные окружения

| Переменная       | Обязательно | Описание                                                                          |
| ---------------- | ----------- | --------------------------------------------------------------------------------- |
| `BASE_URL`       | да          | Базовый URL SWTR, без `/` в конце (например `https://AS21_INTERNAL_URL_PLACEHOLDER/swtr`) |
| `TOKEN`          | да          | Access token (Bearer)                                                             |
| `DISABLED_TOOLS` | нет         | Список имён tools через запятую — не регистрируются и не видны клиенту            |

Проверка конфигурации выполняется при **первом вызове tool** (не при `tools/list`), чтобы клиент мог подключиться без токена в dev.

### `DISABLED_TOOLS` — отключение инструментов

В переменной можно перечислить через запятую имена tools, которые **не будут зарегистрированы** на сервере. Они исчезают из списка `tools/list` и недоступны модели — это надёжнее, чем полагаться на системный промпт.

Пробелы вокруг запятых игнорируются. Пример — оставить **только read-only**, отключив все операции записи/изменения/удаления:

```json
"env": {
    "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
    "TOKEN": "<your_token>",
    "DISABLED_TOOLS": "create_unit,update_unit,create_unit_link,create_unit_comment,create_wiki_page,create_test_case,create_test_case_step,update_test_case_data,update_test_case_parameters,create_test_cycle,link_test_case_to_test_cycle,create_work_log,create_work_log_range,update_work_log,delete_work_log"
}
```

После такого конфига доступными остаются только read-only инструменты: `read_unit`, `find_units`, `find_units_by_filter`, `get_tql_properties`, `get_unit_types_by_space`, `get_unit_comments`, `get_unit_links`, `get_unit_attributes`, `search_link_types`, `search_users`, `search_versions`, `search_sprints`, `search_wiki_pages`, `read_wiki_page`, `search_test_cases`, `get_test_case_folders`, `read_test_case`, `get_step_info_parameters`, `get_test_cases`, `get_test_cases_in_test_cycle`, `get_work_types`, `get_work_log`, `get_work_report`, `get_work_sum`.

## Документация

| Документ                         | Для кого                                            |
| -------------------------------- | --------------------------------------------------- |
| [LOCAL_SETUP.md](LOCAL_SETUP.md) | Запуск **из репозитория**, если пакет не в registry |
| [PUBLISHING.md](PUBLISHING.md)   | Публикация в корпоративный npm                      |

## Подключение клиентов (опубликованный пакет)

### Cursor

Файл: `~/.cursor/mcp.json` (или MCP в настройках проекта).

```json
{
    "mcpServers": {
        "swtr": {
            "command": "npx",
            "args": [
                "-y",
                "--registry=https://AS21_INTERNAL_URL_PLACEHOLDER/ssd/tools/nexus-ci/repository/sbt_npm/",
                "@abac/mcp-swtr@latest"
            ],
            "env": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            }
        }
    }
}
```

> `--registry` нужен, потому что корпоративный npm registry настроен глобально и не содержит публичных пакетов.

Запуск из клона без registry: **[LOCAL_SETUP.md](LOCAL_SETUP.md)**.

После изменения конфига перезапустите Cursor или переподключите MCP.

### OpenCode

Файл: `~/.config/opencode/opencode.json`. Для local MCP используется поле **`environment`** (не `env`).

```json
{
    "mcp": {
        "swtr": {
            "type": "local",
            "enabled": true,
            "command": [
                "npx",
                "-y",
                "--registry=https://AS21_INTERNAL_URL_PLACEHOLDER/ssd/tools/nexus-ci/repository/sbt_npm/",
                "@abac/mcp-swtr@latest"
            ],
            "environment": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            }
        }
    }
}
```

### Roo Code

Глобально: MCP Settings → Edit Global MCP (`mcp_settings.json`) или `~/.roo/mcp.json`.  
В проекте: `.roo/mcp.json`.

```json
{
    "mcpServers": {
        "swtr": {
            "command": "npx",
            "args": [
                "-y",
                "--registry=https://AS21_INTERNAL_URL_PLACEHOLDER/ssd/tools/nexus-ci/repository/sbt_npm/",
                "@abac/mcp-swtr@latest"
            ],
            "env": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            },
            "disabled": false
        }
    }
}
```

**Windows** (если `npx` не стартует из Roo):

```json
{
    "mcpServers": {
        "swtr": {
            "command": "cmd",
            "args": [
                "/c",
                "npx",
                "-y",
                "--registry=https://AS21_INTERNAL_URL_PLACEHOLDER/ssd/tools/nexus-ci/repository/sbt_npm/",
                "@abac/mcp-swtr@latest"
            ],
            "env": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            }
        }
    }
}
```

Документация: [Using MCP in Roo Code](https://docs.roocode.com/features/mcp/using-mcp-in-roo).

## Каталог tools

### Юниты

| Tool                      | Описание                      |
| ------------------------- | ----------------------------- |
| `read_unit`               | Чтение юнита по коду          |
| `get_unit_types_by_space` | Типы юнитов в пространстве    |
| `find_units`              | Поиск юнитов по пространствам |
| `get_tql_properties`      | Атрибуты для TQL-фильтра      |
| `create_unit`             | Создание юнита                |
| `create_unit_link`        | Связь между юнитами           |
| `create_unit_comment`     | Комментарий к юниту           |
| `get_unit_comments`       | Комментарии юнита             |
| `search_link_types`       | Типы связей                   |
| `get_unit_links`          | Связи юнита                   |
| `get_unit_attributes`     | Справочник атрибутов          |
| `search_versions`         | Поиск релизов                 |
| `search_sprints`          | Поиск спринтов                |

### Вики

| Tool                | Описание           |
| ------------------- | ------------------ |
| `search_wiki_pages` | Поиск wiki-страниц |
| `read_wiki_page`    | Чтение страницы    |
| `create_wiki_page`  | Создание страницы  |

### Тест-кейсы и циклы

| Tool                           | Описание                     |
| ------------------------------ | ---------------------------- |
| `search_test_cases`            | Поиск в каталоге             |
| `get_test_case_folders`        | Корневые каталоги            |
| `read_test_case`               | Чтение тест-кейса            |
| `create_test_case`             | Создание                     |
| `create_test_case_step`        | Шаги                         |
| `update_test_case_data`        | Тестовые данные              |
| `update_test_case_parameters`  | Параметры                    |
| `get_step_info_parameters`     | Параметры шагов              |
| `create_test_cycle`            | Тест-цикл                    |
| `get_test_cases`               | Список кейсов в пространстве |
| `get_test_cases_in_test_cycle` | Кейсы в цикле                |
| `link_test_case_to_test_cycle` | Привязка к циклу             |

### Таймшит

| Tool                    | Описание           |
| ----------------------- | ------------------ |
| `get_work_types`        | Виды работ         |
| `create_work_log`       | Списание           |
| `create_work_log_range` | Списание за период |
| `get_work_log`          | Одно списание      |
| `update_work_log`       | Изменение          |
| `delete_work_log`       | Удаление           |
| `get_work_report`       | Отчёт по юниту     |
| `get_work_sum`          | Сумма по юниту     |

### Пользователи

| Tool           | Описание            |
| -------------- | ------------------- |
| `search_users` | Поиск пользователей |

## Python vs Node

|           | Python ([mcp_server.py](../mcp_server.py)) | Node (этот пакет)    |
| --------- | ------------------------------------------ | -------------------- |
| Транспорт | SSE, порт `PORT`                           | stdio                |
| Запуск    | `python mcp_server.py`, Docker             | `npx @abac/mcp-swtr` |
| Конфиг    | `.env`                                     | env в MCP-клиенте    |

## Troubleshooting

| Симптом                         | Что проверить                                                                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Нет tools в клиенте             | Перезапуск IDE; `npx -y --registry=https://AS21_INTERNAL_URL_PLACEHOLDER/ssd/tools/nexus-ci/repository/sbt_npm/ @abac/mcp-swtr` в терминале |
| Ошибка про `BASE_URL` / `TOKEN` | `env` / `environment` в конфиге MCP                                                                                                 |
| 401 / 403                       | Актуальность токена                                                                                                                 |
| TLS / certificate               | Корпоративный CA; в коде отключена проверка сертификата (как в Python `verify=False`)                                               |
| 404 при `npx`                   | Пакет не в registry — [LOCAL_SETUP.md](LOCAL_SETUP.md) (`file:` или `node dist/index.js`)                                           |
| Windows                         | Конфиг Roo с `cmd /c` (см. выше)                                                                                                    |

## Лицензия

MIT
