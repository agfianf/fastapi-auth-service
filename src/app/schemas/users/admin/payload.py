from enum import StrEnum

from pydantic import BaseModel, Field


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class SortByField(StrEnum):
    created_at = "created_at"
    updated_at = "updated_at"


class GetUsersPayload(BaseModel):
    # Filter
    username: str | None = Field(default=None, description="Filter by username")
    email: str | None = Field(default=None, description="Filter by email")
    role_name: list[str] | None = Field(default=None, description="Filter by role")
    is_active: bool | None = Field(default=None, description="Filter by active status")
    is_deleted: bool | None = Field(default=None, description="Filter by deleted status")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page (max = 100)")
    sort_by: SortByField = Field(default=SortByField.created_at, description="Field to sort results by")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order (asc/desc)")
