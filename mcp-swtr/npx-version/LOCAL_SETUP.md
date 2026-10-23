# Локальный запуск без публикации в npm

Если пакет **ещё не опубликован** в корпоративный registry (или у вас нет к нему доступа), MCP можно подключить **напрямую из клонированного репозитория** — поведение то же, что у `npx mcp-swtr`, но источник — папка `npx-version/` на диске.

Публикация в registry: [PUBLISHING.md](PUBLISHING.md).  
Подключение опубликованной версии: [README.md](README.md).

---

## Что нужно

| Требование                  | Зачем                                                  |
| --------------------------- | ------------------------------------------------------ |
| **Node.js 20+**             | runtime и `npx`                                        |
| **Клон репозитория**        | каталог `npx-version/` с `package.json`                |
| **`BASE_URL`**, **`TOKEN`** | в конфиге MCP-клиента (как для опубликованного пакета) |

Корпоративный npm registry **не обязателен**.

---

## Подготовка (один раз и после `git pull`)

Все команды — из каталога **`npx-version/`** в вашем клоне:

```bash
cd /путь/к/mcp-swtr/npx-version
npm install
npm run build
```

| Шаг             | Результат                                                                        |
| --------------- | -------------------------------------------------------------------------------- |
| `npm install`   | `node_modules/` (dev-зависимости: esbuild, typescript, eslint)                   |
| `npm run build` | **`dist/index.js`** — один самодостаточный файл (744 KB), все зависимости внутри |

**После сборки `node_modules/` больше не нужен** — `dist/index.js` можно запускать напрямую.

Проверка в терминале:

```bash
node dist/index.js
```

Процесс зависнет на stdio — это нормально, завершите **Ctrl+C**.

Через `npx` из этой же папки:

```bash
npx -y file:.
```

После обновления репозитория (`git pull`): **`npm run build`** (если менялся `src/`). Если менялись только `devDependencies`, достаточно `npm install`.

---

## Путь к пакету

Запомните **абсолютный** путь к `npx-version` — его подставляют в конфиг MCP.

Примеры:

- macOS / Linux: `/Users/you/projects/mcp-swtr/npx-version`
- Windows: `C:\Users\you\projects\mcp-swtr\npx-version`

В JSON для Windows в путях `file:` часто используют прямые слэши: `file:C:/Users/you/.../npx-version`.

Относительный `file:./npx-version` в MCP **не рекомендуется**: рабочая директория IDE может быть любой, путь не найдётся.

---

## Способ 1 — `npx` + `file:` (как опубликованный пакет)

Аналог `npx -y mcp-swtr@1.0.0`, но пакет берётся с диска.

Перед первым запуском в IDE должны быть выполнены `npm install` и `npm run build` (см. выше).

### Cursor

`~/.cursor/mcp.json` или MCP проекта:

```json
{
    "mcpServers": {
        "swtr": {
            "command": "npx",
            "args": ["-y", "file:/Users/you/projects/mcp-swtr/npx-version"],
            "env": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            }
        }
    }
}
```

### OpenCode

`~/.config/opencode/opencode.json` — поле **`environment`**, не `env`:

```json
{
    "mcp": {
        "swtr": {
            "type": "local",
            "enabled": true,
            "command": ["npx", "-y", "file:/Users/you/projects/mcp-swtr/npx-version"],
            "environment": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            }
        }
    }
}
```

### Roo Code

`~/.roo/mcp.json` или `.roo/mcp.json`:

```json
{
    "mcpServers": {
        "swtr": {
            "command": "npx",
            "args": ["-y", "file:/Users/you/projects/mcp-swtr/npx-version"],
            "env": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            },
            "disabled": false
        }
    }
}
```

**Windows** (если `npx` из Roo не стартует):

```json
{
    "mcpServers": {
        "swtr": {
            "command": "cmd",
            "args": ["/c", "npx", "-y", "file:C:/Users/you/projects/mcp-swtr/npx-version"],
            "env": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            }
        }
    }
}
```

После правки конфига — **перезапуск IDE** или переподключение MCP.

---

## Способ 2 — прямой запуск `node` (надёжнее для IDE)

Не зависит от кэша `npx`, если сборка уже есть. **`node_modules/` не требуется** (все зависимости внутри `dist/index.js`).

### Cursor / Roo

```json
{
    "mcpServers": {
        "swtr": {
            "command": "node",
            "args": ["/Users/you/projects/mcp-swtr/npx-version/dist/index.js"],
            "env": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            }
        }
    }
}
```

### OpenCode

```json
"command": ["node", "/Users/you/projects/mcp-swtr/npx-version/dist/index.js"],
"environment": {
    "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
    "TOKEN": "<your_token>"
}
```

На Windows укажите полный путь к `node.exe` при необходимости и путь к `dist\index.js` с экранированием в JSON.

---

## Способ 3 — глобальная команда `mcp-swtr` (опционально)

Удобно для ручных проверок в терминале; в MCP можно указать `"command": "mcp-swtr"`.

Из каталога **`npx-version/`**:

```bash
npm run link
```

Скрипт сам определит bin-директорию (`~/.local/bin` → `~/bin` → `/usr/local/bin`), соберёт проект (если нужно) и создаст симлинк:

```
✓ Linked: /home/user/.local/bin/mcp-swtr → .../npx-version/dist/index.js
```

Проверка:

```bash
mcp-swtr
# Ctrl+C
```

В `mcp.json`:

```json
{
    "mcpServers": {
        "swtr": {
            "command": "mcp-swtr",
            "args": [],
            "env": {
                "BASE_URL": "https://AS21_INTERNAL_URL_PLACEHOLDER/swtr",
                "TOKEN": "<your_token>"
            }
        }
    }
}
```

Отвязка:

```bash
npm run unlink
```

---

## Сравнение способов

| Способ               | Плюсы                                   | Минусы                                     |
| -------------------- | --------------------------------------- | ------------------------------------------ |
| `npx` + `file:`      | Близко к боевому `npx mcp-swtr@version` | Первый старт медленнее, нужен `npx` в PATH |
| `node dist/index.js` | Предсказуемый путь, быстрый старт IDE   | Абсолютный путь в конфиге                  |
| `npm link`           | Короткая команда в конфиге              | Глобальная установка, один путь на машину  |

---

## Частые проблемы

| Симптом                                      | Что сделать                                                          |
| -------------------------------------------- | -------------------------------------------------------------------- |
| Нет `dist/index.js`                          | `npm run build` (сборка ~30 мс)                                      |
| 404 / package not found при `mcp-swtr@1.0.0` | Пакет не в registry — перейти на `file:` или `node` (эта инструкция) |
| Tools не появляются                          | Перезапустить IDE; проверить путь (абсолютный `file:`)               |
| После `git pull` сломалось                   | `npm run build` (если менялся `src/`)                                |
| `BASE_URL` / `TOKEN`                         | Задать в `env` (Cursor, Roo) или `environment` (OpenCode)            |
| Windows + Roo                                | Конфиг с `cmd /c` (см. выше)                                         |

---

## Чеклист

- [ ] Node.js 20+
- [ ] Репозиторий склонирован
- [ ] `npm install` и `npm run build` в `npx-version/`
- [ ] В конфиге MCP — абсолютный `file:...` или путь к `dist/index.js`
- [ ] `node_modules/` после сборки **не нужна** — `dist/index.js` самодостаточен
- [ ] `BASE_URL` и `TOKEN` в env
- [ ] IDE перезапущена
- [ ] В списке tools видны инструменты SWTR

Когда пакет опубликуют — достаточно заменить `file:...` на `mcp-swtr@<version>` в [README.md](README.md).
