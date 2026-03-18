"""Shared pagination / response envelope schemas."""
from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=200, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        pages = (total + page_size - 1) // page_size if page_size else 1
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)
