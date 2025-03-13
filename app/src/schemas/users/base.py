from pydantic import BaseModel, EmailStr, Field
from src.schemas._default_base import BaseAudit
from uuid_utils.compat import UUID


class UserBase(BaseModel, BaseAudit):
    uuid: UUID = Field(..., description="UUID of the service")
    role_id: int | None = Field(None, description="ID of the role")
    username: str = Field(..., description="Username of the user")
    firstname: str = Field(..., description="Firstname of the user")
    midname: str | None = Field(None, description="Midname of the user")
    lastname: str | None = Field(None, description="Lastname of the user")
    email: EmailStr = Field(..., description="Email of the user")
    phone: str | None = Field(None, description="Phone of the user")
    telegram: str | None = Field(None, description="Telegram of the user")
    password_hash: str = Field(..., description="Password hash of the user")
    is_active: bool = Field(False, description="Is the user active")
