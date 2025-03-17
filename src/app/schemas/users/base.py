from pydantic import EmailStr, Field
from uuid_utils.compat import UUID

from app.schemas._default_base import BaseAudit


class UserBase(BaseAudit):
    uuid: UUID = Field(..., description="UUIDv7 of the service")
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
    mfa_enabled: bool = Field(False, description="Is MFA enabled")
    mfa_secret: str | None = Field(None, description="MFA secret of the user")

    def jwt_data(self, role: str | None) -> dict:
        """Transform the user object to a JWT token payload."""
        return {
            "uuid": str(self.uuid),
            "role": role,
            "username": self.username,
            "firstname": self.firstname,
            "midname": self.midname,
            "lastname": self.lastname,
            "email": self.email,
            "phone": self.phone,
            "telegram": self.telegram,
            "is_active": self.is_active,
            "mfa_enabled": self.mfa_enabled,
        }
