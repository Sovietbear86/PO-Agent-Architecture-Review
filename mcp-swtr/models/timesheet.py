from datetime import date as dt_date
from typing import Optional, Literal
from pydantic import BaseModel, Field

class TimeInfo(BaseModel):
    """Информация о времени"""
    time: int = Field(None, ge=0)
    temporalUnit: Literal['MINUTES', 'HOURS'] = Field(None, description="Единица времени")


class WorkLogType(BaseModel):
    """Тип работы"""
    code: str = None


class WorkLogRange(BaseModel):
    """Период"""
    # Задано from_date, а не from, чтобы не было конфликта с from в pydantic
    from_date: dt_date = Field(..., description="Начало периода", le=dt_date.today(), alias='from')
    to: dt_date = Field(..., description="Конец периода", le=dt_date.today())


class WorkLogCreateRequest(BaseModel):
    """
    Запрос на создание списания рабочего времени
    """
    date: dt_date = Field(..., description="Дата списания рабочего времени", le=dt_date.today())
    unit: str = Field(..., description="Идентификатор юнита", min_length=1)
    comment: Optional[str] = Field(None, description="Комментарий", max_length=4000)
    time: TimeInfo = Field(..., description="Информация о времени")
    type: WorkLogType = Field(..., description="Тип работы")
    user: str = Field(..., description="Идентификатор пользователя", min_length=1)

class WorkLogRangeCreateRequest(BaseModel):
    """
    Запрос на создание списания рабочего времени за период
    """
    range: WorkLogRange = Field(..., description="Период")
    unit: str = Field(..., description="Идентификатор юнита", min_length=1)
    comment: Optional[str] = Field(None, description="Комментарий", max_length=4000)
    time: TimeInfo = Field(..., description="Информация о времени")
    type: WorkLogType = Field(..., description="Тип работы")
    user: str = Field(..., description="Идентификатор пользователя", min_length=1)


class WorkLogUpdateRequest(BaseModel):
    """
    Запрос на обновление списания рабочего времени
    """
    date: dt_date = Field(..., description="Дата списания рабочего времени", le=dt_date.today())
    unit: str = Field(..., description="Идентификатор юнита", min_length=1)
    comment: Optional[str] = Field(None, description="Комментарий", max_length=4000)
    time: TimeInfo = Field(..., description="Информация о времени")
    type: WorkLogType = Field(..., description="Тип работы")
    user: str = Field(..., description="Идентификатор пользователя", min_length=1)