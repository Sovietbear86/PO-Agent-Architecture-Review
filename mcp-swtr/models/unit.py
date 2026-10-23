from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from models.common import BasePageSizeRequest, PropertiesFilter, Priority, BaseLinkRequest


class BaseUnitSearchRequest(BasePageSizeRequest):
    calculatedAttributes: Optional[List[str]] = Field(description="Список вычисляемых атрибутов")
    attributes: List[str] = Field(default=["code", "summary", "priority", "assigned_to"],
                                  description="Список атрибутов")


class UnitSearchRequest(BaseUnitSearchRequest):
    spaces: Optional[List[str]] = Field(None, description="Коды пространств для поиска")
    properties: PropertiesFilter = Field(description="Дополнительная фильтрация по свойствам")
    full_info: bool = Field(default=True, description="Верннуть полную информацию о тикетах")


class TqlSearchRequest(BaseUnitSearchRequest):
    query: str = Field(default="",
                       description='Текст фильтра в формате TQL. Строки должны быть заключены в "", и/или должны быть с большой буквы: OR, AND')
    timeZone: str = Field(default="Europe/Moscow", description="Часовой пояс")


class FindBySpaceRequest(BasePageSizeRequest):
    space: str = Field(None, description="Код пространства")


class BaseUnitRequest(BaseModel):
    suit: str = Field(..., description="Тип юнита")
    space: str = Field(..., description="Код пространства")
    summary: str = Field(..., description="Тема")
    description: str = Field(..., description="Описание")
    attributes: Dict[str, Any] = Field({}, description="Атрибуты юнита")


class UnitCreateRequest(BaseUnitRequest):
    priority: Priority = Field(..., description="Приоритет")
    status: str = Field("NEW", description="Статус")


class UnitUpdateRequest(BaseUnitRequest):
    code: str = Field(description="Код юнита")


class UnitLinkRequest(BaseLinkRequest):
    destination: str = Field(..., description="Код юнита-назначения")


class CommentSearchRequest(BasePageSizeRequest):
    unit_code: str = Field(..., description="Код юнита")


class BaseSearchRequest(BasePageSizeRequest):
    text_search: Optional[str] = Field(None, description="Текст для поиска")


class GetUnitLinksRequest(BasePageSizeRequest):
    unit_code: str = Field(..., description="Код юнита")
    link_types: List[str] = Field([], description="Типы связей")


class VersionSearchRequest(BaseUnitSearchRequest):
    query: str = Field(default="",
                       description='Текст фильтра в формате TQL. Строки должны быть заключены в "", и/или должны быть с большой буквы: OR, AND')
    space: str = Field(..., description="Код пространства")
    withArchived: bool = Field(default=False, description="Включая архивные")
    withDeleted: bool = Field(default=False, description="Включая удаленные")
