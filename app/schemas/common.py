from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class Envelope(BaseModel, Generic[T]):
    data: T


class PaginatedEnvelope(BaseModel, Generic[T]):
    data: list[T]
    meta: Meta