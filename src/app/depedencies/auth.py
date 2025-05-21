from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncConnection

from app.depedencies.database import get_async_conn
from app.exceptions.auth import (
    InactiveUserException,
    InsufficientPermissionsException,
    InvalidCredentialsHeaderException,
    InvalidCredentialsSchemeException,
    InvalidTokenException,
    TokenRevokedException,
)
from app.helpers.auth import decode_access_jwt
from app.integrations.redis import RedisHelper
from app.schemas.roles.base import UserRole
from app.schemas.users import UserMembershipQueryReponse
from app.services.member import MemberService


# Constants
AUTH_SCHEME = "Bearer"


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True) -> None:
        super().__init__(auto_error=auto_error)

    async def __call__(
        self,
        request: Request,
        connection: Annotated[AsyncConnection, Depends(get_async_conn)],
    ) -> tuple[UserMembershipQueryReponse, str]:
        credentials = await super().__call__(request)
        redis_helper: RedisHelper = request.state.redis_helper
        member_service: MemberService = request.state.member_service

        if not credentials:
            raise InvalidCredentialsHeaderException()

        if credentials.scheme != AUTH_SCHEME:
            raise InvalidCredentialsSchemeException()

        is_creds_revoked = redis_helper.is_token_revoked(credentials.credentials)

        if is_creds_revoked:
            raise TokenRevokedException()

        token_jwt = credentials.credentials
        decoded_jwt = decode_access_jwt(token_jwt)

        if decoded_jwt is None:
            raise InvalidTokenException()

        user_profile = await member_service.fetch_member_details(
            user_uid=decoded_jwt["sub"],
            connection=connection,
            ignore_error=True,
        )

        if user_profile is None:
            raise InvalidTokenException()

        if not user_profile.is_active:
            raise InactiveUserException()

        return user_profile, credentials.credentials


@lru_cache(maxsize=1)
def get_jwt_bearer_instance() -> JWTBearer:
    return JWTBearer()


jwt_bearer = get_jwt_bearer_instance()


class RoleChecker:
    def __init__(self, required_roles: list[str]):
        self.required_role = required_roles

    async def __call__(
        self,
        jwt_data: Annotated[tuple[UserMembershipQueryReponse, str], Depends(jwt_bearer)],
    ) -> tuple[UserMembershipQueryReponse, str]:
        user_profile, jwt = jwt_data

        if user_profile.role not in self.required_role:
            raise InsufficientPermissionsException()

        return user_profile, jwt


# Dependency injection for role-based permissions
@lru_cache(maxsize=1)
def get_role_superadmin() -> RoleChecker:
    return RoleChecker([UserRole.superadmin])


@lru_cache(maxsize=1)
def get_role_admin() -> RoleChecker:
    return RoleChecker([UserRole.superadmin, UserRole.admin])


@lru_cache(maxsize=1)
def get_role_staff() -> RoleChecker:
    return RoleChecker([UserRole.staff])


@lru_cache(maxsize=1)
def get_role_member() -> RoleChecker:
    return RoleChecker([UserRole.member])


@lru_cache(maxsize=1)
def get_role_guest() -> RoleChecker:
    return RoleChecker([UserRole.guest])


role_superadmin = get_role_superadmin()
role_admin = get_role_admin()
role_staff = get_role_staff()
role_member = get_role_member()
role_guest = get_role_guest()

PERMISSION_SUPERADMIN = Depends(role_superadmin)
PERMISSION_ADMIN = Depends(role_admin)
PERMISSION_STAFF = Depends(role_staff)
PERMISSION_MEMBER = Depends(role_member)
PERMISSION_GUEST = Depends(role_guest)
