import time

import structlog

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils import UUID

from app.config import settings
from app.exceptions.auth import (
    AlreadySignedOutException,
    InactiveUserException,
    InvalidTokenException,
    RefreshTokenNotFoundException,
    ServiceInactiveUserException,
    SessionExpiredException,
    TokenRevokedException,
    UserNotRegisteredOnTargetedService,
)
from app.helpers.auth import create_access_token, decode_access_jwt, decode_refresh_jwt
from app.helpers.generator_jwt import generate_delete_refresh_cookies, generate_jwt_tokens, generate_temporary_mfa_token
from app.helpers.user_validator import verify_mfa_credentials, verify_user_password, verify_user_status
from app.integrations.mfa import TwoFactorAuth
from app.integrations.redis import RedisHelper
from app.repositories.auth import AuthAsyncRepositories
from app.repositories.member import MemberAsyncRepositories
from app.schemas.users import (
    CreateUserPayload,
    CreateUserQuery,
    CreateUserQueryResponse,
    SignInPayload,
    SignInResponse,
    UserMembershipQueryReponse,
    UserTokenVerifyResponse,
    VerifyMFAResponse,
)
from app.schemas.users.response import AccessTokenResponse


logger = structlog.get_logger(__name__)


class AuthService:
    def __init__(
        self,
        repo_auth: AuthAsyncRepositories,
        repo_member: MemberAsyncRepositories,
        redis: RedisHelper,
    ) -> None:
        self.repo_auth = repo_auth
        self.repo_member = repo_member
        self.redis = redis

    async def verify_token(  # noqa: C901
        self,
        token: str,
        service_id: UUID,
        connection: AsyncConnection,
    ) -> UserTokenVerifyResponse:
        """Verify the token and return a success message."""
        is_creds_revoked = self.redis.is_token_revoked(token)

        if is_creds_revoked:
            logger.warning("Token revoked in Redis", jwt=token, service_id=service_id)
            raise TokenRevokedException()

        key_user_details = f"jwt_verify:{token}:{service_id}"
        self.redis.get_data(key_user_details)

        # 1. Verify token is valid
        decoded_jwt = decode_access_jwt(token=token)
        if decoded_jwt is None:
            logger.warning("Invalid JWT token", jwt=token, service_id=service_id)
            raise InvalidTokenException()

        user_uuid = decoded_jwt.get("sub")
        user_profile: UserMembershipQueryReponse = await self.repo_member.get_member_by_uuid(
            member_uuid=user_uuid,
            connection=connection,
        )
        if user_profile is None:
            logger.warning("User not found", jwt=token, service_id=str(service_id))
            raise InvalidTokenException()

        # 2. Check is user is active
        if not user_profile.is_active:
            logger.warning("Inactive user", jwt=token, service_id=str(service_id))
            raise InactiveUserException()

        is_registered_service = False
        service_user_role = None
        service_user_status = None
        service_name = None

        for service_user in user_profile.services:
            if is_registered_service:
                break
            if str(service_user.uuid) == str(service_id):
                if service_user.service_is_active is False:
                    raise InactiveUserException()
                is_registered_service = True
                service_user_role = service_user.role
                service_user_status = service_user.member_is_active
                service_name = service_user.name

        # 3. Check if user is registered on the targeted service
        if not is_registered_service:
            logger.warning(
                "User not registered on targeted service",
                jwt=token,
                service_id=str(service_id),
                user_uuid=str(user_uuid),
            )
            raise UserNotRegisteredOnTargetedService()

        # 4. Check if user is active on the targeted service
        if service_user_status is False:
            logger.warning(
                "User is inactive on the targeted service",
                jwt=token,
                service_id=str(service_id),
                user_uuid=str(user_uuid),
            )
            raise ServiceInactiveUserException()

        # ! until here, all verification is done and user is valid
        data = {
            "uuid": user_profile.uuid,
            "username": user_profile.username,
            "email": user_profile.email,
            "firstname": user_profile.firstname,
            "midname": user_profile.midname,
            "lastname": user_profile.lastname,
            "phone": user_profile.phone,
            "telegram": user_profile.telegram,
            "role": user_profile.role,
            "is_active": user_profile.is_active,
            "mfa_enabled": user_profile.mfa_enabled,
            "service_id": service_id,
            "service_valid": is_registered_service,
            "service_name": service_name,
            "service_role": service_user_role,
            "service_status": service_user_status,
        }

        time_now = time.time()
        expire_time = int(decoded_jwt.get("exp", 0) - time_now)

        result = UserTokenVerifyResponse(**data)

        self.redis.set_data(
            key=key_user_details,
            value=result.to_redis_dict(),
            expire_sec=expire_time,
        )
        logger.debug("Token verified successfully")
        return result

    async def sign_up(
        self,
        payload: CreateUserPayload,
        connection: AsyncConnection,
    ) -> tuple[CreateUserQueryResponse, str | None]:
        qr_code_bs64 = None
        mfa_secret = None
        if payload.mfa_enabled:
            logger.debug("MFA is enabled for user registration")
            mfa_secret = TwoFactorAuth.get_secret()
            qr_code_bs64 = TwoFactorAuth.get_provisioning_qrcode_base64(
                username=payload.username,
                secret=mfa_secret,
            )

        query_payload = CreateUserQuery(
            mfa_secret=mfa_secret,
            **payload.model_dump(exclude_none=True),
        )

        logger.debug("Creating user with payload", payload=query_payload.model_dump(mode="json"))
        user_info = await self.repo_auth.create_user(
            payload=query_payload,
            connection=connection,
        )
        logger.debug("User created successfully", user_id=str(user_info.uuid))
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
            logger.debug("MFA is enabled for user")
            temp_token = generate_temporary_mfa_token(
                redis=self.redis,
                user_data=curr_user.transform_jwt_v2(),
                expire_minutes=3,
                username=curr_user.username,
            )

            signin_response = SignInResponse(
                access_token=None,
                mfa_token=temp_token,
                mfa_required=True,
            )
            logger.debug("MFA token generated for user")
            return signin_response, None

        access_token, cookies = generate_jwt_tokens(
            user_data=curr_user.transform_jwt_v2(),
            expire_minutes_access=settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
            expire_minutes_refresh=settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES,
        )

        signin_response = SignInResponse(
            access_token=access_token,
            mfa_token=None,
            mfa_required=False,
        )
        logger.debug("User signed in successfully", user_id=str(curr_user.uuid))
        return signin_response, cookies

    async def sign_out(
        self,
        access_token: str,
        refresh_token_app: str,
    ) -> tuple[dict, dict]:
        if refresh_token_app is None or len(refresh_token_app) == 0:
            logger.warning("Refresh token not found or empty")
            raise RefreshTokenNotFoundException()

        data_access = decode_access_jwt(token=access_token)
        data_refresh = decode_refresh_jwt(token=refresh_token_app)

        if data_access is None or data_refresh is None:
            logger.warning("User is not signed in or token is invalid")
            raise AlreadySignedOutException()

        timenow = time.time()
        expiry_access_sec = int(data_access.get("exp", 0) - timenow)
        expiry_refresh_sec = int(data_refresh.get("exp", 0) - timenow)

        is_access_token_revoked = self.redis.is_token_revoked(token=access_token)
        is_refresh_token_revoked = self.redis.is_token_revoked(token=refresh_token_app)

        if is_access_token_revoked is False:
            logger.debug("Revoking access token")
            self.redis.add_token_to_blacklist(
                token=access_token,
                expire_sec=expiry_access_sec,
            )

        if is_refresh_token_revoked is False:
            logger.debug("Revoking refresh token")
            self.redis.add_token_to_blacklist(
                token=refresh_token_app,
                expire_sec=expiry_refresh_sec,
            )

        if is_access_token_revoked and is_refresh_token_revoked:
            logger.warning("Session has already been logged out")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=("Session has already been logged out. Please login again."),
            )

        delete_cookie = generate_delete_refresh_cookies()

        logger.debug("User signed out successfully")
        return {
            "access_token_revoked": True,
            "refresh_token_revoked": True,
        }, delete_cookie

    async def verify_mfa(
        self,
        mfa_token: str,
        mfa_code: str,
        username: str,
        connection: AsyncConnection,
    ) -> VerifyMFAResponse:
        """Verify MFA credentials and return access token."""
        logger.debug("Verifying MFA credentials for user")
        user: UserMembershipQueryReponse | None = await self.repo_auth.get_user_by_username(
            username=username,
            connection=connection,
        )
        verify_user_status(user=user)
        verify_mfa_credentials(
            redis=self.redis,
            mfa_token=mfa_token,
            mfa_code=mfa_code,
            user=user,
        )
        access_token, cookies = generate_jwt_tokens(
            user_data=user.transform_jwt_v2(),
            expire_minutes_access=settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
            expire_minutes_refresh=settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES,
        )
        logger.debug("MFA credentials verified successfully", user_id=str(user.uuid))
        return VerifyMFAResponse(access_token=access_token), cookies

    async def refresh_token(
        self,
        refresh_token_app: str | None,
    ) -> AccessTokenResponse:
        # check refresh token
        if refresh_token_app is None:
            raise RefreshTokenNotFoundException()

        is_revoked = self.redis.is_token_revoked(token=refresh_token_app)
        if is_revoked:
            logger.warning("Refresh token has been revoked")
            raise SessionExpiredException()

        # check refresh token
        data_user = decode_refresh_jwt(token=refresh_token_app)
        if data_user is None:
            logger.warning("Invalid or expired refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token. Please login again.",
            )
        extend_time = 60 * settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES
        data_user.update({"exp": time.time() + extend_time})
        access_token = create_access_token(data=data_user)
        logger.debug("Access token refreshed successfully", user_id=data_user.get("sub"))
        return AccessTokenResponse(access_token=access_token)
