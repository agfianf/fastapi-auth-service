from typing import Generic

from fastapi import status
from pydantic import BaseModel
from typing_extensions import TypeVar


class MetaResponse(BaseModel):
    current_page: int | None
    page_size: int | None
    prev_page: bool | None
    next_page: bool | None
    total_pages: int | None
    total_items: int | None


T = TypeVar("T")
M = TypeVar("M", bound=MetaResponse | None)


class JsonResponse(BaseModel, Generic[T, M]):
    data: T = None
    message: str = None
    success: bool = True
    meta: M = None
    status_code: int = status.HTTP_200_OK
