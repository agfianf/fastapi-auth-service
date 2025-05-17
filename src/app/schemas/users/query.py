from pydantic import BaseModel, Field

from app.schemas.users.base import UserBase
from app.schemas.users.payload import CreateUserPayload


class CreateUserQuery(CreateUserPayload):
    service_uuid: str | None = Field(
        default=None,
        description="Service UUID",
    )

    service_role: str | None = Field(
        default=None,
        description="Role key",
    )


class CreateUserQueryResponse(UserBase):
    service_uuid: str | None = Field(
        default=None,
        description="Service UUID",
    )

    def transform_jwt(self, role: str | None) -> dict:
        data = self.model_dump()
        data["uuid"] = str(data["uuid"])
        return data


class UserMembership(BaseModel):
    member_uuid: str = Field(
        title="User UUID",
        description="User UUID",
    )
    service_uuid: str = Field(
        title="Service UUID",
        description="Service UUID",
    )
    role: str = Field(
        title="Role",
        description="Role key",
    )
    service_is_active: bool = Field(
        default=True,
        title="Service Status",
        description="Service active status",
    )
    member_is_active: bool = Field(
        default=True,
        title="Member Status",
        description="Member service active status",
    )


class UserMembershipQueryReponse(UserBase):
    role: str = Field(
        title="Role",
        description="Role key",
    )
    services: list[UserMembership] = Field(
        default=[],
        title="Services",
        description="List of services",
    )

    def transform_jwt(self) -> dict:
        """Transform the user object to a JWT token payload.

        Only includes minimal information needed for authentication:
        - UUID
        - Role
        - Services with their roles
        """
        # Only include minimal information in JWT
        data = {
            "uuid": str(self.uuid),
            "role": self.role,
            "sub": self.username,  # Keep 'sub' for JWT standard compliance
        }

        # Include only service UUIDs and roles
        services_data = []
        for service in self.services:
            services_data.append({
                "uuid": str(service["uuid"]),
                "role": service["role"],
            })

        data["services"] = services_data

        return data