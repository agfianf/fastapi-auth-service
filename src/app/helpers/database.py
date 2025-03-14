"""Database connection configuration and setup for the FastAPI auth service."""

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings
from app.helpers.generator import generate_connection_url


DATABASE_URL = generate_connection_url(
    driver_name="postgresql+psycopg",
    username=settings.POSTGRE_USER,
    password=settings.POSTGRE_PASSWORD,
    host=settings.POSTGRE_HOST,
    port=settings.POSTGRE_PORT,
    database=settings.POSTGRE_DB,
)


engine_async = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=20,
    echo=False,
    echo_pool=True,
)

Base = declarative_base()
metadata = Base.metadata
