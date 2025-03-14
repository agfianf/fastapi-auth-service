# tests/conftest.py
from unittest.mock import AsyncMock

import pytest

from fastapi.testclient import TestClient

from app.main import app, lifespan


@pytest.fixture
async def client():
    async with lifespan(app) as state:
        with TestClient(app) as client:
            yield client, state


@pytest.fixture
def mock_auth_service():
    auth_service = AsyncMock()
    return auth_service
