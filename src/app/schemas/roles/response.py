from pydantic import BaseModel

from app.schemas.roles.base import RoleBase


class RoleResponse(RoleBase):
    """Response model for role operations."""

    pass


class CreateRoleResponse(RoleResponse):
    """Response model for create role operation."""

    pass


class UpdateRoleResponse(RoleResponse):
    """Response model for update role operation."""

    pass


class DeleteRoleResponse(BaseModel):
    """Response model for delete role operation."""

    success: bool
