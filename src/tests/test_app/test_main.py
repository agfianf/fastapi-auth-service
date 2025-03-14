# tests/test_main.py
import pytest

from app.config import settings
from app.main import app


def test_app_initialization():
    assert app.title == settings.APP_NAME
    assert app.version == f"{settings.APP_VERSION}-{settings.APP_ENV}"
    assert app.lifespan is not None


@pytest.mark.asyncio
async def test_root_redirect(client):
    test_client, _ = client
    response = test_client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


@pytest.mark.asyncio
async def test_lifespan_initialization(client, mock_auth_service):  # noqa: ARG001
    _, state = client
    assert "auth_service" in state
