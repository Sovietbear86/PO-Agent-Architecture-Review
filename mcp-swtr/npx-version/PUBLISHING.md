# Публикация `mcp-swtr` (инструкция для администратора)

Документ для того, кто **собирает и публикует** npm-пакет в корпоративный registry.

- Пользователи (опубликованный пакет): [README.md](README.md)
- Пользователи **без** registry (клон репозитория): [LOCAL_SETUP.md](LOCAL_SETUP.md)

---

## Что публикуется

| Параметр    | Значение                                                                            |
| ----------- | ----------------------------------------------------------------------------------- |
| Имя пакета  | `mcp-swtr`                                                                          |
| Точка входа | `bin.mcp-swtr` → `dist/index.js` (stdio MCP)                                        |
| В tarball   | только `dist/`, `README.md`, `LICENSE` (см. `files` в [package.json](package.json)) |
| Node.js     | **≥ 20**                                                                            |

Исходники (`src/`) в registry **не попадают** — перед publish обязательна сборка TypeScript → `dist/`.

---

## Что потребуется

### ПО на машине публикации

- **Node.js 20+** и **npm** (идут вместе с Node)
- **Git** — клон репозитория с актуальной веткой релиза
- Сетевой доступ к **корпоративному npm registry**

### Доступы и учётные данные

- Право **publish** для пакета `mcp-swtr` в целевом registry (роль maintainer / CI service account)
- **Токен registry** (`NPM_TOKEN` или результат `npm login`) — не коммитить в репозиторий
- URL registry (подставляется в `.npmrc` и `publishConfig.registry`)

### Одноразовая настройка репозитория (до первого publish)

1. **`publishConfig.registry`** в [package.json](package.json) — заменить placeholder `https://YOUR_CORP_NPM_REGISTRY/` на реальный URL.
2. **Файл `LICENSE`** в каталоге `npx-version/` — в `package.json` он указан в `files`, без него tarball неполный (лицензия MIT).
3. При необходимости — **scope** (`@your-org/mcp-swtr`): тогда меняют `name` в `package.json` и документацию клиентов (`npx @your-org/mcp-swtr`).

### Для CI (опционально)

- Секрет `NPM_TOKEN` с правом publish
- Job: `npm ci` → lint/format (по политике) → `npm publish` (см. раздел «Публикация из CI»)

---

## Первичная настройка registry

```bash
cd npx-version
cp .npmrc.example .npmrc
```

Отредактировать `.npmrc` (файл **в `.gitignore` не обязан быть**, но токен — только локально или в CI):

```ini
registry=https://<ваш-корпоративный-registry>/
//<ваш-корпоративный-registry>/:_authToken=${NPM_TOKEN}
```

Авторизация — один из вариантов:

```bash
# интерактивно
npm login --registry=https://<ваш-корпоративный-registry>/

# или через переменную (CI / скрипт)
export NPM_TOKEN="<токен>"
```

Проверка, что registry отвечает и токен валиден:

```bash
npm whoami --registry=https://<ваш-корпоративный-registry>/
```

---

## Сборка

Все команды — из каталога **`npx-version/`**.

```bash
npm install          # зависимости, в т.ч. dev (typescript, eslint)
npm run build        # tsc → каталог dist/
```

Проверки качества (рекомендуется перед релизом):

```bash
npm run lint
npm run format:check
```

| Скрипт                 | Действие               |
| ---------------------- | ---------------------- |
| `npm run build`        | `tsc`, выход в `dist/` |
| `npm run lint`         | ESLint по `src/`       |
| `npm run format:check` | Prettier без записи    |

`dist/` в git не хранится (см. `.gitignore`) — собирается локально или в CI перед publish.

---

## Проверка без публикации

### 1. Содержимое tarball

```bash
npm pack --dry-run
```

Убедиться, что в списке есть `package/dist/...`, `README.md`, `LICENSE`.

### 2. Локальный запуск как у пользователей

```bash
node dist/index.js
# процесс ждёт stdio — прервать Ctrl+C

# или через npx из папки пакета:
npx -y file:.
```

В MCP-клиенте для отладки: `"args": ["-y", "file:/абсолютный/путь/к/npx-version"]`.

### 3. Smoke через MCP (по желанию)

Подключить локальный `file:` в Cursor/OpenCode, вызвать любой tool с валидными `BASE_URL` и `TOKEN` — ошибка конфигурации должна появляться только при вызове tool, не при `tools/list`.

---

## Версионирование

Перед каждым релизом обновить **`version`** в [package.json](package.json) по [semver](https://semver.org/):

- **patch** — исправления, без изменения API tools
- **minor** — новые tools или обратно совместимые изменения схем
- **major** — ломающие изменения имён/полей tools (редко)

```bash
npm version patch   # или minor / major — создаёт git tag, если репозиторий чистый
# либо вручную правка "version" в package.json
```

После publish пользователи фиксируют версию в конфиге, например: `mcp-swtr@1.0.1`.

---

## Публикация (ручная)

```bash
cd npx-version
npm install
npm run lint          # по процессу команды
npm run format:check
npm publish
```

Скрипт **`prepublishOnly`** в `package.json` автоматически выполнит **`npm run build`** непосредственно перед upload — отдельно `build` можно не вызывать, но для проверки `dist/` его лучше запустить заранее.

Явный registry (если не задан в `.npmrc` / `publishConfig`):

```bash
npm publish --registry=https://<ваш-корпоративный-registry>/
```

Повторная публикация **той же версии** registry не примет — нужен bump `version`.

### Публикация из CI (эскиз)

```yaml
# пример шага
- working-directory: npx-version
  env:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
  run: |
      echo "//<registry>/:_authToken=${NPM_TOKEN}" >> .npmrc
      echo "registry=https://<registry>/" >> .npmrc
      npm ci
      npm run lint
      npm run format:check
      npm publish --registry=https://<registry>/
```

Теги git и approval gates — по политике вашей команды.

---

## После публикации

1. Сообщить пользователям новую версию: `npx -y mcp-swtr@<version>`.
2. Обновить примеры в [README.md](README.md) (строки с `@1.0.0`), если версия изменилась.
3. Проверить установку с чистой машины / у коллеги:

    ```bash
    npm view mcp-swtr version --registry=https://<registry>/
    npx -y mcp-swtr@<version> --help 2>&1 || true
    ```

Пакет **не содержит** `BASE_URL` / `TOKEN` — их задаёт каждый пользователь в конфиге MCP-клиента.

---

## Откат и исправления

| Ситуация                   | Действие                                                                  |
| -------------------------- | ------------------------------------------------------------------------- |
| Опубликован битый tarball  | Bump patch-версии, исправить код, `npm publish` снова                     |
| Нужно скрыть версию        | `npm deprecate mcp-swtr@1.0.0 "причина"` (версия остаётся в registry)     |
| Снять с deprecate          | `npm undeprecate mcp-swtr@1.0.0`                                          |
| Удалить версию из registry | Только если политика registry разрешает `npm unpublish` (часто запрещено) |

---

## Частые ошибки

| Ошибка                                     | Причина                          | Решение                                                |
| ------------------------------------------ | -------------------------------- | ------------------------------------------------------ |
| `403 Forbidden` / `401`                    | Нет прав или протух токен        | `npm whoami`, перевыпуск токена, роль publish          |
| `ENEEDAUTH`                                | Нет `.npmrc` / `NPM_TOKEN`       | Настроить `.npmrc` по [.npmrc.example](.npmrc.example) |
| `403 Package name too similar`             | Имя занято в registry            | Согласовать scope с админами registry                  |
| `You cannot publish over the same version` | Версия уже есть                  | Увеличить `version` в `package.json`                   |
| Пустой / старый `dist`                     | Сборка не прошла                 | `npm run build`, смотреть ошибки `tsc`                 |
| В tarball нет `LICENSE`                    | Файл не создан                   | Добавить `LICENSE` в `npx-version/`                    |
| Клиенты: 404 при `npx`                     | Пакет не в том registry / версия | Проверить `npm view`, URL registry у пользователей     |

---

## Чеклист релиза

- [ ] `publishConfig.registry` — боевой URL
- [ ] `LICENSE` присутствует
- [ ] `version` увеличена
- [ ] `npm install`, `npm run lint`, `npm run format:check`
- [ ] `npm run build` без ошибок
- [ ] `npm pack --dry-run` — ожидаемые файлы
- [ ] Локально проверен `npx -y file:.` или MCP с `file:`
- [ ] `npm publish` успешен
- [ ] `npm view mcp-swtr version` на целевом registry
- [ ] Пользователям сообщена новая версия для `mcp.json` / OpenCode / Roo

---

## Связанные файлы

| Файл                             | Назначение                                         |
| -------------------------------- | -------------------------------------------------- |
| [package.json](package.json)     | версия, `files`, `prepublishOnly`, `publishConfig` |
| [.npmrc.example](.npmrc.example) | шаблон registry и токена                           |
| [tsconfig.json](tsconfig.json)   | сборка в `dist/`                                   |
| [README.md](README.md)           | подключение MCP для конечных пользователей         |
