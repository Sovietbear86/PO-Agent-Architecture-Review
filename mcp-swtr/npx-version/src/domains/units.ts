/**
 * Домен юнитов (задачи, связи, комментарии, версии, спринты).
 * @module domains/units
 */

import type { SwtrClient } from "../api/client.js";
import { safeFormatJson } from "../api/format.js";
import { propertiesFilterToApi } from "./helpers.js";
import type { PageInput, PropertiesFilter, UnitPriority } from "../types/common.js";

/**
 * Параметры получения типов юнитов (suit) по пространству.
 */
export interface GetUnitTypesBySpaceInput extends PageInput {
    /** Код пространства; `null` — без фильтра */
    space?: string | null;
}

/**
 * Параметры поиска юнитов (`find_units`).
 */
export interface FindUnitsInput extends PageInput {
    /** Вычисляемые атрибуты в ответе */
    calculatedAttributes?: string[] | null;
    /** Запрашиваемые атрибуты */
    attributes?: string[];
    /** Коды пространств */
    spaces?: string[] | null;
    /** Фильтр по свойствам (TQL) */
    properties: PropertiesFilter;
    /** `false` — урезать поле `unit` в элементах `content` */
    full_info?: boolean;
}

/**
 * Параметры создания юнита.
 */
export interface CreateUnitInput {
    /** Код типа (suit), например `task` */
    suit: string;
    /** Код пространства */
    space: string;
    /** Заголовок */
    summary: string;
    /** Описание (plain или rich) */
    description: string;
    /** Приоритет */
    priority: UnitPriority;
    /** Команда workflow (по умолчанию `NEW`) */
    status?: string;
    /** Дополнительные атрибуты */
    attributes?: Record<string, unknown>;
}

/**
 * Параметры обновления юнита.
 */
export interface UpdateUnitInput {
    /** Код юнита */
    code: string;
    /** Атрибуты для обновления */
    attributes?: Record<string, unknown>;
}

/**
 * Параметры связи двух юнитов.
 */
export interface CreateUnitLinkInput {
    /** Код исходного юнита */
    source: string;
    /** Код целевого юнита */
    destination: string;
    /** Код типа связи */
    link_type: string;
}

/**
 * Параметры комментария к юниту.
 */
export interface CreateUnitCommentInput {
    /** Код юнита */
    unit_code: string;
    /** Текст комментария */
    comment_text: string;
}

/**
 * Параметры списка комментариев юнита.
 */
export interface GetUnitCommentsInput extends PageInput {
    /** Код юнита */
    unit_code: string;
}

/**
 * Параметры поиска типов связей.
 */
export interface SearchLinkTypesInput extends PageInput {
    /** Подстрока в названии типа */
    text_search?: string | null;
}

/**
 * Параметры списка связей юнита.
 */
export interface GetUnitLinksInput extends PageInput {
    /** Код юнита */
    unit_code: string;
    /** Фильтр по типам связи (пусто — все) */
    link_types?: string[];
}

/**
 * Параметры поиска версий (релизов).
 */
export interface SearchVersionsInput extends PageInput {
    /** Текстовый запрос */
    query?: string;
    /** Код пространства */
    space: string;
    /** Включать архивные */
    withArchived?: boolean;
    /** Включать удалённые */
    withDeleted?: boolean;
    /** Вычисляемые атрибуты (зарезервировано API) */
    calculatedAttributes?: string[] | null;
    /** Запрашиваемые атрибуты */
    attributes?: string[];
}

/**
 * Параметры поиска спринтов.
 */
export interface SearchSprintsInput extends PageInput {
    /** Код пространства */
    space?: string | null;
}

/**
 * Чтение одного юнита по коду.
 * @param client - HTTP-клиент
 * @param code - Код юнита
 */
export async function readUnit(client: SwtrClient, code: string): Promise<string> {
    return client.get(`/rest/api/unit/v2/${code}`);
}

/**
 * Типы юнитов (suit) в пространстве.
 * @param client - HTTP-клиент
 * @param input - Пространство и пагинация
 */
export async function getUnitTypesBySpace(
    client: SwtrClient,
    input: GetUnitTypesBySpaceInput
): Promise<string> {
    const payload = {
        filters: { space: input.space ?? [] },
        page: { page: input.page ?? 0, size: input.size ?? 25 }
    };
    return client.postText("/rest/api/suit/v1/find", payload);
}

/**
 * Поиск юнитов по пространствам и свойствам.
 * @param client - HTTP-клиент
 * @param input - Фильтры, атрибуты, режим `full_info`
 */
export async function findUnits(client: SwtrClient, input: FindUnitsInput): Promise<string> {
    const payload = {
        calculatedAttributes: input.calculatedAttributes ?? [],
        attributes: input.attributes ?? [],
        filters: {
            properties: propertiesFilterToApi(input.properties),
            spaces: input.spaces ?? []
        },
        page: { page: input.page ?? 0, size: input.size ?? 25 }
    };
    const res = await client.postRaw("/rest/api/unit/v2/find", payload);
    const text = await res.text();
    if (input.full_info !== false) {
        try {
            const json = JSON.parse(text) as unknown;
            return JSON.stringify(safeFormatJson(json));
        } catch {
            return text;
        }
    }
    try {
        const json = JSON.parse(text) as { content?: Record<string, unknown>[] };
        if (json.content) {
            for (const item of json.content) {
                if (item && typeof item === "object" && "unit" in item) {
                    delete item.unit;
                }
            }
        }
        return JSON.stringify(safeFormatJson(json));
    } catch {
        return text;
    }
}

/**
 * Параметры поиска юнитов по TQL-запросу (`find_units_by_filter`).
 */
export interface FindUnitsByFilterInput extends PageInput {
    /** Вычисляемые атрибуты в ответе */
    calculatedAttributes?: string[] | null;
    /** Запрашиваемые атрибуты */
    attributes?: string[];
    /**
     * TQL-строка фильтрации. Пример:
     * `assigned_to = "Gotskin.D.L" AND status != "DONE"`
     * Доступные поля — см. get_tql_properties.
     */
    query: string;
    /** Часовой пояс для дат (по умолчанию Europe/Moscow) */
    timeZone?: string;
}

/**
 * Поиск юнитов через TQL-запрос (эндпоинт /find/tql).
 * Поддерживает фильтрацию по assigned_to, status, suit и любым другим полям.
 * @param client - HTTP-клиент
 * @param input - TQL-запрос и параметры
 */
export async function findUnitsByFilter(
    client: SwtrClient,
    input: FindUnitsByFilterInput
): Promise<string> {
    const payload = {
        calculatedAttributes: input.calculatedAttributes ?? [],
        attributes: input.attributes ?? [],
        query: input.query,
        timeZone: input.timeZone ?? "Europe/Moscow",
        page: { page: input.page ?? 0, size: input.size ?? 25 }
    };
    return client.post("/rest/api/unit/v3/find/tql", payload);
}

/**
 * Справочник атрибутов для TQL-фильтрации.
 * @param client - HTTP-клиент
 */
export async function getTqlProperties(client: SwtrClient): Promise<string> {
    return client.get("/rest/api/attr/v1/tql/properties");
}

/**
 * Создание юнита заданного suit.
 * @param client - HTTP-клиент
 * @param input - Поля юнита и приоритет
 */
export async function createUnit(client: SwtrClient, input: CreateUnitInput): Promise<string> {
    const attributes = { ...(input.attributes ?? {}) };
    attributes.priority = input.priority;
    attributes.workflow_status = { command: input.status ?? "NEW" };
    return client.post(`/rest/api/unit/v2/${input.suit}/create`, {
        description: input.description,
        summary: input.summary,
        space: input.space,
        attributes
    });
}

/**
 * Обновление юнита.
 * @param client - HTTP-клиент
 * @param input - Код юнита и атрибуты для обновления
 */
export async function updateUnit(client: SwtrClient, input: UpdateUnitInput): Promise<string> {
    return client.patch(`/rest/api/unit/v2/update/${input.code}`, {
        attributes: input.attributes ?? {}
    });
}

/**
 * Создание связи между юнитами.
 * @param client - HTTP-клиент
 * @param input - Источник, назначение, тип связи
 */
export async function createUnitLink(
    client: SwtrClient,
    input: CreateUnitLinkInput
): Promise<string> {
    return client.post("/rest/api/unit/v1/link", {
        source: input.source,
        destination: input.destination,
        type: input.link_type
    });
}

/**
 * Добавление комментария к юниту.
 * @param client - HTTP-клиент
 * @param input - Код юнита и текст
 */
export async function createUnitComment(
    client: SwtrClient,
    input: CreateUnitCommentInput
): Promise<string> {
    return client.post("/rest/api/unit-comment/v1/create", {
        unitCode: input.unit_code,
        commentText: input.comment_text
    });
}

/**
 * Список комментариев юнита.
 * @param client - HTTP-клиент
 * @param input - Код юнита и пагинация
 */
export async function getUnitComments(
    client: SwtrClient,
    input: GetUnitCommentsInput
): Promise<string> {
    return client.post("/rest/api/unit-comment/v1/find", {
        unitCode: input.unit_code,
        pageDtoRq: { page: input.page ?? 0, size: input.size ?? 25 }
    });
}

/**
 * Поиск типов связей по подстроке.
 * @param client - HTTP-клиент
 * @param input - `text_search` и пагинация
 */
export async function searchLinkTypes(
    client: SwtrClient,
    input: SearchLinkTypesInput
): Promise<string> {
    return client.post("/rest/api/unit/v2/link/types", {
        filters: { textSearch: input.text_search },
        page: { page: input.page ?? 0, size: input.size ?? 25 }
    });
}

/**
 * Связи указанного юнита.
 * @param client - HTTP-клиент
 * @param input - Код юнита, типы связей, пагинация
 */
export async function getUnitLinks(client: SwtrClient, input: GetUnitLinksInput): Promise<string> {
    return client.post("/rest/api/unit/v1/link/find", {
        type: input.link_types ?? [],
        unitId: input.unit_code,
        page: {
            page: { page: input.page ?? 0, size: input.size ?? 25 }
        }
    });
}

/**
 * Справочник всех атрибутов unit.
 * @param client - HTTP-клиент
 */
export async function getUnitAttributes(client: SwtrClient): Promise<string> {
    return client.get("/rest/api/attr/v1/findAll");
}

/**
 * Поиск версий (релизов) в пространстве.
 * @param client - HTTP-клиент
 * @param input - Пространство, запрос, флаги архива
 */
export async function searchVersions(
    client: SwtrClient,
    input: SearchVersionsInput
): Promise<string> {
    return client.post("/extension/plugin/v2/rest/api/swtr_task_tracker_plugin/v1/version/find", {
        query: input.query ?? "",
        space: input.space,
        withArchived: input.withArchived ?? false,
        withDeleted: input.withDeleted ?? false,
        page: { page: input.page ?? 0, size: input.size ?? 25 }
    });
}

/**
 * Поиск спринтов scrum-доски.
 * @param client - HTTP-клиент
 * @param input - Пространство и пагинация
 */
export async function searchSprints(
    client: SwtrClient,
    input: SearchSprintsInput
): Promise<string> {
    return client.post("/extension/plugin/v2/rest/api/scrum_board_plugin/v1/sprint/find", {
        space: input.space,
        page: { page: input.page ?? 0, size: input.size ?? 25 }
    });
}
