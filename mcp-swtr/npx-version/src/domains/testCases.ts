/**
 * Домен тест-кейсов, шагов, тест-циклов и TMS-плагина.
 * @module domains/testCases
 */

import type { SwtrClient } from "../api/client.js";
import {
    paragraphFormattedText,
    propertiesFilterToApi,
    safePageContentJson,
    type PageContentInput
} from "./helpers.js";
import type {
    CreateTestArtifactInput,
    CreateTestCaseStepInput,
    GetTestCasesInTestCycleInput,
    GetTestCasesInput,
    LinkTestCaseToTestCycleInput,
    SearchTestCasesInput,
    UpdateTestCaseDataInput,
    UpdateTestCaseParametersInput
} from "../types/testCases.js";

/**
 * Преобразует `precondition` в JSON-строку, если передан объект контента.
 * @param attrs - Атрибуты создания тест-кейса
 */
function formatTestCaseAttributes(attrs: Record<string, unknown>): Record<string, unknown> {
    const out = { ...attrs };
    if (out.precondition && typeof out.precondition === "object") {
        out.precondition = safePageContentJson(out.precondition as PageContentInput);
    }
    return out;
}

/**
 * Для шагов в `test_step.testStepList` оборачивает plain `formattedText` в doc JSON.
 * @param attrs - Атрибуты patch шага
 */
function formatStepListAttributes(attrs: Record<string, unknown>): Record<string, unknown> {
    const out = JSON.parse(JSON.stringify(attrs)) as Record<string, unknown>;
    const testStep = out.test_step as { testStepList?: Array<Record<string, unknown>> } | undefined;
    if (testStep?.testStepList) {
        for (const item of testStep.testStepList) {
            for (const key of ["stepResult", "stepDescription", "stepData"] as const) {
                const step = item[key] as { formattedText?: string } | undefined;
                if (step?.formattedText && typeof step.formattedText === "string") {
                    step.formattedText = paragraphFormattedText(step.formattedText);
                }
            }
        }
    }
    return out;
}

/**
 * Поиск тест-кейсов в папке иерархии TMS.
 * @param client - HTTP-клиент
 * @param input - Папка, фильтры, атрибуты, сортировка
 */
export async function searchTestCases(
    client: SwtrClient,
    input: SearchTestCasesInput
): Promise<string> {
    return client.post(
        `/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/hierarchy/${input.folder}/units`,
        {
            filters: {
                attributes: propertiesFilterToApi(input.filters.attributes),
                properties: propertiesFilterToApi(input.filters.properties)
            },
            attributes: input.attributes,
            page: { page: input.page ?? 0, size: input.size ?? 25 },
            sort: input.sort
        }
    );
}

/**
 * Корневые каталоги тест-кейсов пространства.
 * @param client - HTTP-клиент
 * @param code - Код пространства
 */
export async function getTestCaseFolders(client: SwtrClient, code: string): Promise<string> {
    return client.post("/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/root", {
        type: "TEST_CASE",
        spaceId: { code }
    });
}

/**
 * Чтение тест-кейса (тот же эндпоинт, что и unit v2).
 * @param client - HTTP-клиент
 * @param code - Код тест-кейса
 */
export async function readTestCase(client: SwtrClient, code: string): Promise<string> {
    return client.get(`/rest/api/unit/v2/${code}`);
}

/**
 * Создание тест-кейса.
 * @param client - HTTP-клиент
 * @param input - Summary, пространство, атрибуты
 */
export async function createTestCase(
    client: SwtrClient,
    input: CreateTestArtifactInput
): Promise<string> {
    const attrs = formatTestCaseAttributes(input.attributes);
    return client.post(`/rest/api/unit/v2/${input.suit ?? "test_case"}/create`, {
        summary: input.summary,
        description: input.description ? safePageContentJson(input.description) : null,
        code: input.code,
        space: input.space,
        suit: input.suit ?? "test_case",
        attributes: attrs
    });
}

/**
 * Обновление шагов тест-кейса (patch атрибутов).
 * @param client - HTTP-клиент
 * @param input - Код кейса и атрибуты с шагами
 */
export async function createTestCaseStep(
    client: SwtrClient,
    input: CreateTestCaseStepInput
): Promise<string> {
    const attrs = formatStepListAttributes(input.attributes);
    return client.patch(`/rest/api/unit/v2/update/${input.code}`, { attributes: attrs });
}

/**
 * Запись тестовых данных кейса.
 * @param client - HTTP-клиент
 * @param input - Код и массив `data`
 */
export async function updateTestCaseData(
    client: SwtrClient,
    input: UpdateTestCaseDataInput
): Promise<string> {
    return client.post(
        `/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/test_case/${input.code}/test_data`,
        { data: input.data }
    );
}

/**
 * Обновление параметров кейса.
 * @param client - HTTP-клиент
 * @param input - Код и массив `parameters`
 */
export async function updateTestCaseParameters(
    client: SwtrClient,
    input: UpdateTestCaseParametersInput
): Promise<string> {
    return client.patch(
        `/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/test_case/${input.code}/parameters`,
        { parameters: input.parameters }
    );
}

/**
 * Метаданные параметров шагов тест-кейса.
 * @param client - HTTP-клиент
 * @param code - Код тест-кейса
 */
export async function getStepInfoParameters(client: SwtrClient, code: string): Promise<string> {
    return client.get(
        `/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/test_case/${code}/test_case_step_info`
    );
}

/**
 * Создание тест-цикла.
 * @param client - HTTP-клиент
 * @param input - Поля артефакта с suit `test_cycle`
 */
export async function createTestCycle(
    client: SwtrClient,
    input: CreateTestArtifactInput
): Promise<string> {
    return client.post("/rest/api/unit/v2/test_cycle/create", {
        summary: input.summary,
        description: input.description ? safePageContentJson(input.description) : null,
        code: input.code,
        space: input.space,
        suit: input.suit ?? "test_cycle",
        attributes: input.attributes
    });
}

/**
 * Список тест-кейсов в корневой папке пространства.
 * @param client - HTTP-клиент
 * @param input - Пространство, атрибуты, пагинация
 */
export async function getTestCases(client: SwtrClient, input: GetTestCasesInput): Promise<string> {
    return client.post("/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/root/units", {
        getRootFolderRq: {
            type: "TEST_CASE",
            spaceId: { code: input.space }
        },
        unitFilters: {
            attributes: [
                input.attributes ?? [
                    "test_case_status",
                    "priority",
                    "automated",
                    "estimate",
                    "label",
                    "owner",
                    "precondition",
                    "test_level",
                    "test_type",
                    "type_of_testing",
                    "component_code",
                    "product_code",
                    "folder"
                ]
            ] as [string[]],
            page: { page: input.page ?? 0, size: input.size ?? 25 }
        }
    });
}

/**
 * Тест-кейсы, включённые в тест-цикл.
 * @param client - HTTP-клиент
 * @param input - Код цикла и пагинация
 */
export async function getTestCasesInTestCycle(
    client: SwtrClient,
    input: GetTestCasesInTestCycleInput
): Promise<string> {
    return client.post(
        "/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/link/test_cycle/test_cases",
        {
            unitId: { code: input.code },
            unitFilters: {
                attributes: input.attributes ?? ["test_case_status"],
                page: { page: input.page ?? 0, size: input.size ?? 25 }
            }
        }
    );
}

/**
 * Привязка тест-кейсов к тест-циклу.
 * @param client - HTTP-клиент
 * @param input - Источник (цикл), назначения, тип связи
 */
export async function linkTestCaseToTestCycle(
    client: SwtrClient,
    input: LinkTestCaseToTestCycleInput
): Promise<string> {
    return client.post("/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/link", {
        source: input.source,
        destinations: input.destinations,
        type: input.link_type
    });
}
