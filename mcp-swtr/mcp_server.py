import base64
import json
import os
from typing import Any, Set, Optional

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from mcp.types import ImageContent, TextContent
from pydantic import Field

from models.test_case import TestCaseCreateRequest, TestCaseStepRequest, \
    TestCaseParametersRequest, TestCaseDataRequest, SearchTestCaseRequest, TestCycleCreateRequest, GetTestCasesRequest, \
    TestCasesInCycleRequest, TestCycleLinkRequest
from models.timesheet import WorkLogCreateRequest, WorkLogRangeCreateRequest, WorkLogUpdateRequest
from models.unit import UnitSearchRequest, UnitCreateRequest, UnitLinkRequest, CommentSearchRequest, BaseSearchRequest, \
    GetUnitLinksRequest, FindBySpaceRequest, TqlSearchRequest, UnitUpdateRequest, VersionSearchRequest
from models.wiki import WikiSearchRequest, WikiPageCreateRequest, PageContent, SafePageContent


def safe_json_dumps(obj: Any, seen: Set[int] = None) -> Any:
    """
    Безопасная сериализация JSON с обработкой циклических ссылок.
    """
    if seen is None:
        seen = set()
    
    if obj is None:
        return None
    
    obj_id = id(obj)
    if obj_id in seen:
        return "[Circular Reference]"
    
    if isinstance(obj, dict):
        seen.add(obj_id)
        result = {k: safe_json_dumps(v, seen) for k, v in obj.items()}
        seen.discard(obj_id)
        return result
    elif isinstance(obj, list):
        seen.add(obj_id)
        result = [safe_json_dumps(item, seen) for item in obj]
        seen.discard(obj_id)
        return result
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif hasattr(obj, 'model_dump'):
        # Pydantic модель
        try:
            return safe_json_dumps(obj.model_dump(mode='json', by_alias=True, exclude_none=True), seen)
        except ValueError:
            # Если возникает ошибка циклической ссылки, пробуем с exclude
            return safe_json_dumps(obj.model_dump(mode='json', by_alias=True, exclude_none=True, exclude={'content': True}), seen)
    elif hasattr(obj, '__dict__'):
        return safe_json_dumps(obj.__dict__, seen)
    else:
        return str(obj)

mcp = FastMCP("mcp-swtr")

load_dotenv()

# Базовый URL API
base_url = os.getenv("BASE_URL")

token = os.getenv("TOKEN")

try:
    port = int(os.getenv("PORT"))
except:
    port = 0

timeout = 10


def get_headers():
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cookie': 'api_swtr_as21=true'
    }
    return headers


async def call_api_get(url: str):
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        response = await client.get(
            f'{base_url}{url}',
            headers=get_headers()
        )
        return response


async def call_api_post(url: str, payload: dict[str, Any]):
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        response = await client.post(
            f'{base_url}{url}',
            json=payload,
            headers=get_headers()
        )
        return response


async def call_api_patch(url: str, payload: dict[str, Any]):
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        response = await client.patch(
            f'{base_url}{url}',
            json=payload,
            headers=get_headers()
        )
        return response


async def call_api_delete(url: str):
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        response = await client.delete(
            f'{base_url}{url}',
            headers=get_headers()
        )
        return response


@mcp.tool()
async def read_unit(code: str = Field(..., description="Код юнита")) -> str:
    """Чтение юнита"""
    response = await call_api_get(f"/rest/api/unit/v2/{code}")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_unit_types_by_space(request: FindBySpaceRequest) -> str:
    """Получение типов юнитов по заданному пространству"""

    payload = {
        "filters": {
            "space": request.space or []
        },
        "page": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        "/rest/api/suit/v1/find",
        payload,
    )
    return response.text


@mcp.tool()
async def find_units(request: UnitSearchRequest) -> str:
    """Поиск юнитов по заданным пространствам"""

    payload = {
        "calculatedAttributes": request.calculatedAttributes or [],
        "attributes": request.attributes or [],
        "filters": {
            "properties": request.properties.model_dump(mode='json', by_alias=True),
            "spaces": request.spaces or []
        },
        "page": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        "/rest/api/unit/v2/find",
        payload,
    )
    if request.full_info:
        try:
            response_json = response.json()
            return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
        except Exception:
            return response.text
    else:
        try:
            # Parse response and remove 'unit' attribute from results
            response_json = response.json()
            if 'content' in response_json:
                # Remove 'unit' attribute from each item
                for item in response_json['content']:
                    if isinstance(item, dict) and 'unit' in item:
                        del item['unit']
            # Return modified response as string
            return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
        except Exception:
            # If parsing fails, return original response
            return response.text


@mcp.tool()
async def find_units_by_filter(request: TqlSearchRequest) -> str:
    """Поиск юнитов по фильтру TQL (используй get_tql_properties для построения фильтров). Пример query: summary ~ "test" OR description ~ "test" """

    payload = {
        "calculatedAttributes": request.calculatedAttributes or [],
        "attributes": request.attributes or [],
        "query": request.query,
        "timeZone": request.timeZone,
        "page": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        "/rest/api/unit/v3/find/tql",
        payload,
    )

    return response.text


@mcp.tool()
async def get_tql_properties() -> str:
    """Получение информации об атрибутах для фильтрации c tql"""
    response = await call_api_get("/rest/api/attr/v1/tql/properties")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def create_unit(request: UnitCreateRequest) -> str:
    """Создание нового юнита"""
    request.attributes.update({"priority": request.priority,
                               "workflow_status": {
                                   "command": request.status
                               }})
    response = await call_api_post(
        f"/rest/api/unit/v2/{request.suit}/create",
        {"description": request.description, "summary": request.summary, "space": request.space,
         "attributes": request.attributes}
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def update_unit(request: UnitUpdateRequest) -> str:
    """Редактирование юнита"""

    payload = {
        "description": request.description,
        "suit": request.suit,
        "space": request.space,
        "summary": request.summary,
        "code": request.code,
        "attributes": request.attributes or []
    }
    response = await call_api_patch(
        f"/rest/api/unit/v2/update/{request.code}",
        payload,
    )
    return response.text


@mcp.tool()
async def create_unit_link(request: UnitLinkRequest) -> str:
    """Создание связи между юнитами"""

    payload = {
        "source": request.source,
        "destination": request.destination,
        "type": request.link_type
    }
    response = await call_api_post(
        "/rest/api/unit/v1/link",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def create_unit_comment(unit_code: str = Field(..., description="Код юнита"),
                              comment_text: str = Field(..., description="Текст комментария")) -> str:
    """Создание комментария к юниту"""
    payload = {
        "unitCode": unit_code,
        "commentText": comment_text
    }
    response = await call_api_post(
        "/rest/api/unit-comment/v1/create",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_unit_comments(request: CommentSearchRequest) -> str:
    """Получение комментариев юнита"""

    payload = {
        "unitCode": request.unit_code,
        "pageDtoRq": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        "/rest/api/unit-comment/v1/find",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


# @mcp.tool()
# пока не работает {'errorDtoObject': None, 'errorType': 'SWTR_BASIC_ERROR', 'exceptionUUID': 'FKMaVgkBom', 'uiErrorMessage': "Элемент 'LinkType' с идентификатором 'SWTR-1' не найден"}
async def get_unit_link_types(code: str = Field(..., description="Код юнита")) -> str:
    """Получение типа связи между юнитами по коду юнита"""

    response = await call_api_get(
        f"/rest/api/unit/v2/link/type/{code}"
    )
    return response.text


@mcp.tool()
async def search_link_types(request: BaseSearchRequest) -> str:
    """Поиск типов связей между юнитами"""

    payload = {
        "filters": {
            "textSearch": request.text_search
        },
        "page": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        "/rest/api/unit/v2/link/types",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_unit_links(request: GetUnitLinksRequest) -> str:
    """Получение связей между юнитами"""

    payload = {
        "type": request.link_types,
        "unitId": request.unit_code,
        "page": {
            "page": {
                "page": request.page,
                "size": request.size}
        }
    }
    response = await call_api_post(
        "/rest/api/unit/v1/link/find",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_unit_attributes() -> str:
    """Получение информации о списках атрибутов unit"""
    response = await call_api_get("/rest/api/attr/v1/findAll")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def search_users(request: BaseSearchRequest) -> str:
    """Создание данных тест-кейса"""
    payload = {
        "searchString": request.text_search,
        "paging": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        f"/rest/api/user/v1/search",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def search_versions(request: VersionSearchRequest) -> str:
    """Поиск версий (релизов)"""
    payload = {
        "query": request.query,
        "space": request.space,
        "withArchived": request.withArchived,
        "withDeleted": request.withDeleted,
        "page": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        f"/extension/plugin/v2/rest/api/swtr_task_tracker_plugin/v1/version/find",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def search_sprints(request: FindBySpaceRequest) -> str:
    """Поиск спринтов в указанном пространстве"""
    payload = {
        "space": request.space,
        "page": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        f"/extension/plugin/v2/rest/api/scrum_board_plugin/v1/sprint/find",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_current_sprint(space: str = Field(..., description="Код пространства")) -> str:
    """Получение текущего активного спринта в пространстве"""
    payload = {
        "space": space,
        "page": {"page": 0, "size": 10}
    }
    response = await call_api_post(
        f"/extension/plugin/v2/rest/api/scrum_board_plugin/v1/sprint/find",
        payload
    )
    try:
        response_json = response.json()
        # Find active sprint (not completed, not future)
        if 'content' in response_json:
            for sprint in response_json['content']:
                if sprint.get('state') == 'ACTIVE' or (not sprint.get('closed', False) and not sprint.get('completed', False)):
                    return json.dumps(safe_json_dumps(sprint), ensure_ascii=False, indent=2)
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_sprint_tasks(sprint_id: str = Field(..., description="ID спринта (например, DMS-SPRNT-1)")) -> str:
    """Получение всех задач в спринте по ID спринта"""
    # Use TQL to find tasks in the sprint
    # Sprint attribute is named "scrum_board_plugin_sprint"
    tql_query = f"scrum_board_plugin_sprint = \"{sprint_id}\""
    
    payload = {
        "calculatedAttributes": [],
        "attributes": ["code", "summary", "workflow_status", "assigned_to"],
        "query": tql_query,
        "page": {
            "page": 0,
            "size": 100
        }
    }
    
    response = await call_api_post(
        "/rest/api/unit/v3/find/tql",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_current_sprint_tasks(space: str = Field(..., description="Код пространства (DMS, OLP, WMB)")) -> str:
    """Получение всех задач в текущем активном спринте пространства"""
    # First get current sprint
    sprint_info = await get_current_sprint(space=space)
    try:
        sprint_data = json.loads(sprint_info)
        # Extract sprint ID from response
        if 'content' in sprint_data:
            for item in sprint_data['content']:
                if item.get('type') == 'text':
                    sprint_json = json.loads(item.get('text', '{}'))
                    sprint_id = sprint_json.get('id', {}).get('code', '')
                    if sprint_id:
                        # Get tasks in this sprint
                        return await get_sprint_tasks(sprint_id=sprint_id)
    except:
        pass
    return sprint_info


@mcp.tool()
async def search_wiki_pages(request: WikiSearchRequest) -> str:
    """Поиск wiki-страниц"""
    # Эндпоинт для wiki нужно уточнить в документации

    payload = {
        "filters": {
            "spaces": request.spaces or [],
            "units": request.units or [],
            "query": request.text_search
        },
        "page": {
            "page": request.page,
            "size": request.size
        }
    }
    response = await call_api_post(
        "/extension/plugin/v2/rest/api/swtr_wiki_plugin/v1/wiki/unit/find",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def read_wiki_page(code: str = Field(..., description="Код страницы")) -> str:
    """Чтение wiki-страницы"""

    response = await call_api_get(
        f"/extension/plugin/v2/rest/api/swtr_wiki_plugin/v1/wiki/unit/{code}"
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def create_wiki_page(request: WikiPageCreateRequest) -> str:
    """Создание новой wiki-страницы"""
    payload = {
        "space": request.space_code,
        "summary": request.title,
        "description": request.description,
        "attributes": {
            "label": request.labels,
            "wiki_page_body": request.content.model_dump_json()
        }
    }
    response = await call_api_post(
        "/rest/api/unit/v2/wiki_page/create",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def search_test_cases(request: SearchTestCaseRequest) -> str:
    """Поиск тест-кейсов"""

    payload = {
        "filters": request.filters.model_dump(mode='json', by_alias=True),
        "attributes": request.attributes,
        "page": {"page": request.page, "size": request.size},
        "sort": request.sort
    }
    response = await call_api_post(
        f"/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/hierarchy/{request.folder}/units",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_test_case_folders(code: str = Field(..., description="Код пространства")) -> str:
    """Получить список каталогов тест-кейсов"""
    payload = {
        "type": "TEST_CASE",
        "spaceId": {
            "code": code
        }
    }
    response = await call_api_post(
        "/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/root",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def read_test_case(code: str = Field(..., description="Код тест-кейса")) -> str:
    """Получение информации о тест-кейсе"""
    response = await call_api_get(
        f"/rest/api/unit/v2/{code}")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def create_test_case(request: TestCaseCreateRequest) -> str:
    """Создание нового тест-кейса"""
    # жуткий костыль, потому что precondition принимает JSON строкой!!!
    precondition = request.attributes.precondition
    if precondition:
        request.attributes.precondition = SafePageContent.from_page_content(precondition).model_dump_json()

    payload = {
        "summary": request.summary,
        "description": SafePageContent.from_page_content(request.description).model_dump_json() if request.description else None,
        "code": request.code,
        "space": request.space,
        "suit": request.suit,
        "attributes": request.attributes.model_dump(mode='json')
    }

    response = await call_api_post(
        f"/rest/api/unit/v2/{request.suit}/create",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def create_test_case_step(request: TestCaseStepRequest) -> str:
    """Создание шага тест-кейса"""
    # жуткий костыль, потому что formattedText принимает JSON строкой!!!
    for item in request.attributes.test_step.testStepList:
        item.stepResult.formattedText = SafePageContent(content=[{"type": "paragraph", "content": [
            {"type": "text", "text": item.stepResult.formattedText}]}]).model_dump_json()
        item.stepDescription.formattedText = SafePageContent(content=[{"type": "paragraph", "content": [
            {"type": "text", "text": item.stepDescription.formattedText}]}]).model_dump_json()
        item.stepData.formattedText = SafePageContent(content=[{"type": "paragraph", "content": [
            {"type": "text", "text": item.stepData.formattedText}]}]).model_dump_json()

    payload = {
        "attributes": request.attributes.model_dump(mode='json')
    }
    response = await call_api_patch(
        f"/rest/api/unit/v2/update/{request.code}",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def update_test_case_data(request: TestCaseDataRequest) -> str:
    """Создание данных тест-кейса"""
    payload = {
        "data": request.daa
    }
    response = await call_api_post(
        f"/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/test_case/{request.code}/test_data",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def update_test_case_parameters(request: TestCaseParametersRequest) -> str:
    """Создание параметров тест-кейса"""
    payload = {
        "parameters": request.parameters
    }
    response = await call_api_patch(
        f"/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/test_case/{request.code}/parameters",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_step_info_parameters(code: str = Field(..., description="Код тест-кейса")) -> str:
    """Получение информации о параметрах шагов тест-кейса"""
    response = await call_api_get(
        f"/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/test_case/{code}/test_case_step_info")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def create_test_cycle(request: TestCycleCreateRequest) -> str:
    """Создание нового тест цикла"""

    payload = {
        "summary": request.summary,
        "description": SafePageContent.from_page_content(request.description).model_dump_json() if request.description else None,
        "code": request.code,
        "space": request.space,
        "suit": request.suit,
        "attributes": request.attributes.model_dump(mode='json')
    }

    response = await call_api_post(
        f"/rest/api/unit/v2/test_cycle/create",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_test_cases(request: GetTestCasesRequest) -> str:
    """Получение списка тест-кейсов"""
    payload = {
        "getRootFolderRq": {
            "type": "TEST_CASE",
            "spaceId": {
                "code": request.space
            }
        },
        "unitFilters": {
            "attributes": [
                request.attributes
            ],
            "page": {
                "page": request.page,
                "size": request.size
            }
        }
    }

    response = await call_api_post(
        f"/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/folder/root/units",
        payload)
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_test_cases_in_test_cycle(request: TestCasesInCycleRequest) -> str:
    """Получение списка тест-кейсов в тест цикле"""
    payload = {
        "unitId": {
            "code": request.code
        },
        "unitFilters": {
            "attributes": request.attributes,
            "page": {
                "page": request.page,
                "size": request.size
            }
        }
    }

    response = await call_api_post(
        f"/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/link/test_cycle/test_cases",
        payload)
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def link_test_case_to_test_cycle(request: TestCycleLinkRequest) -> str:
    """Добавляет тест-кейсы в тест цикл"""

    payload = {
        "source": request.source,
        "destinations": request.destinations,
        "type": request.link_type
    }
    response = await call_api_post(
        "/extension/plugin/v2/rest/api/swtr_tms_plugin/v1/link",
        payload
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_work_types() -> str:
    """Получение информации о видах работ списания рабочего времени"""
    response = await call_api_get("/rest/api/timesheet/v1/worktype")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json))
    except Exception:
        return response.text


@mcp.tool()
async def create_work_log(request: WorkLogCreateRequest) -> str:
    """Списание времени
    Пример Запроса:
    ```
    {
        "date": "2025-02-15",
        "unit": "FOO-123",
        "comment": "comment",
        "time": {
            "temporalUnit": "HOURS",
            "time": 1
        },
        "type": {
            "code": "16"
        },
        "user": "Familiya.I.O"
    }
    ```
    """
    # Преобразуем поля для совместимости с API
    request_dict = request.model_dump(mode='json')
    response = await call_api_post(
        "/rest/api/timesheet/v1/worklog",
        request_dict
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def create_work_log_range(request: WorkLogRangeCreateRequest) -> str:
    """Списание времени в диапазоне дат (требуется исключать выходные дни)
    Пример Запроса:
    ```
    {
        "range": {
            "from": "2025-02-14",
            "to": "2025-02-16"
        },
        "unit": "FOO-123",
        "comment": "comment",
        "time": {
            "temporalUnit": "HOURS",
            "time": 1
        },
        "type": {
            "code": "16"
        },
        "user": "Familiya.I.O"
    }
    ```
    """
    # Преобразуем поля для совместимости с API
    request_dict = request.model_dump(mode='json')
    request_dict['range']['from'] = request_dict['range'].pop('from_date')
    response = await call_api_post(
        "/rest/api/timesheet/v1/worklog",
        request_dict
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_work_log(work_log_id: str = Field(..., description="ID списания")) -> str:
    """Получение информации о списании"""
    response = await call_api_get(f"/rest/api/timesheet/v1/worklog/{work_log_id}")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def update_work_log(work_log_id: str = Field(..., description="ID списания"),
                          request: WorkLogUpdateRequest = Field(..., description="Запрос на обновление")) -> str:
    """Изменение списания
    Пример Запроса:
    ```
    {
        "date": "2025-02-15",
        "unit": "FOO-123",
        "comment": "comment",
        "time": {
            "temporalUnit": "HOURS",
            "time": 1
        },
        "type": {
            "code": "16"
        },
        "user": "Familiya.I.O"
    }
    ```
    """
    response = await call_api_patch(
        f"/rest/api/timesheet/v1/worklog/{work_log_id}",
        request.model_dump(mode='json')
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def delete_work_log(work_log_id: str = Field(..., description="ID списания")) -> str:
    """Удаление списания"""
    response = await call_api_delete(f"/rest/api/timesheet/v1/worklog/{work_log_id}")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_work_report(unit_code: str = Field(..., description="Код юнита"),
                          page: int = Field(..., description="Номер страницы"),
                          size: int = Field(1000, description="Размер страницы")) -> str:
    """Получение информации о списаниях рабочего времени"""
    response = await call_api_get(
        f"/rest/api/timesheet/v1/report/{unit_code}?page={page}&size={size}"
    )
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_work_sum(unit_code: str = Field(..., description="Код юнита")) -> str:
    """Сумма списаний рабочего времени по юниту"""
    response = await call_api_get(f"/rest/api/timesheet/v1/report/{unit_code}/sum")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_unit_files(unit_code: str = Field(..., description="Код юнита"),
                         safe: bool = Field(False, description="Безопасный режим: не падать если файл не найден в S3")) -> str:
    """Получение информации о файлах юнита"""
    response = await call_api_get(f"/rest/api/unit/files/v2/{unit_code}?safe={str(safe).lower()}")
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def download_unit_file(file_id: str = Field(..., description="UUID файла юнита")) -> list[ImageContent | TextContent]:
    """Скачивает файл юнита. Возвращает файл в формате, зависящем от MIME-типа:
    - растровые изображения → ImageContent
    - drawio → XML текст
    - PDF → base64 строка
    - остальное → JSON с метаданными
    """
    response = await call_api_get(f"/rest/api/unit/files/v1/download?fileId={file_id}")
    raw_content_type = (response.headers.get("content-type") or "application/octet-stream").lower()
    # Очищаем MIME-тип от параметров (например, image/png;charset=utf-8 → image/png)
    content_type = raw_content_type.split(";")[0].strip()
    raw_bytes = response.content

    # Ошибка API (JSON с описанием)
    if content_type.startswith("application/json"):
        try:
            error_data = safe_json_dumps(response.json())
            return [TextContent(type="text", text=json.dumps(error_data, ensure_ascii=False, indent=2))]
        except Exception:
            return [TextContent(type="text", text=response.text)]

    # Растровые изображения → ImageContent
    if content_type.startswith("image/"):
        b64 = base64.b64encode(raw_bytes).decode("utf-8")
        return [ImageContent(type="image", data=b64, mimeType=content_type)]

    # Drawio → XML текст (несжатый)
    if "drawio" in raw_content_type:
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = raw_bytes.decode("utf-8", errors="replace")
        return [TextContent(type="text", text=text)]

    # PDF → base64 строка
    if content_type == "application/pdf":
        b64 = base64.b64encode(raw_bytes).decode("utf-8")
        return [TextContent(type="text", text=b64)]

    # Остальные файлы → JSON с метаданными
    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    return [TextContent(
        type="text",
        text=json.dumps({
            "file_id": file_id,
            "content_base64": b64,
            "content_type": content_type,
            "content_length": len(raw_bytes),
        }, ensure_ascii=False, indent=2)
    )]


def main():
    if port == 0:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host="0.0.0.0", port=port)


@mcp.tool()
async def get_my_tasks(assignee: str = Field(..., description="ФИО исполнителя (например, 'Калачанов Виктор')")) -> str:
    """Получение задач на указанного исполнителя через поиск по фразе"""
    # Extract last name from full name
    parts = assignee.strip().split()
    last_name = parts[0] if parts else assignee
    
    payload = {
        "query": last_name,
        "attributes": ["code", "summary", "workflow_status", "assigned_to"],
        "page": {"page": 0, "size": 50}
    }
    
    response = await call_api_post("/rest/api/unit/v3/find", payload)
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def get_task(task_id: str = Field(..., description="ID задачи (например, WMB-123)")) -> str:
    """Получение деталей задачи по ID"""
    payload = {
        "query": task_id,
        "attributes": ["code", "summary", "description", "workflow_status", "assigned_to", "created_at", "updated_at"],
        "page": {"page": 0, "size": 1}
    }
    
    response = await call_api_post("/rest/api/unit/v3/find", payload)
    try:
        response_json = response.json()
        if response_json.get('content') and len(response_json['content']) > 0:
            return json.dumps(safe_json_dumps(response_json['content'][0]), ensure_ascii=False, indent=2)
        return json.dumps({"error": f"Task {task_id} not found"}, ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
async def search_tasks(
    search_terms: str = Field(..., description="Поисковый запрос"),
    status: Optional[str] = Field(None, description="Статус задачи (optional)"),
    assignee: Optional[str] = Field(None, description="Имя исполнителя (optional)"),
    limit: int = Field(10, description="Максимальное количество результатов")
) -> str:
    """Поиск задач по фразе и фильтрам"""
    # Extract last name if assignee is provided
    assignee_query = ""
    if assignee:
        parts = assignee.strip().split()
        last_name = parts[0] if parts else assignee
        assignee_query = f"assigned_to: {last_name}"

    full_query = search_terms
    if assignee_query:
        full_query = f"{search_terms} {assignee_query}"

    payload = {
        "query": full_query,
        "attributes": ["code", "summary", "workflow_status", "assigned_to"],
        "page": {"page": 0, "size": limit}
    }

    response = await call_api_post("/rest/api/unit/v3/find", payload)
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool(description="Get task history (status and assignee transitions)")
async def get_task_history(
    task_code: str = Field(..., description="Task code like DMS-271")
) -> str:
    """Get task history (status and assignee transitions)"""
    payload = {
        "unit": task_code,
        "filter": {
            "attributes": ["workflow_status", "assigned_to"]
        },
        "sort": "ASC",
        "page": {
            "page": 0,
            "size": 100
        }
    }
    response = await call_api_post("/rest/api/unit/v1/history/find", payload)
    try:
        response_json = response.json()
        return json.dumps(safe_json_dumps(response_json), ensure_ascii=False, indent=2)
    except Exception:
        error_response = {
            "errorType": "SWTR_HISTORY_ERROR",
            "uiErrorMessage": response.text,
            "exceptionUUID": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()