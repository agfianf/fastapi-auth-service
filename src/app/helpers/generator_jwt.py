import datetime as dt
import time

from datetime import datetime, timedelta

from app.config import settings
from app.helpers.auth import create_access_token, create_refresh_token
from app.integrations.redis import RedisHelper


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
        "key": "refresh_token_app",
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
        "key": "refresh_token_app",
        "path": "/",
        "httponly": True,
        "samesite": "none" if is_https else "lax",
    }


# auth
def generate_temporary_mfa_token(
    redis: RedisHelper,
    user_data: dict,
    expire_minutes: int = settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
) -> str:
    expire_time = time.time() + (60 * expire_minutes)
    jwt_data_temporary = {
        **user_data,
        "expire_time": expire_time,
    }

    mfa_temporary_token = create_access_token(data=jwt_data_temporary)
    redis.set_data(
        key=f"mfa_temporary_token-{user_data.get('username')}",
        value=mfa_temporary_token,
        expire_sec=60 * expire_minutes,  # 3 minutes
    )

    return mfa_temporary_token


def generate_jwt_tokens(
    user_data: dict,
    expire_minutes_access: int = settings.AUTH_TOKEN_ACCESS_EXPIRE_MINUTES,
    expire_minutes_refresh: int = settings.AUTH_TOKEN_REFRESH_EXPIRE_MINUTES,
) -> tuple[str, dict]:
    jwt_access_data = {
        **user_data,
        "expire_time": time.time() + (60 * expire_minutes_access),
    }
    jwt_refresh_data = {
        **user_data,
        "expire_time": time.time() + (60 * expire_minutes_refresh),
    }

    access_token = create_access_token(data=jwt_access_data)
    refresh_token = create_refresh_token(data=jwt_refresh_data)

    cookies = generate_refresh_cookies(refresh_token)
    return access_token, cookies
