# conftest.py
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def async_client():
    # Create a test app state with mocked services
    app.state.auth_service = MagicMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_auth_service():
    """Create a mock auth service for testing."""
    auth_service = AsyncMock()
    return auth_service


@pytest.fixture
def setup_app_with_mocks(mock_auth_service):
    """Set up the app with all required mocks."""
    app.state.auth_service = mock_auth_service
    return app
