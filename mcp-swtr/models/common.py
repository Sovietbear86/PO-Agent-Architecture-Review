from enum import Enum
from typing import List

from pydantic import BaseModel, Field

class Priority(str, Enum):
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"

class OperatorValuePair(BaseModel):
    property: str = Field(description="Название свойства")
    value: str = Field(description="Значение для поиска")
    operator: str = Field(description="Оператор сравнения (например, 'like')")


class PropertiesFilter(BaseModel):
    or_: List[OperatorValuePair] = Field(default=[], alias='or', description="Список альтернативных условий ('или')")
    and_: List[OperatorValuePair] = Field(default=[], alias='and', description="Список обязательных условий ('и')")


class BasePageSizeRequest(BaseModel):
    page: int = Field(default=0, ge=0, description="Номер страницы (начиная с 0)")
    size: int = Field(default=25, ge=0, description="Количество элементов на странице")

class BaseLinkRequest(BaseModel):
    source: str = Field(..., description="Код источника")
    link_type: str = Field(..., description="Тип связи")
