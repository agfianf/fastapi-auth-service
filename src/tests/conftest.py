from unittest.mock import AsyncMock

import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from app.depedencies.database import get_async_conn, get_async_transaction_conn
from app.main import app

# Fixtures
from tests.fixtures.auth.roles import override_role_admin


@pytest_asyncio.fixture
async def async_client():
    # Don't not create mock connection here
    # because it will be shared across all tests
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_conn_trans():
    """Fixture to mocking database connection for transaction tests.

    Each endpoint will contain dependecny injection to get_async_transaction_conn which is to get database connection
    for transaction. We will mock this connection to avoid real database connection
    and to speed up the test.
    """
    mock_connection = AsyncMock()
    app.dependency_overrides[get_async_transaction_conn] = lambda: mock_connection

    yield mock_connection  # Mengembalikan mock connection untuk digunakan dalam test

    # Bersihkan override setelah test selesai
    app.dependency_overrides.pop(get_async_transaction_conn, None)


@pytest_asyncio.fixture
async def db_conn():
    """Fixture to mocking database connection for non-transaction tests.

    Each endpoint will contain dependecny injection to get_async_conn which is to get database connection
    for non-transaction. We will mock this connection to avoid real database connection
    and to speed up the test.
    """
    mock_connection = AsyncMock()
    app.dependency_overrides[get_async_conn] = lambda: mock_connection

    yield mock_connection  # return mock_connection

    # cleanup override after test
    app.dependency_overrides.pop(get_async_conn, None)
