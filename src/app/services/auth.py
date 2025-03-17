from sqlalchemy.ext.asyncio import AsyncConnection

from app.helpers.generator_jwt import generate_jwt_tokens, generate_temporary_mfa_token
from app.helpers.user_validator import verify_user_password, verify_user_status
from app.integrations.mfa import TwoFactorAuth
from app.integrations.redis import RedisHelper
from app.repositories.auth import AuthAsyncRepositories
from app.schemas.users import (
    CreateUserPayload,
    CreateUserQuery,
    CreateUserQueryResponse,
    SignInPayload,
    UserMembershipQueryReponse,
)
from app.schemas.users.response import SignInResponse


class AuthService:
    def __init__(
        self,
        repo_auth: AuthAsyncRepositories,
        redis: RedisHelper,
    ) -> None:
        self.repo_auth = repo_auth
        self.redis = redis

    async def sign_up(
        self,
        payload: CreateUserPayload,
        connection: AsyncConnection,
    ) -> tuple[CreateUserQueryResponse, str | None]:
        qr_code_bs64 = None
        mfa_secret = None
        if payload.mfa_enabled:
            mfa_secret = TwoFactorAuth.get_secret()
            qr_code_bs64 = TwoFactorAuth.get_provisioning_qrcode_base64(
                username=payload.username,
                secret=mfa_secret,
            )

        query_payload = CreateUserQuery(
            mfa_secret=mfa_secret,
            **payload.model_dump(exclude_none=True),
        )

        user_info = await self.repo_auth.create_user(
            payload=query_payload,
            connection=connection,
        )
        return user_info, qr_code_bs64

    async def sign_in(
        self,
        payload: SignInPayload,
        connection: AsyncConnection,
    ) -> tuple[SignInResponse | None, dict | None]:
        curr_user: UserMembershipQueryReponse | None = await self.repo_auth.get_user_by_username(
            username=payload.username,
            connection=connection,
        )

        verify_user_status(user=curr_user)
        verify_user_password(
            password_input=payload.password.get_secret_value(),
            password_hash=curr_user.password_hash,
        )

        if curr_user.mfa_enabled:
            temp_token = generate_temporary_mfa_token(
                redis=self.redis,
                user_data=curr_user.model_dump(include={"username"}),
                expire_minutes=3,
            )

            signin_response = SignInResponse(
                access_token=None,
                mfa_token=temp_token,
                mfa_required=True,
            )
            return signin_response, None

        access_token, cookies = generate_jwt_tokens(
            user_data=curr_user.transform_jwt(),
            expire_minutes_access=15,
            expire_minutes_refresh=60 * 24,
        )

        signin_response = SignInResponse(
            access_token=access_token,
            mfa_token=None,
            mfa_required=False,
        )

        return signin_response, cookies
