import structlog

from sqlalchemy.ext.asyncio import AsyncConnection
from uuid_utils.compat import UUID

from app.config import settings
from app.exceptions.member import (
    InvalidCurrentPasswordException,
    MemberNotFoundException,
    MFACodeInvalidException,
    MFANotEnabledException,
    MFAUpdateFailedException,
    PasswordUpdateFailedException,
)
from app.helpers.auth import get_password_hash, verify_password
from app.helpers.generator_jwt import generate_jwt_tokens
from app.helpers.password_validator import PasswordValidate
from app.integrations.mfa import TwoFactorAuth
from app.integrations.redis import RedisHelper
from app.repositories.member import MemberAsyncRepositories
from app.schemas.member.payload import UpdateMemberPayload, UpdateMFAPayload, UpdatePasswordPayload
from app.schemas.member.response import MFAQRCodeResponse, UpdateMemberMFAResponse, UpdateMemberResponse
from app.schemas.users import UserMembershipQueryReponse


logger = structlog.get_logger(__name__)


class MemberService:
    def __init__(
        self,
        repo_member: MemberAsyncRepositories,
        redis: RedisHelper,
    ) -> None:
        self.repo_member = repo_member
        self.redis = redis

    async def fetch_member_details(
        self,
        user_uid: UUID,
        connection: AsyncConnection,
        ignore_error: bool = False,
    ) -> UserMembershipQueryReponse:
        """Get member details."""
        logger.debug("Fetching member details")
        user_cache_key = f"member:{str(user_uid)}"
        data_cache = self.redis.get_data(user_cache_key)

        if data_cache is not None:
            logger.debug("Member details fetched from cache")
            return UserMembershipQueryReponse(**data_cache)

        member = await self.repo_member.get_member_by_uuid(
            connection=connection,
            member_uuid=user_uid,
        )

        if member is None:
            if ignore_error:
                logger.debug("Member not found, returning None")
                return None
            logger.warning("Member not found")
            raise MemberNotFoundException()

        self.redis.set_data(
            key=user_cache_key,
            value=member.to_redis_dict(),
            expire_sec=3600,  # 1 hour
        )

        logger.debug("Member details fetched successfully")
        return member

    async def update_password(
        self,
        current_user: UserMembershipQueryReponse,
        payload: UpdatePasswordPayload,
        access_token: str,
        refresh_token: str,
        connection: AsyncConnection,
    ) -> tuple[UpdateMemberResponse, str]:
        """Update member password."""
        logger.debug("Updating member password")
        # Get the current member details
        member = await self.fetch_member_details(
            current_user=current_user,
            connection=connection,
        )

        # Verify current password
        is_verified = verify_password(
            plain_password=payload.current_password.get_secret_value(),
            hashed_password=member.password_hash,
        )

        if not is_verified:
            logger.warning("Invalid current password provided")
            raise InvalidCurrentPasswordException()

        # Check if new password is not too similar to username
        is_valid, ls_msgs = PasswordValidate.validate_password(
            username=member.username,
            pwd=payload.new_password.get_secret_value(),
            conf_pwd=payload.new_password_confirm.get_secret_value(),
        )

        if not is_valid:
            logger.warning("Password validation failed")
            raise PasswordUpdateFailedException(ls_msgs)

        if payload.new_password.get_secret_value() == payload.current_password.get_secret_value():
            logger.warning("New password cannot be the same as current password")
            raise PasswordUpdateFailedException(["New password cannot be the same as the current password"])

        # Generate new password hash
        new_password_hash = get_password_hash(payload.new_password.get_secret_value())

        # Update password in database
        logger.debug("Updating password in database")
        success = await self.repo_member.update_member_password(
            connection=connection,
            member_uuid=member.uuid,
            password_hash=new_password_hash,
            executed_by=member.email,
        )

        if not success:
            logger.error("Failed to update password")
            raise PasswordUpdateFailedException()

        # Revoke old tokens
        self._revoke_tokens(access_token, refresh_token)

        # Get updated member details
        updated_member = await self.fetch_member_details(
            current_user=current_user,
            connection=connection,
        )

        # Generate new tokens
        new_access_token, cookies = generate_jwt_tokens(
            user_data=updated_member.transform_jwt_v2(),
            expire_minutes_access=settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
            expire_minutes_refresh=settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES,
        )

        logger.debug("Password updated successfully")
        return UpdateMemberResponse(
            access_token=new_access_token,
            user=updated_member,
        ), cookies

    async def update_mfa(
        self,
        current_user: UserMembershipQueryReponse,
        payload: UpdateMFAPayload,
        access_token: str,
        refresh_token: str,
        connection: AsyncConnection,
    ) -> tuple[UpdateMemberMFAResponse, dict]:
        """Update member MFA settings."""
        logger.debug("Updating member MFA settings")
        # Get the current member details
        member = await self.fetch_member_details(
            current_user=current_user,
            connection=connection,
        )

        # If enabling MFA
        mfa_secret = None
        qr_code_bs64 = None
        if payload.mfa_enabled and not member.mfa_enabled:
            logger.debug("Enabling MFA for member")
            mfa_secret = TwoFactorAuth.get_secret()
            qr_code_bs64 = TwoFactorAuth.get_provisioning_qrcode_base64(
                username=current_user.username,
                secret=mfa_secret,
            )

        # If disabling MFA, we need to verify the MFA code
        if member.mfa_enabled and not payload.mfa_enabled:
            logger.debug("Disabling MFA for member")
            # If disabling MFA, verify the MFA code
            if not payload.mfa_code:
                logger.warning("MFA code required for disabling MFA")
                raise MFACodeInvalidException()

            is_verified = TwoFactorAuth.verify_token(
                secret=member.mfa_secret,
                token=payload.mfa_code,
            )

            if not is_verified:
                logger.warning("Invalid MFA code provided")
                raise MFACodeInvalidException()

        # Update MFA settings in database
        logger.debug("Updating MFA settings in database")
        success = await self.repo_member.update_member_mfa(
            connection=connection,
            member_uuid=member.uuid,
            mfa_enabled=payload.mfa_enabled,
            mfa_secret=mfa_secret,
            executed_by=member.email,
        )

        if not success:
            logger.error("Failed to update MFA settings")
            raise MFAUpdateFailedException()

        # Revoke old tokens
        self._revoke_tokens(access_token, refresh_token)

        # Get updated member details
        updated_member = await self.fetch_member_details(
            current_user=current_user,
            connection=connection,
        )

        # Generate new tokens
        new_access_token, cookies = generate_jwt_tokens(
            user_data=updated_member.transform_jwt_v2(),
            expire_minutes_access=settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
            expire_minutes_refresh=settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES,
        )

        logger.debug("MFA settings updated successfully")
        return UpdateMemberMFAResponse(
            access_token=new_access_token,
            user=updated_member,
            qr_code_bs64=qr_code_bs64,
        ), cookies

    async def update_profile(
        self,
        current_user: UserMembershipQueryReponse,
        payload: UpdateMemberPayload,
        access_token: str,
        refresh_token: str,
        connection: AsyncConnection,
    ) -> tuple[UpdateMemberResponse, str]:
        """Update member profile."""
        logger.debug("Updating member profile")
        # Update profile in database
        updated_member = await self.repo_member.update_member_profile(
            connection=connection,
            member_uuid=current_user.uuid,
            payload=payload,
            executed_by=current_user.email,
        )

        if updated_member is None:
            logger.error("Failed to update member profile")
            raise MemberNotFoundException()

        # Revoke old tokens
        self._revoke_tokens(access_token, refresh_token)

        # Generate new tokens
        new_access_token, cookies = generate_jwt_tokens(
            user_data=updated_member.transform_jwt_v2(),
            expire_minutes_access=settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
            expire_minutes_refresh=settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES,
        )

        logger.debug("Member profile updated successfully")
        return UpdateMemberResponse(
            access_token=new_access_token,
            user=updated_member,
        ), cookies

    async def get_mfa_qrcode(
        self,
        current_user: UserMembershipQueryReponse,
        connection: AsyncConnection,
    ) -> MFAQRCodeResponse:
        """Get MFA QR code for setup."""
        logger.debug("Fetching MFA QR code")
        # Get the current member details
        logger.debug("Fetching member details for MFA QR code")
        member = await self.fetch_member_details(
            connection=connection,
            user_uid=current_user.uuid,
        )

        if member.mfa_enabled is False:
            logger.warning("MFA is not enabled for the user")
            raise MFANotEnabledException()

        # Generate QR code
        qr_code_bs64 = TwoFactorAuth.get_provisioning_qrcode_base64(
            username=current_user.username,
            secret=member.mfa_secret,
        )

        logger.debug("MFA QR code generated successfully")
        return MFAQRCodeResponse(qr_code_bs64=qr_code_bs64)

    def _revoke_tokens(self, access_token: str, refresh_token: str) -> None:
        """Revoke access and refresh tokens by adding them to the Redis blacklist."""
        logger.debug("Revoking tokens")
        import time

        from app.helpers.auth import decode_access_jwt, decode_refresh_jwt

        # Revoke access token
        if access_token:
            data_access = decode_access_jwt(token=access_token)
            if data_access:
                timenow = time.time()
                expiry_access_sec = int(data_access.get("expire_time", 0) - timenow)
                if expiry_access_sec > 0 and not self.redis.is_token_revoked(token=access_token):
                    self.redis.add_token_to_blacklist(
                        token=access_token,
                        expire_sec=expiry_access_sec,
                    )

        # Revoke refresh token
        if refresh_token:
            data_refresh = decode_refresh_jwt(token=refresh_token)
            if data_refresh:
                timenow = time.time()
                expiry_refresh_sec = int(data_refresh.get("expire_time", 0) - timenow)
                if expiry_refresh_sec > 0 and not self.redis.is_token_revoked(token=refresh_token):
                    self.redis.add_token_to_blacklist(
                        token=refresh_token,
                        expire_sec=expiry_refresh_sec,
                    )
