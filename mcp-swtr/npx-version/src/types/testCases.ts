/**
 * Типы домена тест-кейсов и TMS.
 * @module types/testCases
 */

import type { PageContentInput, PageInput, PropertiesFilter } from "./common.js";

/**
 * Сортировка списка тест-кейсов в каталоге.
 */
export interface TestCaseSortInput {
    /** Направление (`ASC` / `DESC` и т.п.) */
    direction?: string;
    /** Поля для сортировки */
    attribute?: string[];
}

/**
 * Фильтры поиска тест-кейсов в папке иерархии.
 */
export interface TestCaseSearchFiltersInput {
    /** Фильтр по атрибутам */
    attributes: PropertiesFilter;
    /** Фильтр по свойствам */
    properties: PropertiesFilter;
}

/**
 * Параметры `search_test_cases`.
 */
export interface SearchTestCasesInput extends PageInput {
    /** Код папки в иерархии TMS */
    folder: string;
    /** Список запрашиваемых атрибутов */
    attributes: string[];
    /** Составные фильтры */
    filters: TestCaseSearchFiltersInput;
    /** Сортировка */
    sort?: TestCaseSortInput | null;
}

/**
 * Общие поля создания тест-кейса или тест-цикла.
 */
export interface CreateTestArtifactInput {
    /** Заголовок */
    summary: string;
    /** Rich-text описание */
    description?: PageContentInput | null;
    /** Явный код (опционально) */
    code?: string | null;
    /** Код пространства */
    space: string;
    /** Код suit (`test_case` / `test_cycle`) */
    suit?: string;
    /** Атрибуты TMS */
    attributes: Record<string, unknown>;
}

/**
 * Параметры создания шага тест-кейса (patch атрибутов).
 */
export interface CreateTestCaseStepInput {
    /** Код тест-кейса */
    code: string;
    /** Атрибуты с `test_step` / formattedText */
    attributes: Record<string, unknown>;
}

/**
 * Обновление тестовых данных кейса.
 */
export interface UpdateTestCaseDataInput {
    /** Код тест-кейса */
    code?: string | null;
    /** Массив записей test data */
    data: unknown[];
}

/**
 * Обновление параметров кейса.
 */
export interface UpdateTestCaseParametersInput {
    /** Код тест-кейса */
    code?: string | null;
    /** Массив параметров */
    parameters: unknown[];
}

/**
 * Список тест-кейсов корневой папки пространства.
 */
export interface GetTestCasesInput extends PageInput {
    /** Код пространства */
    space: string;
    /** Запрашиваемые атрибуты (есть дефолтный набор) */
    attributes?: string[];
}

/**
 * Тест-кейсы, привязанные к тест-циклу.
 */
export interface GetTestCasesInTestCycleInput extends PageInput {
    /** Код тест-цикла */
    code: string;
    /** Атрибуты в ответе */
    attributes?: string[];
}

/**
 * Связь тест-кейсов с тест-циклом.
 */
export interface LinkTestCaseToTestCycleInput {
    /** Код тест-цикла (источник) */
    source: string;
    /** Коды тест-кейсов */
    destinations: string[];
    /** Тип связи TMS */
    link_type: string;
}
