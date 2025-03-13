from sqlalchemy.ext.asyncio import AsyncConnection
from src.integrations.mfa import TwoFactorAuth
from src.repositories.auth import AuthAsyncRepositories
from src.schemas.users import (
    CreateUserPayload,
    CreateUserQuery,
    CreateUserQueryResponse,
)


class AuthService:
    def __init__(
        self,
        repo_auth: AuthAsyncRepositories,
    ) -> None:
        self.repo_auth = repo_auth

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
