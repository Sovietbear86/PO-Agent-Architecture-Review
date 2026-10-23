/**
 * Домен wiki-страниц SWTR.
 * @module domains/wiki
 */

import type { SwtrClient } from "../api/client.js";
import { safePageContentJson, type PageContentInput } from "./helpers.js";
import type { PageInput } from "../types/common.js";

/**
 * Параметры поиска wiki-страниц.
 */
export interface SearchWikiPagesInput extends PageInput {
    /** Коды пространств */
    spaces: string[];
    /** Коды связанных юнитов */
    units: string[];
    /** Полнотекстовый запрос */
    text_search?: string | null;
}

/**
 * Параметры создания wiki-страницы.
 */
export interface CreateWikiPageInput {
    /** Код пространства */
    space_code: string;
    /** Заголовок (summary) */
    title: string;
    /** Краткое описание */
    description?: string;
    /** Метки */
    labels?: string[];
    /** Тело страницы (ProseMirror JSON) */
    content: PageContentInput;
}

/**
 * Поиск wiki-страниц по пространствам, юнитам и тексту.
 * @param client - HTTP-клиент
 * @param input - Фильтры и пагинация
 */
export async function searchWikiPages(
    client: SwtrClient,
    input: SearchWikiPagesInput
): Promise<string> {
    return client.post("/extension/plugin/v2/rest/api/swtr_wiki_plugin/v1/wiki/unit/find", {
        filters: {
            spaces: input.spaces ?? [],
            units: input.units ?? [],
            query: input.text_search
        },
        page: { page: input.page ?? 0, size: input.size ?? 25 }
    });
}

/**
 * Чтение wiki-страницы по коду.
 * @param client - HTTP-клиент
 * @param code - Код wiki-юнита
 */
export async function readWikiPage(client: SwtrClient, code: string): Promise<string> {
    return client.get(`/extension/plugin/v2/rest/api/swtr_wiki_plugin/v1/wiki/unit/${code}`);
}

/**
 * Создание wiki-страницы (`wiki_page` suit).
 * @param client - HTTP-клиент
 * @param input - Пространство, заголовок, контент
 */
export async function createWikiPage(
    client: SwtrClient,
    input: CreateWikiPageInput
): Promise<string> {
    const bodyJson = safePageContentJson(input.content);
    return client.post("/rest/api/unit/v2/wiki_page/create", {
        space: input.space_code,
        summary: input.title,
        description: input.description ?? "",
        attributes: {
            label: input.labels ?? [],
            wiki_page_body: bodyJson
        }
    });
}
