import time

from typing import Literal

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from app.config import settings
from app.exceptions.auth import InvalidTokenException


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Password Management
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Token/JWT Management
## Create JWT
def create_access_token(data: dict) -> str:
    return jwt.encode(
        claims=data,
        key=settings.AUTH_SECRET_ACCESS,
        algorithm=settings.AUTH_ALGORITHM_ACCESS,
    )


def create_refresh_token(data: dict) -> str:
    return jwt.encode(
        claims=data,
        key=settings.AUTH_SECRET_REFRESH,
        algorithm=settings.AUTH_ALGORITHM_REFRESH,
    )


## Decode JWT
def decode_jwt(token: str, type_jwt: Literal["access", "refresh"] = "access") -> dict | None:
    try:
        key_secret = settings.AUTH_SECRET_ACCESS if type_jwt == "access" else settings.AUTH_SECRET_REFRESH
        algorithm = settings.AUTH_ALGORITHM_ACCESS if type_jwt == "access" else settings.AUTH_ALGORITHM_REFRESH
        return jwt.decode(
            token=token,
            key=key_secret,
            algorithms=[algorithm],
        )
    except Exception as err:
        raise InvalidTokenException() from err


def decode_access_jwt(token: str) -> dict | None:
    try:
        decoded_token = decode_jwt(token=token)
        exp_time = decoded_token.get("exp", None)
        return decoded_token if exp_time >= time.time() else None
    except Exception:
        return None


def decode_refresh_jwt(token: str) -> dict:
    try:
        decoded_token = decode_jwt(token=token, type_jwt="refresh")
        exp_time = decoded_token.get("exp", None)
        return decoded_token if exp_time >= time.time() else None
    except Exception:
        return {}


## Verify JWT
def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_jwt(token=token)
        username: str | None = payload.get("sub", None)
        roles: list | None = payload.get("roles", None)
        exp_time = payload.get("exp", None)

        if time.time() > exp_time:
            raise InvalidTokenException()

        if username is None or roles is None:
            raise InvalidTokenException()

    except jwt.PyJWTError as err:
        raise InvalidTokenException() from err

    return payload
