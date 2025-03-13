from pydantic import BaseModel, Field


class CreateRole(BaseModel):
    name: str = Field(..., description="Name of the role")
    description: str | None = Field(None, description="Description of the role")
    is_active: bool = Field(False, description="Is the role active")

    def transform(self) -> dict:
        return self.model_dump()


class UpdateRole(BaseModel):
    name: str | None = Field(None, description="Name of the role")
    description: str | None = Field(None, description="Description of the role")
    is_active: bool | None = Field(None, description="Is the role active")

    def transform(self) -> dict:
        return self.model_dump(exclude_none=True)


class DeleteRole(BaseModel):
    id: int = Field(..., description="ID of the role")

    def transform(self) -> dict:
        return self.model_dump()
