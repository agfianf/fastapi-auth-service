from sqlalchemy.ext.asyncio import AsyncConnection

from app.exceptions.business_roles import (
    BusinessRoleCreationFailedException,
    BusinessRoleDeletionFailedException,
    BusinessRoleNotFoundException,
    BusinessRoleUpdateFailedException,
)
from app.helpers.response_api import MetaResponse
from app.integrations.redis import RedisHelper
from app.repositories.business_roles import BusinessRoleAsyncRepositories
from app.schemas.business_roles.base import BusinessRoleBase
from app.schemas.business_roles.payload import CreateBusinessRole, UpdateBusinessRole
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import SortOrder


class BusinessRoleService:
    def __init__(
        self,
        repo_business_roles: BusinessRoleAsyncRepositories,
        redis: RedisHelper,
    ) -> None:
        self.repo_business_roles = repo_business_roles
        self.redis = redis

    async def fetch_business_role_by_id(
        self,
        business_role_id: int,
        connection: AsyncConnection,
    ) -> BusinessRoleBase:
        """Get business role by ID."""
        business_role = await self.repo_business_roles.get_business_role_by_id(
            connection=connection,
            business_role_id=business_role_id,
        )

        if business_role is None:
            raise BusinessRoleNotFoundException()

        return business_role

    async def fetch_all_business_roles(
        self,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
        connection: AsyncConnection = None,
    ) -> tuple[list[BusinessRoleBase], MetaResponse]:
        """Get all business roles with pagination."""
        business_roles, meta = await self.repo_business_roles.get_all_business_roles(
            connection=connection,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return business_roles, meta

    async def create_business_role(
        self,
        current_user: UserMembershipQueryReponse,
        payload: CreateBusinessRole,
        connection: AsyncConnection,
    ) -> BusinessRoleBase:
        """Create a new business role."""
        business_role = await self.repo_business_roles.create_business_role(
            connection=connection,
            payload=payload,
            executed_by=current_user.email,
        )

        if business_role is None:
            raise BusinessRoleCreationFailedException()

        return business_role

    async def update_business_role(
        self,
        current_user: UserMembershipQueryReponse,
        business_role_id: int,
        payload: UpdateBusinessRole,
        connection: AsyncConnection,
    ) -> BusinessRoleBase:
        """Update an existing business role."""
        # Check if business role exists
        await self.fetch_business_role_by_id(business_role_id=business_role_id, connection=connection)

        updated_business_role = await self.repo_business_roles.update_business_role(
            connection=connection,
            business_role_id=business_role_id,
            payload=payload,
            executed_by=current_user.email,
        )

        if updated_business_role is None:
            raise BusinessRoleUpdateFailedException()

        return updated_business_role

    async def delete_business_role(
        self,
        business_role_id: int,
        connection: AsyncConnection,
    ) -> bool:
        """Delete a business role."""
        # Check if business role exists
        await self.fetch_business_role_by_id(business_role_id=business_role_id, connection=connection)

        success = await self.repo_business_roles.delete_business_role(
            connection=connection,
            business_role_id=business_role_id,
        )

        if not success:
            raise BusinessRoleDeletionFailedException()

        return success
