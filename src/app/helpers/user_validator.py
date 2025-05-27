import structlog

from app.depedencies.auth import decode_access_jwt
from app.exceptions.auth import InvalidMFATokenException, SignInFailureException, UserIsUnactiveException
from app.helpers.auth import verify_password
from app.integrations.mfa import TwoFactorAuth
from app.integrations.redis import RedisHelper
from app.schemas.users import CreateUserQueryResponse, UserMembershipQueryReponse


logger = structlog.get_logger(__name__)


def verify_user_status(user: CreateUserQueryResponse | UserMembershipQueryReponse | None) -> None:
    if user is None:
        logger.error("[Sign In Failed]: User not found")
        raise SignInFailureException()

    if user.is_active is False:
        logger.error("[Sign In Failed]: User is not active")
        raise UserIsUnactiveException()

    if user.deleted_at is not None:
        logger.error("[Sign In Failed]: User is deleted")
        raise SignInFailureException()


def verify_user_password(
    password_input: str,
    password_hash: str,
) -> None:
    is_verified = verify_password(
        plain_password=password_input,
        hashed_password=password_hash,
    )

    if not is_verified:
        logger.error("[Sign In Failed]: Password verification failed")
        raise SignInFailureException()


def verify_mfa_credentials(
    redis: RedisHelper,
    mfa_token: str,
    mfa_code: str,
    user: UserMembershipQueryReponse,
) -> None:
    key_cache = f"mfa_temporary_token-{user.username}"
    mfa_token_db = redis.get_data(key_cache)
    logger.info("Verifying MFA credentials")
    if mfa_token_db != mfa_token:
        logger.debug(
            "[Sign In Failed]: MFA token does not match",
            mfa_token_db=mfa_token_db,
            mfa_token=mfa_token,
        )
        logger.error("[Sign In Failed]: Invalid MFA token")
        raise InvalidMFATokenException()

    user_data = decode_access_jwt(token=mfa_token)
    if user_data is None:
        logger.error("[Sign In Failed]: Invalid MFA token data")
        raise InvalidMFATokenException()

    logger.info("[MFA Verification]: Verifying MFA code")
    is_verified_token = TwoFactorAuth.verify_token(
        token=mfa_code,
        secret=user.mfa_secret,
    )

    if not is_verified_token:
        logger.error("[Sign In Failed]: Invalid MFA code")
        raise InvalidMFATokenException()

    logger.info("[MFA Verification]: MFA code verified successfully")
    redis.delete_data(key_cache)
    logger.debug("Deleted MFA temporary token from cache")
