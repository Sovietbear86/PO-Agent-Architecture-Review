/**
 * Конфигурация подключения к SWTR API из переменных окружения.
 * @module config
 */

/**
 * Параметры HTTP-клиента SWTR.
 */
export interface SwtrConfig {
    /** Базовый URL API без завершающего слэша */
    baseUrl: string;
    /** Bearer-токен авторизации */
    token: string;
}

/** Кэшированный экземпляр конфигурации (singleton на процесс) */
let cached: SwtrConfig | null = null;

/**
 * Читает `BASE_URL` и `TOKEN` из `process.env`, нормализует URL и кэширует результат.
 * @returns Готовая конфигурация
 * @throws {Error} Если `BASE_URL` или `TOKEN` не заданы
 */
export function getConfig(): SwtrConfig {
    if (cached) return cached;
    const baseUrl = (process.env.BASE_URL ?? "").replace(/\/$/, "");
    const token = process.env.TOKEN ?? "";
    if (!baseUrl || !token) {
        throw new Error(
            "BASE_URL and TOKEN must be set (via MCP client env: Cursor env, OpenCode environment, Roo Code env)"
        );
    }
    cached = { baseUrl, token };
    return cached;
}

/**
 * Возвращает множество имён инструментов, отключённых через `DISABLED_TOOLS`.
 * Формат: через запятую, пробелы игнорируются. Пустая строка → пустое множество.
 */
export function getDisabledTools(): Set<string> {
    const raw = process.env.DISABLED_TOOLS ?? "";
    if (!raw.trim()) return new Set();
    return new Set(raw.split(",").map((s) => s.trim()).filter(Boolean));
}

/**
 * Сбрасывает кэш конфигурации (для тестов).
 */
export function resetConfigForTests(): void {
    cached = null;
}
