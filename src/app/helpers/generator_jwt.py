import datetime as dt
import time

from datetime import datetime, timedelta

import structlog

from app.config import KEY_REFRESH_TOKEN, settings
from app.helpers.auth import create_access_token, create_refresh_token
from app.integrations.redis import RedisHelper


logger = structlog.get_logger(__name__)


# auth
def generate_refresh_cookies(
    refresh_token: str,
    is_https: bool = False,
) -> dict:
    """Generate cookie settings for refresh token.

    Parameters
    ----------
    refresh_token : str
        The refresh token to store in the cookie.
    is_https : bool, optional
        Whether the connection is secure (HTTPS), by default False.

    Returns
    -------
    dict
        Dictionary containing cookie settings.

    """
    # Calculate expiration time
    expire_minutes = settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES
    expire_time = datetime.now(tz=dt.UTC) + timedelta(minutes=expire_minutes)

    return {
        "key": KEY_REFRESH_TOKEN,
        "value": refresh_token,
        "path": "/",
        "httponly": True,
        "secure": is_https,
        "samesite": "none" if is_https else "lax",
        "max_age": expire_minutes * 60,
        "expires": expire_time,
    }


def generate_delete_refresh_cookies(is_https: bool = False) -> dict:
    """Generate cookie settings to delete refresh token cookie.

    Parameters
    ----------
    is_https : bool, optional
        Whether the connection is secure (HTTPS), by default False.

    Returns
    -------
    dict
        Dictionary containing cookie settings for deletion.

    """
    return {
        "key": KEY_REFRESH_TOKEN,
        "path": "/",
        "httponly": True,
        "samesite": "none" if is_https else "lax",
    }


# auth
def generate_temporary_mfa_token(
    redis: RedisHelper,
    user_data: dict,
    expire_minutes: int = settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
    username: str | None = None,
) -> str:
    expire_time = time.time() + (60 * expire_minutes)
    jwt_data_temporary = {
        **user_data,
        "exp": expire_time,
    }

    mfa_temporary_token = create_access_token(data=jwt_data_temporary)
    logger.debug(f"Create key `mfa_temporary_token-{username}` with expire {expire_minutes} minutes")
    redis.set_data(
        key=f"mfa_temporary_token-{username}",
        value=mfa_temporary_token,
        expire_sec=60 * expire_minutes,  # 3 minutes
    )

    return mfa_temporary_token


def generate_jwt_forgot_password_token(
    user_data: dict,
    expire_minutes: int = settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
) -> str:
    expire_time = time.time() + (60 * expire_minutes)
    jwt_data_temporary = {
        "sub": user_data.get("uuid", ""),
        "exp": expire_time,
    }
    forgot_password_token = create_access_token(data=jwt_data_temporary)

    return forgot_password_token


def generate_jwt_tokens(
    user_data: dict,
    expire_minutes_access: int = settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
    expire_minutes_refresh: int = settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES,
) -> tuple[str, dict]:
    timenow = time.time()
    jwt_access_data = {
        **user_data,
        "exp": timenow + (60 * expire_minutes_access),
        "iat": timenow,
    }
    jwt_refresh_data = {
        **user_data,
        "exp": timenow + (60 * expire_minutes_refresh),
        "iat": timenow,
    }

    access_token = create_access_token(data=jwt_access_data)
    refresh_token = create_refresh_token(data=jwt_refresh_data)

    cookies = generate_refresh_cookies(refresh_token)
    return access_token, cookies
