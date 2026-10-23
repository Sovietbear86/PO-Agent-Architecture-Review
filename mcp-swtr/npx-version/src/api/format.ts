/**
 * Форматирование JSON-ответов API: безопасная сериализация и разбор HTTP-тела.
 * @module api/format
 */

/**
 * Рекурсивно клонирует объект, заменяя циклические ссылки на маркер `[Circular Reference]`.
 * @param obj - Значение для обхода
 * @param seen - Множество уже посещённых объектов (внутренний стек)
 * @returns Копия без циклов, пригодная для `JSON.stringify`
 */
export function safeFormatJson(obj: unknown, seen: Set<object> = new Set()): unknown {
    if (obj === null || obj === undefined) return obj;
    if (typeof obj === "string" || typeof obj === "number" || typeof obj === "boolean") {
        return obj;
    }
    if (typeof obj !== "object") return String(obj);
    if (seen.has(obj as object)) return "[Circular Reference]";
    seen.add(obj as object);
    try {
        if (Array.isArray(obj)) {
            return obj.map((item) => safeFormatJson(item, seen));
        }
        const record = obj as Record<string, unknown>;
        const out: Record<string, unknown> = {};
        for (const [k, v] of Object.entries(record)) {
            out[k] = safeFormatJson(v, seen);
        }
        return out;
    } finally {
        seen.delete(obj as object);
    }
}

/**
 * Читает тело ответа: если это JSON — возвращает компактную строку через {@link safeFormatJson}.
 * @param res - HTTP-ответ (native fetch Response)
 * @returns Текст или отформатированный JSON
 */
export async function textFromResponse(res: Response): Promise<string> {
    const text = await res.text();
    try {
        const json = JSON.parse(text) as unknown;
        return JSON.stringify(safeFormatJson(json));
    } catch {
        return text;
    }
}
