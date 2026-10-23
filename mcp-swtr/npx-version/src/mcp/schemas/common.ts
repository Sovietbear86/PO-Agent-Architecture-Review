/**
 * Общие Zod-схемы аргументов MCP-инструментов.
 * @module mcp/schemas/common
 */

import { z } from "zod";

/**
 * Поля пагинации для `z.object({ ...pageSizeSchema })`.
 * Ключи: `page`, `size`.
 */
export const pageSizeSchema = {
    page: z.number().int().min(0).optional().describe("Номер страницы (с 0)"),
    size: z.number().int().min(0).optional().describe("Размер страницы")
};

/** Одно условие фильтра: свойство, значение, оператор */
export const operatorPairSchema = z.object({
    property: z.string().describe("Название свойства"),
    value: z.string().describe("Значение"),
    operator: z.string().describe("Оператор (например like)")
});

/**
 * Фильтр по свойствам с ветками `or` и `and`.
 * Соответствует `PropertiesFilter` в `types/common`.
 */
export const propertiesFilterSchema = z
    .object({
        or: z.array(operatorPairSchema).optional().describe("Условия ИЛИ"),
        and: z.array(operatorPairSchema).optional().describe("Условия И")
    })
    .describe("Фильтр по свойствам");

/**
 * Контент wiki-страницы / rich-text описания (ProseMirror-like JSON).
 */
export const pageContentSchema = z
    .object({
        type: z.string().optional().default("doc"),
        content: z.array(z.record(z.unknown())).describe("Содержимое wiki/doc")
    })
    .describe("Контент страницы (ProseMirror-like JSON)");

/** Допустимые приоритеты при создании юнита */
export const prioritySchema = z.enum(["blocker", "critical", "major", "minor", "trivial"]);
