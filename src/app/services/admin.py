import structlog

from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.exceptions.admin import (
    AdminCannotUpdateAdminException,
    AdminCannotUpdateSuperAdminException,
    FailedUpdateUserException,
    NoUsersFoundException,
    SuperadminCannotUpdateSuperadminException,
    UpdateUserServicesMappingFailedException,
)
from app.helpers.response_api import MetaResponse
from app.integrations.redis import RedisHelper
from app.repositories.admin import AdminAsyncRepositories
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import GetUsersPayload, UpdateUserByAdminPayload


logger = structlog.get_logger(__name__)


class AdminService:
    def __init__(
        self,
        repo_admin: AdminAsyncRepositories,
        redis: RedisHelper,
    ) -> None:
        self.repo_admin = repo_admin
        self.redis = redis

    async def fetch_user_list(
        self,
        current_user: UserMembershipQueryReponse,
        payload: GetUsersPayload,
        connection: AsyncConnection,
    ) -> tuple[list[UserMembershipQueryReponse], MetaResponse]:
        """List all users."""
        logger.debug("Fetching user list")
        users, metaresponse = await self.repo_admin.get_list_users(
            role=current_user.role,
            payload=payload,
            connection=connection,
        )

        if users is None:
            logger.warning("No users found")
            raise NoUsersFoundException()
        logger.debug("User list fetched successfully", user_count=len(users))
        return users, metaresponse

    async def fetch_user_details(
        self,
        current_user: UserMembershipQueryReponse,
        user_uuid: UUID,
        connection: AsyncConnection,
    ) -> UserMembershipQueryReponse:
        """Get user details."""
        logger.debug("Fetching user details")
        user = await self.repo_admin.get_user_details(
            role=current_user.role,
            user_uuid=user_uuid,
            connection=connection,
        )

        if user is None:
            logger.warning("No user found with the provided UUID")
            raise NoUsersFoundException()
        logger.debug("User details fetched successfully")
        return user

    async def update_user_details(
        self,
        current_user: UserMembershipQueryReponse,
        user_uuid: UUID,
        payload: UpdateUserByAdminPayload,
        connection: AsyncConnection,
    ) -> UserMembershipQueryReponse:
        """Update user details."""
        logger.debug("Updating user details")
        user = await self.repo_admin.get_user_details(
            role=current_user.role,
            user_uuid=user_uuid,
            connection=connection,
        )

        if current_user.role == "superadmin" and payload.role == "superadmin":
            logger.warning("Superadmin cannot update another superadmin")
            raise SuperadminCannotUpdateSuperadminException()

        if current_user.role == "admin" and payload.role == "superadmin":
            logger.warning("Admin cannot update superadmin")
            raise AdminCannotUpdateSuperAdminException()

        if current_user.role == "admin" and payload.role == "admin":
            logger.warning("Admin cannot update another admin")
            raise AdminCannotUpdateAdminException()

        if user is None:
            logger.warning("No user found with the provided UUID")
            raise NoUsersFoundException()

        logger.debug("User found, proceeding with update")
        updated_user = await self.repo_admin.update_user_details(
            role_admin=current_user.role,
            executed_by=current_user.email,
            user_uuid=user_uuid,
            payload=payload,
            connection=connection,
        )

        if updated_user is False:
            logger.error("Failed to update user details")
            raise FailedUpdateUserException()
        logger.debug("User details updated successfully")
        return updated_user

    async def delete_user(
        self,
        current_user: UserMembershipQueryReponse,
        user_uuid: UUID,
        connection: AsyncConnection,
    ) -> bool:
        """Delete user."""
        logger.debug("Deleting user")
        user = await self.repo_admin.get_user_details(
            role=current_user.role,
            user_uuid=user_uuid,
            connection=connection,
        )

        if user is None:
            logger.warning("No user found with the provided UUID")
            raise NoUsersFoundException()

        if current_user.role == "superadmin" and user.role == "superadmin":
            logger.warning("Superadmin cannot delete another superadmin")
            raise SuperadminCannotUpdateSuperadminException()
        if current_user.role == "admin" and user.role == "superadmin":
            logger.warning("Admin cannot delete superadmin")
            raise AdminCannotUpdateSuperAdminException()
        if current_user.role == "admin" and user.role == "admin":
            logger.warning("Admin cannot delete another admin")
            raise AdminCannotUpdateAdminException()

        logger.debug("User found, proceeding with deletion")
        deleted_user = await self.repo_admin.soft_delete_user(
            role_admin=current_user.role,
            executed_by=current_user.email,
            user_uuid=user_uuid,
            connection=connection,
        )

        if deleted_user is False:
            logger.error("Failed to delete user")
            raise FailedUpdateUserException()

        logger.debug("User deleted successfully")
        return deleted_user

    async def update_user_services(
        self,
        current_user: UserMembershipQueryReponse,
        user_uuid: UUID,
        services: list,
        connection: AsyncConnection,
    ) -> bool:
        """Update user service mappings."""
        logger.debug("Updating user service mappings")
        # First, verify the user exists
        user = await self.fetch_user_details(
            current_user=current_user,
            user_uuid=user_uuid,
            connection=connection,
        )

        if not user:
            logger.warning("No user found with the provided UUID")
            raise NoUsersFoundException()

        if current_user.role == "superadmin" and user.role == "superadmin":
            logger.warning("Superadmin cannot update another superadmin")
            raise SuperadminCannotUpdateSuperadminException()
        if current_user.role == "admin" and user.role == "superadmin":
            logger.warning("Admin cannot update superadmin")
            raise AdminCannotUpdateSuperAdminException()
        if current_user.role == "admin" and user.role == "admin":
            logger.warning("Admin cannot update another admin")
            raise AdminCannotUpdateAdminException()

        # Update the service mappings
        logger.debug("User found, proceeding with service mappings update")
        success = await self.repo_admin.update_user_services(
            role_admin=current_user.role,
            executed_by=current_user.email,
            user_uuid=user_uuid,
            services=services,
            connection=connection,
        )

        if not success:
            logger.error("Failed to update user service mappings")
            raise UpdateUserServicesMappingFailedException()

        logger.debug("User service mappings updated successfully")
        return success
