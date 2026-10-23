/**
 * Домен списания рабочего времени (timesheet / work log).
 * @module domains/timesheet
 */

import type { SwtrClient } from "../api/client.js";
import type {
    GetWorkReportInput,
    WorkLogInput,
    WorkLogRangeRequestInput
} from "../types/timesheet.js";

/**
 * Справочник видов работ для списания.
 * @param client - HTTP-клиент
 */
export async function getWorkTypes(client: SwtrClient): Promise<string> {
    return client.get("/rest/api/timesheet/v1/worktype");
}

/**
 * Создание одной записи списания.
 * @param client - HTTP-клиент
 * @param input - Тело work log (дата, юнит, время, тип, пользователь)
 */
export async function createWorkLog(client: SwtrClient, input: WorkLogInput): Promise<string> {
    return client.post("/rest/api/timesheet/v1/worklog", input);
}

/**
 * Списание на каждый день диапазона (поле `range`; `from` → `from_date` для API).
 * @param client - HTTP-клиент
 * @param input - Work log + диапазон дат
 */
export async function createWorkLogRange(
    client: SwtrClient,
    input: WorkLogRangeRequestInput
): Promise<string> {
    const body = JSON.parse(JSON.stringify(input)) as {
        range?: { from?: string; from_date?: string; to?: string };
    };
    if (body.range && "from" in body.range) {
        body.range.from_date = body.range.from as string;
        delete (body.range as { from?: string }).from;
    }
    return client.post("/rest/api/timesheet/v1/worklog", body);
}

/**
 * Чтение записи списания по id.
 * @param client - HTTP-клиент
 * @param work_log_id - Идентификатор work log
 */
export async function getWorkLog(client: SwtrClient, work_log_id: string): Promise<string> {
    return client.get(`/rest/api/timesheet/v1/worklog/${work_log_id}`);
}

/**
 * Обновление записи списания.
 * @param client - HTTP-клиент
 * @param work_log_id - Идентификатор work log
 * @param input - Новое тело work log
 */
export async function updateWorkLog(
    client: SwtrClient,
    work_log_id: string,
    input: WorkLogInput
): Promise<string> {
    return client.patch(`/rest/api/timesheet/v1/worklog/${work_log_id}`, input);
}

/**
 * Удаление записи списания.
 * @param client - HTTP-клиент
 * @param work_log_id - Идентификатор work log
 */
export async function deleteWorkLog(client: SwtrClient, work_log_id: string): Promise<string> {
    return client.delete(`/rest/api/timesheet/v1/worklog/${work_log_id}`);
}

/**
 * Отчёт по списаниям на юнит (пагинация).
 * @param client - HTTP-клиент
 * @param input - Код юнита, страница, размер
 */
export async function getWorkReport(
    client: SwtrClient,
    input: GetWorkReportInput
): Promise<string> {
    const size = input.size ?? 1000;
    return client.get(
        `/rest/api/timesheet/v1/report/${input.unit_code}?page=${input.page}&size=${size}`
    );
}

/**
 * Суммарное списанное время по юниту.
 * @param client - HTTP-клиент
 * @param unit_code - Код юнита
 */
export async function getWorkSum(client: SwtrClient, unit_code: string): Promise<string> {
    return client.get(`/rest/api/timesheet/v1/report/${unit_code}/sum`);
}
