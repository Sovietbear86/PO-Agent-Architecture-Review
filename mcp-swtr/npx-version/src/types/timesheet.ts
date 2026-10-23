/**
 * Типы домена списания рабочего времени (timesheet).
 * @module types/timesheet
 */

/**
 * Длительность списания.
 */
export interface WorkLogTimeInput {
    /** Число единиц времени */
    time: number;
    /** Единица: минуты или часы */
    temporalUnit: "MINUTES" | "HOURS";
}

/**
 * Вид работы для списания.
 */
export interface WorkLogTypeInput {
    /** Код вида работ */
    code: string;
}

/**
 * Тело создания/обновления одной записи work log.
 */
export interface WorkLogInput {
    /** Дата списания `YYYY-MM-DD` */
    date: string;
    /** Код юнита (задачи) */
    unit: string;
    /** Комментарий */
    comment?: string;
    /** Объём времени */
    time: WorkLogTimeInput;
    /** Тип работ */
    type: WorkLogTypeInput;
    /** Идентификатор пользователя */
    user: string;
}

/**
 * Диапазон дат для массового списания (без выходных на стороне API).
 */
export interface WorkLogRangeInput {
    /** Начало периода `YYYY-MM-DD` */
    from: string;
    /** Конец периода `YYYY-MM-DD` */
    to: string;
}

/**
 * Списание времени на каждый рабочий день в диапазоне.
 */
export interface WorkLogRangeRequestInput extends WorkLogInput {
    /** Интервал дат */
    range: WorkLogRangeInput;
}

/**
 * Параметры отчёта по списаниям юнита.
 */
export interface GetWorkReportInput {
    /** Код юнита */
    unit_code: string;
    /** Номер страницы отчёта */
    page: number;
    /** Размер страницы (по умолчанию 1000) */
    size?: number;
}
