from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.exceptions.admin import (
    AdminCannotUpdateAdminException,
    AdminCannotUpdateSuperAdminException,
    FailedUpdateUserException,
    NoUsersFoundException,
    SuperadminCannotUpdateSuperadminException,
)
from app.helpers.response_api import MetaResponse
from app.integrations.redis import RedisHelper
from app.repositories.admin import AdminAsyncRepositories
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import GetUsersPayload, UpdateUserByAdminPayload


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
        users, metaresponse = await self.repo_admin.get_list_users(
            role=current_user.role,
            payload=payload,
            connection=connection,
        )

        if users is None:
            raise NoUsersFoundException()
        return users, metaresponse

    async def fetch_user_details(
        self,
        current_user: UserMembershipQueryReponse,
        user_uuid: UUID,
        connection: AsyncConnection,
    ) -> UserMembershipQueryReponse:
        """Get user details."""
        user = await self.repo_admin.get_user_details(
            role=current_user.role,
            user_uuid=user_uuid,
            connection=connection,
        )

        if user is None:
            raise NoUsersFoundException()
        return user

    async def update_user_details(
        self,
        current_user: UserMembershipQueryReponse,
        user_uuid: UUID,
        payload: UpdateUserByAdminPayload,
        connection: AsyncConnection,
    ) -> UserMembershipQueryReponse:
        """Update user details."""
        user = await self.repo_admin.get_user_details(
            role=current_user.role,
            user_uuid=user_uuid,
            connection=connection,
        )

        if current_user.role == "superadmin" and payload.role == "superadmin":
            raise SuperadminCannotUpdateSuperadminException()

        if current_user.role == "admin" and payload.role == "superadmin":
            raise AdminCannotUpdateSuperAdminException()

        if current_user.role == "admin" and payload.role == "admin":
            raise AdminCannotUpdateAdminException()

        if user is None:
            raise NoUsersFoundException()

        updated_user = await self.repo_admin.update_user_details(
            role_admin=current_user.role,
            executed_by=current_user.email,
            user_uuid=user_uuid,
            payload=payload,
            connection=connection,
        )

        if updated_user is False:
            raise FailedUpdateUserException()
        return updated_user

    async def delete_user(
        self,
        current_user: UserMembershipQueryReponse,
        user_uuid: UUID,
        connection: AsyncConnection,
    ) -> bool:
        """Delete user."""
        user = await self.repo_admin.get_user_details(
            role=current_user.role,
            user_uuid=user_uuid,
            connection=connection,
        )

        if user is None:
            raise NoUsersFoundException()

        if current_user.role == "superadmin" and user.role == "superadmin":
            raise SuperadminCannotUpdateSuperadminException()
        if current_user.role == "admin" and user.role == "superadmin":
            raise AdminCannotUpdateSuperAdminException()
        if current_user.role == "admin" and user.role == "admin":
            raise AdminCannotUpdateAdminException()

        deleted_user = await self.repo_admin.soft_delete_user(
            role_admin=current_user.role,
            executed_by=current_user.email,
            user_uuid=user_uuid,
            connection=connection,
        )

        if deleted_user is False:
            raise FailedUpdateUserException()

        return deleted_user
