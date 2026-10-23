/**
 * Вспомогательные преобразования фильтров и wiki-контента (совместимость с Python MCP).
 * @module domains/helpers
 */

import type { PageContentInput, PropertiesFilter } from "../types/common.js";

export type { PageContentInput, PropertiesFilter };

/**
 * Приводит фильтр свойств к виду API: `or` / `and`, с учётом Python-алиасов `or_` / `and_`.
 * @param filter - Входной фильтр из MCP или pydantic
 * @returns Объект с массивами `or` и `and` (пустые, если не заданы)
 */
export function propertiesFilterToApi(filter: PropertiesFilter): { or: unknown[]; and: unknown[] } {
    return {
        or: filter.or ?? filter.or_ ?? [],
        and: filter.and ?? filter.and_ ?? []
    };
}

/**
 * Сериализует контент страницы в JSON-строку для атрибута `wiki_page_body` и аналогов.
 * @param page - ProseMirror-подобный документ или `null` / `undefined`
 * @returns JSON-строка `{ type, content }` или `null`
 */
export function safePageContentJson(page: PageContentInput | undefined | null): string | null {
    if (!page) return null;
    const type = page.type ?? "doc";
    const content = Array.isArray(page.content) ? page.content : [];
    return JSON.stringify({ type, content });
}

/**
 * Оборачивает plain-text в минимальный doc с одним параграфом (для шагов тест-кейса).
 * @param plain - Простой текст
 * @returns JSON-строка документа
 */
export function paragraphFormattedText(plain: string): string {
    return JSON.stringify({
        type: "doc",
        content: [
            {
                type: "paragraph",
                content: [{ type: "text", text: plain }]
            }
        ]
    });
}
