import structlog

from sqlalchemy.ext.asyncio import AsyncConnection

from app.exceptions.roles import (
    RoleCreationFailedException,
    RoleDeletionFailedException,
    RoleNotFoundException,
    RoleUpdateFailedException,
)
from app.helpers.response_api import MetaResponse
from app.integrations.redis import RedisHelper
from app.repositories.roles import RoleAsyncRepositories
from app.schemas.roles.base import RoleBase
from app.schemas.roles.payload import CreateRole, UpdateRole
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import SortOrder


logger = structlog.get_logger(__name__)


class RoleService:
    def __init__(
        self,
        repo_roles: RoleAsyncRepositories,
        redis: RedisHelper,
    ) -> None:
        self.repo_roles = repo_roles
        self.redis = redis

    async def fetch_role_by_id(
        self,
        role_id: int,
        connection: AsyncConnection,
    ) -> RoleBase:
        """Get role by ID."""
        logger.debug("Fetching role by ID")
        role = await self.repo_roles.get_role_by_id(
            connection=connection,
            role_id=role_id,
        )

        if role is None:
            logger.warning("Role not found")
            raise RoleNotFoundException()

        logger.debug("Role fetched successfully")
        return role

    async def fetch_all_roles(
        self,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
        connection: AsyncConnection = None,
    ) -> tuple[list[RoleBase], MetaResponse]:
        """Get all roles with pagination."""
        logger.debug("Fetching all roles")
        roles, meta = await self.repo_roles.get_all_roles(
            connection=connection,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        logger.debug("Roles fetched successfully", role_count=len(roles))
        return roles, meta

    async def create_role(
        self,
        current_user: UserMembershipQueryReponse,
        payload: CreateRole,
        connection: AsyncConnection,
    ) -> RoleBase:
        """Create a new role."""
        logger.debug("Creating new role")
        role = await self.repo_roles.create_role(
            connection=connection,
            payload=payload,
            executed_by=current_user.email,
        )

        if role is None:
            logger.error("Failed to create role")
            raise RoleCreationFailedException()

        logger.debug("Role created successfully")
        return role

    async def update_role(
        self,
        current_user: UserMembershipQueryReponse,
        role_id: int,
        payload: UpdateRole,
        connection: AsyncConnection,
    ) -> RoleBase:
        """Update an existing role."""
        logger.debug("Updating role")
        # Check if role exists

        logger.debug("Role found, proceeding with update")
        updated_role = await self.repo_roles.update_role(
            connection=connection,
            role_id=role_id,
            payload=payload,
            executed_by=current_user.email,
        )

        if updated_role is None:
            logger.error("Failed to update role")
            raise RoleUpdateFailedException()

        logger.debug("Role updated successfully")
        return updated_role

    async def delete_role(
        self,
        current_user: UserMembershipQueryReponse,
        role_id: int,
        connection: AsyncConnection,
    ) -> bool:
        """Delete a role."""
        logger.debug("Deleting role")
        # Check if role exists
        await self.fetch_role_by_id(role_id=role_id, connection=connection)

        logger.debug("Role found, proceeding with deletion")
        success = await self.repo_roles.delete_role(
            connection=connection,
            role_id=role_id,
            executed_by=current_user.email,
        )

        if not success:
            logger.error("Failed to delete role")
            raise RoleDeletionFailedException()

        logger.debug("Role deleted successfully")
        return success
