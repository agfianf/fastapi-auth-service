# conftest.py
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from app.depedencies.database import get_async_conn, get_async_transaction_conn
from app.main import app


@pytest_asyncio.fixture
async def async_client():
    # Don't not create mock connection here
    # because it will be shared across all tests
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_conn_trans():
    mock_connection = AsyncMock()
    app.dependency_overrides[get_async_transaction_conn] = lambda: mock_connection

    yield mock_connection  # Mengembalikan mock connection untuk digunakan dalam test

    # Bersihkan override setelah test selesai
    app.dependency_overrides.pop(get_async_transaction_conn, None)


@pytest.fixture
async def db_conn():
    mock_connection = AsyncMock()
    app.dependency_overrides[get_async_conn] = lambda: mock_connection

    yield mock_connection  # Mengembalikan mock connection untuk digunakan dalam test

    # Bersihkan override setelah test selesai
    app.dependency_overrides.pop(get_async_conn, None)
