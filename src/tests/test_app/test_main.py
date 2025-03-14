import pytest


@pytest.mark.asyncio
async def test_read_main(async_client):
    response = await async_client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
