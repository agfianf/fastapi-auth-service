from pydantic import BaseModel

from app.schemas.business_roles.base import BusinessRoleBase


class BusinessRoleResponse(BusinessRoleBase):
    """Response model for business role operations."""

    pass


class CreateBusinessRoleResponse(BusinessRoleResponse):
    """Response model for create business role operation."""

    pass


class UpdateBusinessRoleResponse(BusinessRoleResponse):
    """Response model for update business role operation."""

    pass


class DeleteBusinessRoleResponse(BaseModel):
    """Response model for delete business role operation."""

    success: bool
