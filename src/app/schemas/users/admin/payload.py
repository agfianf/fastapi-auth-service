from enum import StrEnum

from pydantic import BaseModel, Field, model_validator
from uuid_utils.compat import UUID

from app.schemas.roles.base import UserRole


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
    roles: list[str] | None = Field(default=None, description="Filter by role")
    is_active: bool | None = Field(default=None, description="Filter by active status")
    is_deleted: bool | None = Field(default=None, description="Filter by deleted status")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page (max = 100)")
    sort_by: SortByField = Field(default=SortByField.created_at, description="Field to sort results by")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order (asc/desc)")

    @model_validator(mode="before")
    @classmethod
    def set_empty_fields_to_none(cls, values: dict[str, str]) -> dict[str, str]:
        for key, val in values.items():
            if val == "" or val == [""]:
                values[key] = None
        return values


class UpdateUserByAdminPayload(BaseModel):
    role: UserRole | None = Field(None, examples=[None])
    is_active: bool | None = Field(None, examples=[None])

    @model_validator(mode="before")
    @classmethod
    def preproces_input_data(cls, data: dict) -> dict:  # noqa: ANN102
        for data_key in data:
            if data.get(data_key) == "":
                data[data_key] = None
        return data


class UserServiceMapping(BaseModel):
    service_uuid: UUID = Field(..., description="UUID of the service")
    role_id: int = Field(..., description="ID of the role for this service")
    is_active: bool = Field(True, description="Whether this service mapping is active")


class UpdateUserServicesPayload(BaseModel):
    services: list[UserServiceMapping] = Field(..., description="List of service mappings")
