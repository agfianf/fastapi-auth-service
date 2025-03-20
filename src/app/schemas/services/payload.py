from pydantic import BaseModel, Field, model_validator

from app.helpers.generator import generate_uuid


class CreateService(BaseModel):
    name: str = Field(..., description="Name of the service")
    location: str | None = Field(None, description="Location of the service")
    description: str | None = Field(None, description="Description of the service")
    is_active: bool = Field(True, description="Whether the service is active")

    def transform(self) -> dict:
        data = self.model_dump()
        data["uuid"] = str(generate_uuid())
        return data


class UpdateService(BaseModel):
    name: str | None = Field(None, description="Name of the service")
    location: str | None = Field(None, description="Location of the service")
    description: str | None = Field(None, description="Description of the service")
    is_active: bool | None = Field(None, description="Whether the service is active")

    @model_validator(mode="before")
    @classmethod
    def preprocess_input_data(cls, data: dict) -> dict:
        for data_key in data:
            if data.get(data_key) == "":
                data[data_key] = None
        return data

    def transform(self) -> dict:
        return self.model_dump(exclude_none=True)


class GetServicesPayload(BaseModel):
    # Filter
    name: str | None = Field(default=None, description="Filter by name")
    is_active: bool | None = Field(default=None, description="Filter by active status")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page (max = 100)")
    sort_by: str = Field(default="created_at", description="Field to sort results by")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")

    @model_validator(mode="before")
    @classmethod
    def set_empty_fields_to_none(cls, values: dict) -> dict:
        for key, val in values.items():
            if val == "" or val == [""]:
                values[key] = None
        return values
