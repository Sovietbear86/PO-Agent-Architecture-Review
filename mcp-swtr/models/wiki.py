from enum import Enum
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field, ConfigDict

from models.common import BasePageSizeRequest


class MarkType(str, Enum):
    BOLD = "bold"
    LINK = "link"
    CODE = "code"
    SUPERSCRIPT = "superscript"
    TEXT_STYLE = "textStyle"
    ITALIC = "italic"


class TextAlign(str, Enum):
    JUSTIFY = "justify"


class MarkAttrs(BaseModel):
    href: Optional[str] = None
    target: Optional[str] = None
    rel: Optional[str] = None
    class_: Optional[str] = Field(None, alias="class")
    color: Optional[str] = ""


class Mark(BaseModel):
    type: MarkType
    attrs: Optional[MarkAttrs] = None


class TextNode(BaseModel):
    type: str = "text"
    text: str
    marks: Optional[List[Mark]] = None


class Attrs(BaseModel):
    id: Optional[str] = None
    indent: Optional[int] = 0
    textAlign: Optional[TextAlign] = None
    level: Optional[int] = None
    colspan: Optional[int] = None
    rowspan: Optional[int] = None
    colwidth: Optional[List[int]] = None
    backgroundColor: Optional[Dict[str, Any]] = None


class ContentNode(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    type: str
    attrs: Optional[Attrs] = None
    content: Optional[List[Union['ContentNode', TextNode]]] = None


class ListItem(BaseModel):
    type: str = "listItem"
    content: List[ContentNode] = Field(...)


class ParagraphItem(BaseModel):
    type: str = "paragraph",
    attrs: Optional[Attrs] = None
    content: List[ContentNode] = Field(...)


class BulletList(BaseModel):
    type: str = "bulletList"
    attrs: Optional[Attrs] = None
    content: List[ListItem] = Field(...)


class TableCell(BaseModel):
    type: str = "tableCell"
    attrs: Optional[Attrs] = None
    content: List[ContentNode] = Field(...)


class TableRow(BaseModel):
    type: str = "tableRow"
    content: List[TableCell] = Field(...)


class Table(BaseModel):
    type: str = "table"
    attrs: Optional[Attrs] = None
    content: List[TableRow] = Field(...)


# Обновляем forward references для рекурсивных моделей
ContentNode.model_rebuild()


class PageContent(BaseModel):
    type: str = "doc"
    content: List[Union[
        ContentNode,
        BulletList,
        ParagraphItem,
        Table,
        TextNode
    ]] = Field(..., description="Содержимое страницы")


class SafePageContent(BaseModel):
    """Безопасная версия PageContent для сериализации без циклических ссылок"""
    type: str = "doc"
    content: List[Dict[str, Any]] = Field(..., description="Содержимое страницы")
    
    @classmethod
    def from_page_content(cls, page_content: PageContent) -> 'SafePageContent':
        """Конвертирует PageContent в SafePageContent для безопасной сериализации"""
        def serialize_node(node) -> Dict[str, Any]:
            if isinstance(node, dict):
                return node
            result = {'type': getattr(node, 'type', None)}
            if hasattr(node, 'attrs') and node.attrs:
                result['attrs'] = node.attrs.model_dump(exclude_none=True) if hasattr(node.attrs, 'model_dump') else node.attrs
            if hasattr(node, 'content') and node.content:
                result['content'] = [serialize_node(child) for child in node.content]
            if hasattr(node, 'text') and node.text:
                result['text'] = node.text
            if hasattr(node, 'marks') and node.marks:
                result['marks'] = [m.model_dump(exclude_none=True) if hasattr(m, 'model_dump') else m for m in node.marks]
            return {k: v for k, v in result.items() if v is not None}
        
        return cls(
            type=page_content.type,
            content=[serialize_node(item) for item in page_content.content]
        )


class WikiSearchRequest(BasePageSizeRequest):
    spaces: List[str] = Field(..., description="Список пространств")
    units: List[str] = Field(..., description="Список юнитов")
    text_search: Optional[str] = Field(None, description="Текст для поиска")


class WikiPageCreateRequest(BaseModel):
    space_code: str = Field(..., description="Код пространства")
    title: str = Field(..., description="Заголовок страницы")
    description: str = Field("", description="Описание страницы")
    labels: List[str] = Field([], description="Список меток")
    content: PageContent = Field(..., description="Содержание страницы")
