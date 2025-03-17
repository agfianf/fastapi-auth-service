from pydantic import BaseModel, Field
from uuid_utils.compat import UUID

from app.schemas._default_base import BaseAudit


class ServicesBase(BaseModel, BaseAudit):
    uuid: UUID = Field(..., description="UUID of the service")
    name: str = Field(..., description="Name of the service")
    location: str | None = Field(None, description="Location of the service")
    description: str | None = Field(None, description="Description of the service")
    is_active: bool = Field(False, description="Is the service active")


class ServiceMembershipBase(BaseModel, BaseAudit):
    id: int = Field(..., description="ID of the user service")
    user_uuid: UUID = Field(..., description="UUID of the user")
    service_uuid: UUID = Field(..., description="UUID of the service")
    role_id: int = Field(..., description="ID of the role")
