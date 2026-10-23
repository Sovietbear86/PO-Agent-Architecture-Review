/**
 * HTTP-клиент SWTR REST API (native fetch, Bearer, таймаут 10 с).
 * @module api/client
 */

import type { SwtrConfig } from "../config.js";
import { getConfig } from "../config.js";
import { textFromResponse } from "./format.js";

/** Таймаут одного HTTP-запроса, мс */
const TIMEOUT_MS = 30_000;

/**
 * Обёртка над REST API SWTR: авторизация, базовый URL, JSON-тело.
 */
export class SwtrClient {
    /** Параметры подключения (из env или переданные в конструктор) */
    private readonly config: SwtrConfig;

    /**
     * @param config - Явная конфигурация; если не передана — {@link getConfig}
     */
    constructor(config?: SwtrConfig) {
        this.config = config ?? getConfig();
    }

    /** Заголовки по умолчанию для всех запросов */
    private headers(): Record<string, string> {
        return {
            Authorization: `Bearer ${this.config.token}`,
            "Content-Type": "application/json",
            Accept: "application/json",
            Cookie: "api_swtr_as21=true"
        };
    }

    /**
     * Собирает абсолютный URL из базы и пути.
     * @param path - Путь вида `/rest/api/...`
     */
    private url(path: string): string {
        return `${this.config.baseUrl}${path}`;
    }

    /**
     * Низкоуровневый запрос с обработкой сетевых ошибок и таймаута.
     * @param method - HTTP-метод
     * @param path - Путь API
     * @param body - Тело запроса (сериализуется в JSON)
     */
    private async request(method: string, path: string, body?: unknown): Promise<Response> {
        try {
            return await fetch(this.url(path), {
                method,
                headers: this.headers(),
                signal: AbortSignal.timeout(TIMEOUT_MS),
                body: body !== undefined ? JSON.stringify(body) : undefined
            });
        } catch (err) {
            // Преобразуем сетевые ошибки и таймаут в читаемое сообщение
            // вместо того чтобы бросать исключение, которое может уронить процесс
            const isTimeout = err instanceof Error && err.name === "TimeoutError";
            const message = isTimeout
                ? `Request timed out after ${TIMEOUT_MS}ms: ${method} ${path}`
                : `Network error: ${method} ${path} — ${err instanceof Error ? err.message : String(err)}`;
            // Возвращаем псевдо-Response с текстом ошибки
            return new Response(JSON.stringify({ error: message }), {
                status: 0,
                headers: { "Content-Type": "application/json" }
            });
        }
    }

    /**
     * GET с разбором JSON-ответа.
     * @param path - Путь API
     */
    async get(path: string): Promise<string> {
        return textFromResponse(await this.request("GET", path));
    }

    /**
     * POST с разбором JSON-ответа.
     * @param path - Путь API
     * @param payload - Тело запроса
     */
    async post(path: string, payload: unknown): Promise<string> {
        return textFromResponse(await this.request("POST", path, payload));
    }

    /**
     * POST без преобразования тела ответа (сырой `Response`).
     * @param path - Путь API
     * @param payload - Тело запроса
     */
    async postRaw(path: string, payload: unknown): Promise<Response> {
        return this.request("POST", path, payload);
    }

    /**
     * PATCH с разбором JSON-ответа.
     * @param path - Путь API
     * @param payload - Тело запроса
     */
    async patch(path: string, payload: unknown): Promise<string> {
        return textFromResponse(await this.request("PATCH", path, payload));
    }

    /**
     * DELETE с разбором JSON-ответа.
     * @param path - Путь API
     */
    async delete(path: string): Promise<string> {
        return textFromResponse(await this.request("DELETE", path));
    }

    /**
     * POST: возвращает сырой текст ответа без JSON re-format
     * (некоторые эндпоинты совпадают с Python `.text`).
     * @param path - Путь API
     * @param payload - Тело запроса
     */
    async postText(path: string, payload: unknown): Promise<string> {
        const res = await this.request("POST", path, payload);
        return res.text();
    }
}
