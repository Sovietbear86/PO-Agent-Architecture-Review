from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from models.common import BasePageSizeRequest, Priority, PropertiesFilter, BaseLinkRequest
from models.wiki import PageContent


class TestType(str, Enum):
    usability_type = "usability_type"
    security_type = "security_type"
    integration_type = "integration_type"
    e2e_type = "e2e_type"
    mt_type = "mt_type"
    lt_type = "lt_type"
    et_type = "et_type"
    other_type = "other_type"


class TypeOfTesting(str, Enum):
    regress = "regress"
    new = "new"


class YesNo(str, Enum):
    yes = "yes"
    no = "not"


class SortDirection(str, Enum):
    asc = "ASC"
    desc = "DESC"


class TesCaseStatus(Enum):
    DRAFT = "draft"
    RECEPTION = "reception"
    IN_PROGRESS = "in_progress"
    RELEVANT = "relevant"
    NOT_RELEVANT = "not_relevant"
    REGRESS = "regress"
    REMOVED = "removed"


class TestStepFormattedText(BaseModel):
    """
    Форматированный текст с атрибутами и контентом.
    """
    formattedText: str = Field(
        None,
        title='Обычный текст',
        description='Прямой простой текст без разметки.'
    )
    plainText: str = Field(
        None,
        title='Обычный текст',
        description='Прямой простой текст без разметки.'
    )


class FileMetadataDto(BaseModel):
    contentType: str
    contentLength: int


class CreatedBy(BaseModel):
    externalId: str
    firstName: str
    lastName: str
    middleName: str
    login: str
    locale: str


class FilePathParsedDto(BaseModel):
    relatedToType: str
    relativePath: str
    fileName: str


class File(BaseModel):
    fileId: UUID
    filePathParsedDto: FilePathParsedDto
    createdBy: CreatedBy
    createdAt: datetime
    fileMetadataDto: FileMetadataDto


class TestCaseStepItem(BaseModel):
    """
    Данные шага теста.
    """
    code: Optional[UUID] = Field(None, description='Код шага')
    stepDescription: Optional[TestStepFormattedText] = Field(
        None,
        title='Описание шага',
        description='Описание действий в формате HTML или JSON.'
    )
    stepData: Optional[TestStepFormattedText] = Field(
        None,
        title='Данные шага',
        description='Информация, необходимая для выполнения шага.'
    )
    stepResult: Optional[TestStepFormattedText] = Field(
        None,
        title='Результат шага',
        description='Описание ожидаемого результата.'
    )
    callToTestId: Optional[UUID] = Field(
        default=None,
        title='Связанный ID теста',
        description='ID связанного теста, если есть.'
    )
    stepNumber: int = Field(
        title='Номер шага',
        description='Последовательность шагов в тестовом сценарии.'
    )
    deleted: bool = Field(
        False,
        title='Удалено?',
        description='Признак удаления шага.'
    )
    stepFiles: Optional[List[File]] = Field(
        [],
        title='Файлы шага',
        description='Файлы, прикрепленные непосредственно к данному шагу.'
    )


class TestCaseStepList(BaseModel):
    """
    Список шагов тестов.
    """
    testStepList: List[TestCaseStepItem] = Field(
        title='Шаги теста',
        description='Перечень шагов в рамках одного сценария тестирования.'
    )


class TestCaseStepAttributes(BaseModel):
    """
    Контейнер атрибутов тестовых шагов.
    """
    test_step: TestCaseStepList = Field(
        title='Шаг теста',
        description='Основные шаги в тестировании.'
    )


class TestCaseStepRequest(BaseModel):
    """
    Корневой класс для основного JSON.
    """
    code: str = Field(description='Код тест-кейса')
    attributes: TestCaseStepAttributes = Field(
        title='Атрибуты тестового шага',
        description='Основной контейнер с информацией о тестовых шагах.'
    )


class BaseTestAttributes(BaseModel):
    """Набор атрибутов теста"""
    space: str = Field(description="Пространство")
    tenant: str = Field("default", description="Тенант")
    folder: str = Field(description="Каталог")
    owner: Optional[str] = Field(None, description="Ответственный владелец")
    type_of_testing: TypeOfTesting = Field(..., description="Тип тестирования")


class TestCaseAttributes(BaseTestAttributes):
    """Набор атрибутов тест-кейса"""
    precondition: Optional[PageContent] = Field(description="Предусловия теста")
    priority: Priority = Field(..., description="Приоритет")
    test_case_status: TesCaseStatus = Field(TesCaseStatus.DRAFT.value, description="Статус тест кейса")
    pmi: YesNo = Field(description="ПМИ yes/no")
    test_type: TestType = Field(..., description="Вид теста")
    component_version: Optional[str] = Field(None, description="Версия компонента")
    component_code: Optional[str] = Field(None, description="Код компонента")
    test_level: Optional[str] = Field(None, description="Уровень тестирования")
    label: Optional[List[str]] = Field(None, description="Маркер или метка")
    estimate: Optional[str] = Field(None, description="Оценочная трудоемкость")
    automated: Optional[str] = Field(None, description="Автоматизирован")
    test_step: Optional[TestCaseStepList] = Field(None, description="Шаг тестирования")


class TestCycleAttributes(BaseTestAttributes):
    """Набор атрибутов тест-цикла"""
    plan_date_end: Optional[str] = Field(None, description="Плановая дата окончания")
    plan_date_start: Optional[str] = Field(None, description="Плановая дата начала")
    test_case_test_type: Optional[TypeOfTesting] = Field(TypeOfTesting.regress.value,
                                                         description="Тип теста для тест-кейсов")
    test_cycle_status: Optional[str] = Field("draft", description="Статус тест-цикла")
    release_name: str = Field(..., description="Название релиза")
    cycles_number: str = Field("1", description="Номер цикла")
    iteration_type: Optional[str] = Field(None, description="Тип итерации")
    old_jira_key: Optional[str] = Field(None, description="Старый ключ Jira")
    cycle_automated: Optional[str] = Field(None, description="Цикл автоматизирован")


class BaseTestCreateRequest(BaseModel):
    """Модель тест-кейса"""
    summary: str = Field(description="Краткое описание")
    description: Optional[PageContent] = Field(description="Полное описание")
    code: Optional[str] = Field(description="Код")
    space: str = Field(description="Пространство")


class TestCaseCreateRequest(BaseTestCreateRequest):
    """Модель тест-кейса"""
    attributes: TestCaseAttributes = Field(description="Дополнительные атрибуты кейса")
    suit: str = Field("test_case", description="Тестовый набор")


class TestCycleCreateRequest(BaseTestCreateRequest):
    """Модель тест-кейса"""
    attributes: TestCycleAttributes = Field(description="Дополнительные атрибуты кейса")
    suit: str = Field("test_cycle", description="Тестовый набор")


class TestCaseDataId(BaseModel):
    parameterId: Optional[UUID] = None


class TestCaseDataValue(BaseModel):
    order: int = Field(description="Порядок")
    value: str = Field(description="Значение")


class TestCaseData(BaseModel):
    id: Optional[TestCaseDataId] = None
    order: int = Field(description="Порядок")
    name: str = Field(description="Наименование")


class TestCaseDataEntry(TestCaseData):
    value: List[TestCaseDataValue] = Field(description="Значение")


class TestCaseParameterEntry(TestCaseData):
    value: str = Field(description="Значение")


class TestCaseParametersRequest(BaseModel):
    code: Optional[str] = Field(description="Код кейса")
    parameters: List[TestCaseParameterEntry] = Field(description="Параметры")


class TestCaseDataRequest(BaseModel):
    code: Optional[str] = Field(description="Код кейса")
    data: List[TestCaseDataEntry]


class Filters(BaseModel):
    attributes: PropertiesFilter = Field(description="Фильтры по атрибутам (OR и AND)")
    properties: PropertiesFilter = Field(description="Дополнительная фильтрация по свойствам")


class Sort(BaseModel):
    direction: SortDirection = Field(SortDirection.asc.value,
                                     description="Направление сортировки (по возрастанию или убыванию)")
    attribute: List[str] = Field(default=["createdAt"], min_items=1, max_items=1, description="Атрибут для сортировки")


class SearchTestCaseRequest(BasePageSizeRequest):
    folder: str = Field(description="Каталог тест-кейса")
    attributes: List[str] = Field(description="Список атрибутов")
    filters: Filters = Field(description="Параметры фильтрации")
    sort: Sort = Field(None, description="Параметры сортировки")


class GetTestCasesRequest(BasePageSizeRequest):
    attributes: List[str] = Field(default=["test_case_status",
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
                                           "folder"],
                                  description="Список атрибутов")
    space: str = Field(description="Пространство")


class TestCasesInCycleRequest(BasePageSizeRequest):
    attributes: List[str] = Field(default=["test_case_status"],
                                  description="Список атрибутов")
    code: str = Field(description="Код тест цикла")


class TestCycleLinkRequest(BaseLinkRequest):
    destinations: List[str] = Field(..., description="Список кодов тест-кейсов")
