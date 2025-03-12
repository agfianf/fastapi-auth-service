import datetime as dt

from datetime import datetime, timedelta

from sqlalchemy import URL
from src.config import settings
from uuid_utils.compat import UUID, uuid7


def generate_connection_url(
    driver_name: str,
    username: str,
    password: str,
    host: str,
    port: str | int,
    database: str,
) -> URL:
    """Generate a SQLAlchemy connection URL.

    Parameters
    ----------
    driver_name : str
        Name of the database driver.
    username : str
        Database username.
    password : str
        Database password.
    host : str
        Database host.
    port : str or int
        Database port.
    database : str
        Database name.

    Returns
    -------
    URL
        SQLAlchemy URL object for database connection.

    """
    return URL.create(
        drivername=driver_name,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def generate_uuid() -> UUID:
    """Generate a UUID using the uuid7 specification.

    Returns
    -------
    UUID
        A new UUID (v7) instance.

    """
    return uuid7()


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
