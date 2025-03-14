from pydantic import BaseModel, Field

from app.schemas._default_base import BaseAudit


class RoleBase(BaseModel, BaseAudit):
    id: int = Field(..., description="ID of the role")
    name: str = Field(..., description="Name of the role")
    description: str | None = Field(
        None,
        description="Description of the role",
    )
