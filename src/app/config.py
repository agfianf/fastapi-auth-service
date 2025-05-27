import os

from typing import Final

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


path_env = os.path.join(os.path.dirname(__file__), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_default=False,
        env_file=path_env,
        extra="ignore",
    )

    # APP
    APP_NAME: str
    APP_PORT: int
    APP_HOST: str
    APP_VERSION: str
    APP_DEBUG: bool
    APP_ENV: str = "local"

    # DATABASE
    POSTGRE_HOST: str
    POSTGRE_PORT: int
    POSTGRE_USER: str
    POSTGRE_PASSWORD: str
    POSTGRE_DB: str

    # AUTH
    AUTH_DEFAULT_ROOT_PASSWORD: str = "rooT123456789?"
    AUTH_DEFAULT_ADMIN_PASSWORD: str = "admiN123456789?"
    AUTH_SALT_PHRASE: str = "defaultsalt"
    AUTH_ROUNDS: int = 1001
    AUTH_ALGORITHM_ACCESS: str = "HS256"
    AUTH_TOKEN_ACCESS_EXPIRE_MINUTES: int = 30
    AUTH_SECRET_ACCESS: str = "access_secret"
    AUTH_SECRET_REFRESH: str = "refresh_secret"
    AUTH_ALGORITHM_REFRESH: str = "HS256"
    AUTH_TOKEN_REFRESH_EXPIRE_MINUTES: int = 24 * 60
    NAME_APP_2FA: str = "Auth Service"

    # REDIS
    REDIS_HOST: str
    REDIS_PORT: int

    # WHITELIST X-CLIENT-ID
    WHITELIST_CLIENT_IDS: str

    # MAIL
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_TIMEOUT: int

    # Property untuk parse whitelist jadi set
    @property
    def parsed_whitelist(self) -> set[str]:
        return set(self.WHITELIST_CLIENT_IDS.split(","))


# Inisialisasi settings
settings: Final[Settings] = Settings()
DATABASE_URL: Final = f"postgresql+psycopg://{settings.POSTGRE_USER}:{settings.POSTGRE_PASSWORD}@{settings.POSTGRE_HOST}:{settings.POSTGRE_PORT}/{settings.POSTGRE_DB}"
WHITELIST_CLIENT_IDS: Final[set[str]] = settings.parsed_whitelist
MIN_LENGTH: int = 8
SIMILARITY_THRESHOLD: float = 0.7
COMMON_SUBSTITUTIONS: dict = {
    "a": "4",
    "e": "3",
    "i": "1",
    "o": "0",
    "s": "5",
    "t": "7",
    "b": "8",
}

KEY_REFRESH_TOKEN: Final = "refresh_token_app"
email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TIMEOUT=settings.MAIL_TIMEOUT,
)
