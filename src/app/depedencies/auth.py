from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPBearer

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
from app.schemas.users import UserMembershipQueryReponse


# Constants
AUTH_SCHEME = "Bearer"


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True) -> None:
        super().__init__(auto_error=auto_error)

    async def __call__(
        self,
        request: Request,
    ) -> tuple[UserMembershipQueryReponse, str]:
        credentials = await super().__call__(request)
        redis_helper: RedisHelper = request.state.redis_helper

        if not credentials:
            raise InvalidCredentialsHeaderException()

        if credentials.scheme != AUTH_SCHEME:
            raise InvalidCredentialsSchemeException()

        token_jwt = credentials.credentials
        user_profile = decode_access_jwt(token_jwt)

        if user_profile is None:
            raise InvalidTokenException()

        is_creds_revoked = redis_helper.is_token_revoked(credentials.credentials)
        if is_creds_revoked:
            raise TokenRevokedException()

        print(user_profile)
        user_profile = UserMembershipQueryReponse(**user_profile)

        if not user_profile.is_active:
            raise InactiveUserException()

        return user_profile, credentials.credentials


class RoleChecker:
    def __init__(self, allowed_roles: list) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(  # noqa: D102
        self,
        request: Request,
        user_profile: Annotated[UserMembershipQueryReponse, Depends(JWTBearer())],
    ) -> UserMembershipQueryReponse:
        if user_profile.role in self.allowed_roles:
            request.state.current_user = user_profile
            return user_profile
        raise InsufficientPermissionsException()
