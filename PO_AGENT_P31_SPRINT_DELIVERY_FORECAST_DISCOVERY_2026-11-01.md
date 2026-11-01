# P3.1 — Sprint Delivery Forecast / Predictability: discovery и контракт (01.11.2026)

## Цель
Устранить бесполезное постоянное «н/д» на вкладке «Спринты», **не заменяя исторический predictability придуманной оценкой**. Добавить отдельно проверяемый прогноз выполнения спринта, построенный на реальных датах, закрытиях, throughput, WIP и истории прошлых спринтов. Пилот: `DMS-SPRNT-5`.

## Зафиксированные факты из текущего кода
- Реальный экран: `po-agent-platform-v2/frontend/src/recovery/Pages.tsx` около 516–554; шесть запросов (health/velocity/throughput/wip/predictability/risks); без числового `predictability` / `predictability_percent` показывает «н/д» и причину «AS21 не отдаёт committed baseline на старт спринта».
- `frontend/src/components/SprintMetrics.tsx` содержит отдельный прежний компонент, где `completed/planned*100` вычисляется из переданных метрик — **не считать его доказательством корректной реализованной метрики**.
- `task-api/src/s21_team_performance/skills/sprint_health.py` в старом коде встречается `len(completed_tasks)*3.0` как synthetic committed effort и расчёт predictability из него — потенциальный **fake-metric hazard**. Перед использованием проверить, достижим ли этот код из текущего живого V4/UI; никакие допущения про 3 story points не использовать для нового показателя.
- `po-agent-platform-v2/src/po_agent/sprint/intelligence.py` содержит `predict_velocity` по истории — сначала проверить, реально ли это вызывается и источниково подтверждена история.

## Семантика
1. **Committed Predictability** = историческая доля выполненного объёма, обещанного на старте спринта. Нельзя вычислять без зафиксированного baseline на дату старта. Отображать `Н/Д — нет достоверного baseline`, а не 0%/100%.
2. **Delivery Forecast** = отдельная оценка вероятного завершения текущего scope к `sprint_end` по наблюдаемым завершениям/скорости. Она может быть рассчитана при отсутствующем committed baseline, если достаточно наблюдений.
3. **Throughput** = фактическое число закрытий за подтверждённый период; закрытие должно иметь проверенный `resolved_at/closed_at` или достоверное событие перехода статуса. **WIP**, а не WHIP — число задач в работе на дату, явно определить набор статусов и источников.
4. Отчёт включает `source`, `source_updated_at`, `as_of`, `scope_definition`, `sprint_start/end`, `elapsed_workdays`, `remaining_workdays`, `closed_count`, `open_count`, `throughput_rate`, `method`, `forecast_completion_date`, `forecast_closed_by_end`, `confidence_state`, `incomplete_reasons`. Вся арифметика повторима. **Не генерировать фиктивные certainty %**.

## MVP расчёта (только после source validation)
- `elapsed_workdays` — фактические рабочие дни от старта до as_of, календарь явно указан.
- `observed_rate = closed_in_sprint_period / elapsed_workdays` если есть подтверждённые closure timestamps и не меньше согласованного объёма наблюдений.
- `remaining = count(current scoped tasks not resolved)`.
- `ETA_workdays = remaining / observed_rate` при `observed_rate > 0`; иначе `insufficient_evidence`.
- `forecast_completed_by_end = min(current_scope_total, closed_so_far + observed_rate * remaining_workdays)`. Прогноз не является committed predictability, не обещает фактический результат и не сохраняется как «fact».
- При доступной истории 3–5 сравнимых завершённых спринтов можно показывать низкую/базовую/высокую скорость, но **только** с явными интервалами и источниками. Если исторические даты/трудозатраты неполные — не создавать ложную точность.
- Разделять «scope на старте», «scope сейчас», «добавлено», «удалено». Когда нет event/snapshot history — `scope_churn_unknown`; текущий scope не выдавать за committed scope.

## Источники и проверка DMS-SPRNT-5
Первый шаг — независимый read-only инвентаризационный A/B: найти канонический sprint ID, start/end, timezone, membership, историю закрытий задач и предыдущих спринтов. Определить, что AS21 реально отдаёт: task.created_at, updated_at, resolved_at, transition history, story points, sprint membership history. Не считать `updated_at` эквивалентом закрытия. По `DMS-SPRNT-5` прежние датированные snapshots 18/36 → 18/35 — это **не** текущая цифра, нужен свежий источник и timestamp. Историю для backtest не синтезировать из текущего состояния.

## Архитектура без изменения Core V4
- Отдельный deterministic plugin `sprint.delivery_forecast` с `source_mode=REAL_AS21`, read-only adapter/Task API boundaries и bounded pagination, строгими лимитами.
- Только данные из разрешённого sprint+project scope, не tenant-wide; scoped joins; корректные неуспешные статусы `SOURCE_UNAVAILABLE`, `INSUFFICIENT_EVIDENCE`, `PARTIAL`.
- UI: новая карточка «Прогноз завершения» рядом с исторической «Predictability: н/д». Чёткая подпись методологии, времени источника, количества задач, тренда и сценариев, с разными provenance для факта и оценки; без raw service JSON.
- Начальная реализация без LLM-расчётов; LLM разрешён только для объяснения уже вычисленного детерминированного результата.

## Разбивка
**P31-D0** (текущий gate): source/implementation discovery, независимый bounded AS21 oracle и спецификация полей. Отчёт: таблица `field | source | available | completeness | sample bounds`; список достижимых code paths и fake-metric risks. **Без изменений кода**.
**P31-D1**: после принятия D0 — deterministic forecasting module+tests, минимум 3 исторических спринта если доступны.
**P31-D2**: V4 plugin binding/capability + источник/пагинация/fail closed.
**P31-D3**: UI-карточка и объяснение; старый predictability не подменять.
**P31-D4**: A/B oracle + backtest на прошлых спринтах + браузер + full regression + Frozen Core V4 6/6.
**P31-D5**: после QA GREEN — sanitized selective transfer to Public, отдельный PR.

## DoD и анти-критерии
- 100% проверяемость чисел по разрешённому source; ни одного `len(tasks)*3` под видом story points.
- Полный backtest без data leakage из будущего; каждое наблюдение привязано к дате.
- Не выводить «прогноз 100%» на основании отсутствия данных.
- LLM 429/AS21 timeout не превращаются в ноль; data freshness и provenance видимы.
- Core 6/6 frozen, V4 + Task API + frontend/browser + AS21 A/B full GREEN.
