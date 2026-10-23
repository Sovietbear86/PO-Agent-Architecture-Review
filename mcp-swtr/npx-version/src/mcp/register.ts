/**
 * Регистрация всех MCP-инструментов SWTR на {@link McpServer}.
 * Схемы аргументов — Zod; описания инструментов — на русском для клиента.
 * @module mcp/register
 */

import type { McpServer, ToolCallback } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { AnySchema, ZodRawShapeCompat } from "@modelcontextprotocol/sdk/server/zod-compat.js";
import type { ToolAnnotations } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { SwtrClient } from "../api/client.js";
import * as units from "../domains/units.js";
import * as wiki from "../domains/wiki.js";
import * as testCases from "../domains/testCases.js";
import * as timesheet from "../domains/timesheet.js";
import * as users from "../domains/users.js";
import type { McpTextResult } from "../types/mcp.js";
import { getDisabledTools } from "../config.js";
import {
    pageContentSchema,
    pageSizeSchema,
    prioritySchema,
    propertiesFilterSchema
} from "./schemas/common.js";

/**
 * Оборачивает строку ответа API в формат контента MCP.
 * @param text - JSON или plain text от доменной функции
 */
function textResult(text: string): McpTextResult {
    return { content: [{ type: "text", text }] };
}

/**
 * Новый HTTP-клиент на каждый вызов инструмента (конфиг из env).
 */
function client(): SwtrClient {
    return new SwtrClient();
}

/**
 * Регистрирует полный набор инструментов: units, wiki, TMS, timesheet, users.
 * @param server - Экземпляр MCP-сервера из {@link createServer}
 */
export function registerAllTools(server: McpServer): void {
    const disabled = getDisabledTools();
    const register = <
        OutputArgs extends ZodRawShapeCompat | AnySchema,
        InputArgs extends undefined | ZodRawShapeCompat | AnySchema = undefined
    >(
        name: string,
        config: {
            title?: string;
            description?: string;
            inputSchema?: InputArgs;
            outputSchema?: OutputArgs;
            annotations?: ToolAnnotations;
            _meta?: Record<string, unknown>;
        },
        cb: ToolCallback<InputArgs>
    ): void => {
        if (disabled.has(name)) return;
        server.registerTool(name, config, cb);
    };

    register(
        "read_unit",
        {
            description: "Чтение юнита",
            inputSchema: z.object({ code: z.string().describe("Код юнита") })
        },
        async ({ code }) => textResult(await units.readUnit(client(), code))
    );

    register(
        "get_unit_types_by_space",
        {
            description: "Получение типов юнитов по заданному пространству",
            inputSchema: z.object({
                space: z.string().nullable().optional().describe("Код пространства"),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await units.getUnitTypesBySpace(client(), input))
    );

    register(
        "find_units",
        {
            description: "Поиск юнитов по заданным пространствам",
            inputSchema: z.object({
                calculatedAttributes: z.array(z.string()).nullable().optional(),
                attributes: z.array(z.string()).optional(),
                spaces: z.array(z.string()).nullable().optional(),
                properties: propertiesFilterSchema,
                full_info: z.boolean().optional().default(true),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await units.findUnits(client(), input))
    );

    register(
        "find_units_by_filter",
        {
            description:
                "Поиск юнитов по TQL-фильтру. Используй get_tql_properties для списка доступных полей. " +
                'Пример query: assigned_to = "Gotskin.D.L" AND status != "DONE" AND status != "CLOSED"',
            inputSchema: z.object({
                query: z
                    .string()
                    .describe(
                        "TQL-строка фильтрации. Строки в двойных кавычках, операторы (AND, OR, !=, =) в верхнем регистре. " +
                            'Пример: assigned_to = "Gotskin.D.L" AND status != "DONE"'
                    ),
                calculatedAttributes: z.array(z.string()).nullable().optional(),
                attributes: z.array(z.string()).optional(),
                timeZone: z.string().optional().default("Europe/Moscow"),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await units.findUnitsByFilter(client(), input))
    );

    register(
        "get_tql_properties",
        {
            description: "Получение информации об атрибутах для фильтрации c tql",
            inputSchema: z.object({})
        },
        async () => textResult(await units.getTqlProperties(client()))
    );

    register(
        "create_unit",
        {
            description: "Создание нового юнита",
            inputSchema: z.object({
                suit: z.string(),
                space: z.string(),
                summary: z.string(),
                description: z.string(),
                priority: prioritySchema,
                status: z.string().optional().default("NEW"),
                attributes: z.record(z.unknown()).optional().default({})
            })
        },
        async (input) => textResult(await units.createUnit(client(), input))
    );

    register(
        "update_unit",
        {
            description: "Редактирование юнита",
            inputSchema: z.object({
                code: z.string().describe("Код юнита"),
                attributes: z.record(z.unknown()).optional().default({})
            })
        },
        async (input) => textResult(await units.updateUnit(client(), input))
    );

    register(
        "create_unit_link",
        {
            description: "Создание связи между юнитами",
            inputSchema: z.object({
                source: z.string(),
                destination: z.string(),
                link_type: z.string()
            })
        },
        async (input) => textResult(await units.createUnitLink(client(), input))
    );

    register(
        "create_unit_comment",
        {
            description: "Создание комментария к юниту",
            inputSchema: z.object({
                unit_code: z.string(),
                comment_text: z.string()
            })
        },
        async (input) => textResult(await units.createUnitComment(client(), input))
    );

    register(
        "get_unit_comments",
        {
            description: "Получение комментариев юнита",
            inputSchema: z.object({
                unit_code: z.string(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await units.getUnitComments(client(), input))
    );

    register(
        "search_link_types",
        {
            description: "Поиск типов связей между юнитами",
            inputSchema: z.object({
                text_search: z.string().nullable().optional(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await units.searchLinkTypes(client(), input))
    );

    register(
        "get_unit_links",
        {
            description: "Получение связей между юнитами",
            inputSchema: z.object({
                unit_code: z.string(),
                link_types: z.array(z.string()).optional().default([]),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await units.getUnitLinks(client(), input))
    );

    register(
        "get_unit_attributes",
        {
            description: "Получение информации о списках атрибутов unit",
            inputSchema: z.object({})
        },
        async () => textResult(await units.getUnitAttributes(client()))
    );

    register(
        "search_users",
        {
            description: "Поиск пользователей",
            inputSchema: z.object({
                text_search: z.string().nullable().optional(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await users.searchUsers(client(), input))
    );

    register(
        "search_versions",
        {
            description: "Поиск версий (релизов)",
            inputSchema: z.object({
                query: z.string().optional().default(""),
                space: z.string(),
                withArchived: z.boolean().optional(),
                withDeleted: z.boolean().optional(),
                calculatedAttributes: z.array(z.string()).nullable().optional(),
                attributes: z.array(z.string()).optional(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await units.searchVersions(client(), input))
    );

    register(
        "search_sprints",
        {
            description: "Поиск спринтов",
            inputSchema: z.object({
                space: z.string().nullable().optional(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await units.searchSprints(client(), input))
    );

    register(
        "search_wiki_pages",
        {
            description: "Поиск wiki-страниц",
            inputSchema: z.object({
                spaces: z.array(z.string()),
                units: z.array(z.string()),
                text_search: z.string().nullable().optional(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await wiki.searchWikiPages(client(), input))
    );

    register(
        "read_wiki_page",
        {
            description: "Чтение wiki-страницы",
            inputSchema: z.object({ code: z.string().describe("Код страницы") })
        },
        async ({ code }) => textResult(await wiki.readWikiPage(client(), code))
    );

    register(
        "create_wiki_page",
        {
            description: "Создание новой wiki-страницы",
            inputSchema: z.object({
                space_code: z.string(),
                title: z.string(),
                description: z.string().optional().default(""),
                labels: z.array(z.string()).optional().default([]),
                content: pageContentSchema
            })
        },
        async (input) => textResult(await wiki.createWikiPage(client(), input))
    );

    register(
        "search_test_cases",
        {
            description: "Поиск тест-кейсов",
            inputSchema: z.object({
                folder: z.string(),
                attributes: z.array(z.string()),
                filters: z.object({
                    attributes: propertiesFilterSchema,
                    properties: propertiesFilterSchema
                }),
                sort: z
                    .object({
                        direction: z.string().optional(),
                        attribute: z.array(z.string()).optional()
                    })
                    .nullable()
                    .optional(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await testCases.searchTestCases(client(), input))
    );

    register(
        "get_test_case_folders",
        {
            description: "Получить список каталогов тест-кейсов",
            inputSchema: z.object({ code: z.string().describe("Код пространства") })
        },
        async ({ code }) => textResult(await testCases.getTestCaseFolders(client(), code))
    );

    register(
        "read_test_case",
        {
            description: "Получение информации о тест-кейсе",
            inputSchema: z.object({ code: z.string() })
        },
        async ({ code }) => textResult(await testCases.readTestCase(client(), code))
    );

    register(
        "create_test_case",
        {
            description: "Создание нового тест-кейса",
            inputSchema: z.object({
                summary: z.string(),
                description: pageContentSchema.nullable().optional(),
                code: z.string().nullable().optional(),
                space: z.string(),
                suit: z.string().optional().default("test_case"),
                attributes: z.record(z.unknown())
            })
        },
        async (input) => textResult(await testCases.createTestCase(client(), input))
    );

    register(
        "create_test_case_step",
        {
            description: "Создание шага тест-кейса",
            inputSchema: z.object({
                code: z.string(),
                attributes: z.record(z.unknown())
            })
        },
        async (input) => textResult(await testCases.createTestCaseStep(client(), input))
    );

    register(
        "update_test_case_data",
        {
            description: "Создание данных тест-кейса",
            inputSchema: z.object({
                code: z.string().nullable().optional(),
                data: z.array(z.record(z.unknown()))
            })
        },
        async (input) => textResult(await testCases.updateTestCaseData(client(), input))
    );

    register(
        "update_test_case_parameters",
        {
            description: "Создание параметров тест-кейса",
            inputSchema: z.object({
                code: z.string().nullable().optional(),
                parameters: z.array(z.record(z.unknown()))
            })
        },
        async (input) => textResult(await testCases.updateTestCaseParameters(client(), input))
    );

    register(
        "get_step_info_parameters",
        {
            description: "Получение информации о параметрах шагов тест-кейса",
            inputSchema: z.object({ code: z.string() })
        },
        async ({ code }) => textResult(await testCases.getStepInfoParameters(client(), code))
    );

    register(
        "create_test_cycle",
        {
            description: "Создание нового тест цикла",
            inputSchema: z.object({
                summary: z.string(),
                description: pageContentSchema.nullable().optional(),
                code: z.string().nullable().optional(),
                space: z.string(),
                suit: z.string().optional().default("test_cycle"),
                attributes: z.record(z.unknown())
            })
        },
        async (input) => textResult(await testCases.createTestCycle(client(), input))
    );

    register(
        "get_test_cases",
        {
            description: "Получение списка тест-кейсов",
            inputSchema: z.object({
                space: z.string(),
                attributes: z.array(z.string()).optional(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await testCases.getTestCases(client(), input))
    );

    register(
        "get_test_cases_in_test_cycle",
        {
            description: "Получение списка тест-кейсов в тест цикле",
            inputSchema: z.object({
                code: z.string().describe("Код тест цикла"),
                attributes: z.array(z.string()).optional(),
                ...pageSizeSchema
            })
        },
        async (input) => textResult(await testCases.getTestCasesInTestCycle(client(), input))
    );

    register(
        "link_test_case_to_test_cycle",
        {
            description: "Добавляет тест-кейсы в тест цикл",
            inputSchema: z.object({
                source: z.string(),
                destinations: z.array(z.string()),
                link_type: z.string()
            })
        },
        async (input) => textResult(await testCases.linkTestCaseToTestCycle(client(), input))
    );

    register(
        "get_work_types",
        {
            description: "Получение информации о видах работ списания рабочего времени",
            inputSchema: z.object({})
        },
        async () => textResult(await timesheet.getWorkTypes(client()))
    );

    /** Zod-схема тела work log (см. {@link WorkLogInput}) */
    const workLogSchema = z.object({
        date: z.string(),
        unit: z.string(),
        comment: z.string().optional(),
        time: z.object({
            time: z.number(),
            temporalUnit: z.enum(["MINUTES", "HOURS"])
        }),
        type: z.object({ code: z.string() }),
        user: z.string()
    });

    register(
        "create_work_log",
        {
            description: "Списание времени",
            inputSchema: workLogSchema
        },
        async (input) => textResult(await timesheet.createWorkLog(client(), input))
    );

    register(
        "create_work_log_range",
        {
            description: "Списание времени в диапазоне дат (исключать выходные)",
            inputSchema: workLogSchema.extend({
                range: z.object({
                    from: z.string().describe("Начало периода YYYY-MM-DD"),
                    to: z.string()
                })
            })
        },
        async (input) => textResult(await timesheet.createWorkLogRange(client(), input))
    );

    register(
        "get_work_log",
        {
            description: "Получение информации о списании",
            inputSchema: z.object({ work_log_id: z.string() })
        },
        async ({ work_log_id }) => textResult(await timesheet.getWorkLog(client(), work_log_id))
    );

    register(
        "update_work_log",
        {
            description: "Изменение списания",
            inputSchema: z.object({
                work_log_id: z.string(),
                request: workLogSchema
            })
        },
        async ({ work_log_id, request }) =>
            textResult(await timesheet.updateWorkLog(client(), work_log_id, request))
    );

    register(
        "delete_work_log",
        {
            description: "Удаление списания",
            inputSchema: z.object({ work_log_id: z.string() })
        },
        async ({ work_log_id }) => textResult(await timesheet.deleteWorkLog(client(), work_log_id))
    );

    register(
        "get_work_report",
        {
            description: "Получение информации о списаниях рабочего времени",
            inputSchema: z.object({
                unit_code: z.string(),
                page: z.number().int(),
                size: z.number().int().optional().default(1000)
            })
        },
        async (input) => textResult(await timesheet.getWorkReport(client(), input))
    );

    register(
        "get_work_sum",
        {
            description: "Сумма списаний рабочего времени по юниту",
            inputSchema: z.object({ unit_code: z.string() })
        },
        async ({ unit_code }) => textResult(await timesheet.getWorkSum(client(), unit_code))
    );
}
