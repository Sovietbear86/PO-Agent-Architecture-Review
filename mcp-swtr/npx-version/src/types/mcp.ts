/**
 * Типы ответов MCP-сервера.
 * @module types/mcp
 */

/** Текстовый фрагмент контента инструмента MCP */
export interface McpTextContent {
    /** Всегда `text` для текстовых ответов */
    type: "text";
    /** Тело ответа (обычно JSON-строка от API SWTR) */
    text: string;
}

/** Стандартный результат MCP-инструмента с одним текстовым блоком */
export interface McpTextResult {
    /** Массив из одного текстового элемента */
    content: [McpTextContent];
    /** Совместимость с расширяемым `CallToolResult` из SDK */
    [x: string]: unknown;
}
