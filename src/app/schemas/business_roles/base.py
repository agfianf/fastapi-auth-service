from enum import StrEnum

from pydantic import Field

from app.schemas._default_base import BaseAudit


class BusinessRole(StrEnum):
    admin = "admin"
    manager = "manager"
    member = "member"
    guest = "guest"


class BusinessRoleBase(BaseAudit):
    id: int = Field(..., description="ID of the business role")
    name: str = Field(..., description="Name of the business role")
    description: str | None = Field(
        None,
        description="Description of the business role",
    )
