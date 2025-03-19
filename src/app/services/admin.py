from sqlalchemy.ext.asyncio import AsyncConnection

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
            role=current_user.role_name,
            payload=payload,
            connection=connection,
        )

        if users is None:
            raise NoUsersFoundException()
        return users, metaresponse
