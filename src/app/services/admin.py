from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.exceptions.admin import NoUsersFoundException
from app.helpers.response_api import MetaResponse
from app.integrations.redis import RedisHelper
from app.repositories.admin import AdminAsyncRepositories
from app.schemas.users import UserMembershipQueryReponse
from app.schemas.users.admin.payload import GetUsersPayload


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
