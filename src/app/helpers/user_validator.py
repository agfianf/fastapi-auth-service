from app.depedencies.auth import decode_access_jwt
from app.exceptions.auth import InvalidMFATokenException, SignInFailureException, UserIsUnactiveException
from app.helpers.auth import verify_password
from app.integrations.mfa import TwoFactorAuth
from app.integrations.redis import RedisHelper
from app.schemas.users import CreateUserQueryResponse, UserMembershipQueryReponse


def verify_user_status(user: CreateUserQueryResponse | UserMembershipQueryReponse | None) -> None:
    if user is None:
        raise SignInFailureException()

    if user.is_active is False:
        raise UserIsUnactiveException()

    if user.deleted_at is not None:
        print(
            "user.deleted_at",
            user.username,
            user.email,
            user.deleted_at,
        )
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
        raise SignInFailureException()


def verify_mfa_credentials(
    redis: RedisHelper,
    mfa_token: str,
    mfa_code: str,
    user: UserMembershipQueryReponse,
) -> None:
    mfa_token_db = redis.get_data(
        f"mfa_temporary_token-{user.username}",
    )
    if mfa_token_db != mfa_token:
        raise InvalidMFATokenException()

    user_data = decode_access_jwt(token=mfa_token)
    if user_data is None:
        raise InvalidMFATokenException()

    is_verfied_token = TwoFactorAuth.verify_token(
        token=mfa_code,
        secret=user.mfa_secret,
    )

    if not is_verfied_token:
        raise InvalidMFATokenException()

    redis.delete_data(f"mfa_temporary_token-{user.username}")
