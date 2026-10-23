/**
 * Домен пользователей SWTR.
 * @module domains/users
 */

import type { SwtrClient } from "../api/client.js";
import type { PageInput } from "../types/common.js";

/**
 * Параметры поиска пользователей.
 */
export interface SearchUsersInput extends PageInput {
    /** Подстрока для поиска по ФИО / логину */
    text_search?: string | null;
}

/**
 * Поиск пользователей по строке.
 * @param client - HTTP-клиент
 * @param input - Фильтр и пагинация
 * @returns JSON-строка ответа API
 */
export async function searchUsers(client: SwtrClient, input: SearchUsersInput): Promise<string> {
    return client.post("/rest/api/user/v1/search", {
        searchString: input.text_search,
        paging: { page: input.page ?? 0, size: input.size ?? 25 }
    });
}
