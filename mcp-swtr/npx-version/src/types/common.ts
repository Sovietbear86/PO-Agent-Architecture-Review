/**
 * Общие типы входных данных MCP-инструментов и доменных функций.
 * @module types/common
 */

/**
 * Пагинация списков (нумерация страниц с нуля).
 */
export interface PageInput {
    /** Номер страницы, начиная с 0 */
    page?: number;
    /** Количество элементов на странице */
    size?: number;
}

/**
 * Пара «свойство — значение — оператор» для фильтрации (TQL-подобные запросы).
 */
export interface OperatorPair {
    /** Имя свойства или атрибута */
    property: string;
    /** Значение для сравнения */
    value: string;
    /** Оператор сравнения (например `like`, `eq`) */
    operator: string;
}

/**
 * Фильтр по свойствам: группы условий И и/или ИЛИ.
 * Алиасы `or_` / `and_` совместимы с Python pydantic-моделью.
 */
export interface PropertiesFilter {
    /** Условия, объединяемые через ИЛИ */
    or?: OperatorPair[] | unknown[];
    /** Условия, объединяемые через И */
    and?: OperatorPair[] | unknown[];
    /** Алиас поля `or` (Python) */
    or_?: unknown[];
    /** Алиас поля `and` (Python) */
    and_?: unknown[];
}

/**
 * Контент wiki/описания в формате ProseMirror-подобного JSON (`type` + `content`).
 */
export interface PageContentInput {
    /** Корневой тип документа (по умолчанию `doc`) */
    type?: string;
    /** Массив узлов содержимого */
    content?: unknown[];
}

/**
 * Приоритет задачи при создании юнита.
 */
export type UnitPriority = "blocker" | "critical" | "major" | "minor" | "trivial";
