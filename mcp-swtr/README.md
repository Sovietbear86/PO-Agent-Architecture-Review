# mcp-swtr

MCP сервер для SberWorks Task Tracker

## Локальный запуск и настройка
1. Переименуйте файл [example.env](example.env) в .env
2. В `BASE_URL` укажите адрес сервера
3. В `TOKEN` укажите access token из Bearer 

## Описание

MCP сервер, предоставляющий набор инструментов для взаимодействия с системой SberWorks Task Tracker. Сервер реализует интерфейс MCP (Model Context Protocol) и предоставляет возможность вызова различных API методов через инструменты.

## Особенности

- Поддержка работы с юнитами (задачами, историями и т.п.)
- Работа с тест-кейсами и тест-циклами
- Управление вики-страницами
- Взаимодействие с таймшитом (временными записями)
- Поиск пользователей и других сущностей
- Поддержка TQL фильтрации
- Работа с файлами юнитов (список и скачивание)

## Node / npx (stdio)

Отдельная реализация для Cursor, OpenCode и Roo Code: каталог [npx-version/](npx-version/), документация — [npx-version/README.md](npx-version/README.md).

## Зависимости

- Python 3.11
- fastmcp
- pydantic
- httpx
- nest_asyncio

Установка зависимостей:
```bash
pip install -r requirements.txt
```

## Локальный запуск и настройка

1. Скопируйте файл [example.env](example.env) в `.env`:
   ```bash
   cp example.env .env
   ```

2. Настройте переменные окружения в файле `.env`:
   - `BASE_URL` - адрес сервера SberWorks
   - `TOKEN` - access token из Bearer
   - `PORT` - порт для запуска сервера (по умолчанию 8000)

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Запустите сервер:
   ```bash
   python mcp_server.py
   ```

## Запуск через Docker

Сборка образа:
```bash
docker build -t mcp-swtr .
```

Запуск контейнера:
```bash
docker run -p 8000:8000 \
  -e BASE_URL=https://AS21_INTERNAL_URL_PLACEHOLDER/swtr \
  -e TOKEN=your_token_here \
  mcp-swtr
```

## Доступные инструменты

### Юниты
- **read_unit** - Получение информации о юните по его коду
- **find_units** - Поиск юнитов по заданным пространствам
- **get_tql_properties** - Получение информации об атрибутах для фильтрации с помощью TQL
- **get_unit_types_by_space** - Получение типов юнитов по заданному пространству
- **create_unit** - Создание нового юнита
- **update_unit** - Редактирование юнита
- **create_unit_link** - Создание связи между юнитами
- **create_unit_comment** - Создание комментария к юниту
- **get_unit_comments** - Получение комментариев юнита
- **search_link_types** - Поиск типов связей между юнитами
- **get_unit_links** - Получение связей между юнитами
- **get_unit_attributes** - Получение информации о списках атрибутов unit
- **get_unit_files** - Получение информации о файлах юнита
- **download_unit_file** - Скачивание файла юнита (возвращает base64)
- **search_versions** - Поиск версий (релизов)
- **search_sprints** - Поиск спринтов

### Вики
- **search_wiki_pages** - Поиск wiki-страниц
- **read_wiki_page** - Чтение wiki-страницы
- **create_wiki_page** - Создание новой wiki-страницы

### Тест-кейсы
- **search_test_cases** - Поиск тест-кейсов
- **get_test_case_folders** - Получить список каталогов тест-кейсов
- **read_test_case** - Получение информации о тест-кейсе
- **create_test_case** - Создание нового тест-кейса
- **create_test_case_step** - Создание шага тест-кейса
- **update_test_case_data** - Создание данных тест-кейса
- **update_test_case_parameters** - Создание параметров тест-кейса
- **get_step_info_parameters** - Получение информации о параметрах шагов тест-кейса
- **create_test_cycle** - Создание нового тест цикла
- **get_test_cases** - Получение списка тест-кейсов
- **get_test_cases_in_test_cycle** - Получение списка тест-кейсов в тест цикле
- **link_test_case_to_test_cycle** - Добавление тест-кейсов в тест цикл

### Таймшит
- **get_work_types** - Получение информации о видах работ списания рабочего времени
- **create_work_log** - Списание времени
- **create_work_log_range** - Списание времени в диапазоне дат (требуется исключать выходные дни)
- **get_work_log** - Получение информации о списании
- **update_work_log** - Изменение списания
- **delete_work_log** - Удаление списания
- **get_work_report** - Получение информации о списаниях рабочего времени
- **get_work_sum** - Сумма списаний рабочего времени по юниту

### Пользователи
- **search_users** - Поиск пользователей

## Структура проекта

- `mcp_server.py` - Основной файл сервера
- `requirements.txt` - Зависимости проекта
- `Dockerfile` - Конфигурация для сборки Docker образа
- `models/` - Модели данных для взаимодействия с API
- `npx-version/` - Node-реализация MCP (stdio, npx)

## Использование

После запуска сервера он будет доступен по адресу `http://localhost:8000` (или указанному порту).

Для использования инструментов необходимо подключить сервер к клиенту, поддерживающему MCP протокол.

## Лицензия

MIT