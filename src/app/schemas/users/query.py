from pydantic import BaseModel, Field
from uuid_utils.compat import UUID

from app.schemas.users.base import UserBase
from app.schemas.users.payload import CreateUserPayload


class CreateUserQuery(CreateUserPayload):
    # transform() already implemented in PayloadUCreateUser2FA

    mfa_secret: str | None = Field(
        None,
        description="MFA secret for the account",
        examples=["JBSWY3DPEHPK3PXP"],
    )


class CreateUserQueryResponse(UserBase):
    password_hash: str | None = Field(None, exclude=True)
    mfa_secret: str | None = Field(None, exclude=True)

    def transform_jwt(self, role: str | None) -> dict:
        """Transform the user object to a JWT token payload."""
        data = self.jwt_data(role=role)
        return data


class UserMembership(BaseModel):
    uuid: UUID = Field(
        ...,
        description="UUID of the user membership",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    name: str = Field(
        ...,
        description="Name of the user membership",
        examples=["Admin"],
    )
    description: str | None = Field(
        None,
        description="Description of the user membership",
        examples=["Administrator role with full access"],
    )
    role: str = Field(
        ...,
        description="Role of the user membership",
        examples=["admin", "user"],
    )
    member_is_active: bool = Field(
        ...,
        description="Is the user membership active",
        examples=[True],
    )
    service_is_active: bool = Field(
        ...,
        description="Is the service active",
        examples=[True],
    )


class UserMembershipQueryReponse(UserBase):
    """Create User Membership Query."""

    password_hash: str | None = Field(None, exclude=True)
    mfa_secret: str | None = Field(None, exclude=True)
    services: list[UserMembership] = Field(
        ...,
        description="List of services for the user membership",
        examples=[
            {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Admin",
                "description": "Administrator role with full access",
                "role": "admin",
                "member_is_active": True,
                "service_is_active": True,
            },
        ],
    )

    def transform_jwt(self) -> dict:
        """Transform the user object to a JWT token payload."""
        data = self.model_dump(
            exclude={
                "password_hash",
                "mfa_secret",
                "deleted_at",
                "deleted_by",
                "role_id",
            },
        )
        data["uuid"] = str(data["uuid"])
        data["created_at"] = str(data["created_at"])
        data["updated_at"] = str(data["updated_at"])
        for service in data["services"]:
            service["uuid"] = str(service["uuid"])

        return data
