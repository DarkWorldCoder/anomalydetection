import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.db.session import AsyncSessionLocal, engine
from app.main import app
from app.models.api_request import ApiRequest
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture(autouse=True)
async def clean_database(request):
    if "client" not in request.fixturenames:
        yield
        return
    async with AsyncSessionLocal() as session:
        await session.execute(delete(ApiRequest))
        await session.execute(delete(RevokedToken))
        await session.execute(delete(User))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(ApiRequest))
        await session.execute(delete(RevokedToken))
        await session.execute(delete(User))
        await session.commit()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client


@pytest.fixture
async def auth_headers(client: AsyncClient):
    await client.post("/auth/register", json={
        "full_name": "API Tester",
        "email": "api-tester@example.com",
        "password": "strongpass123",
    })
    response = await client.post("/auth/login", json={
        "email": "api-tester@example.com",
        "password": "strongpass123",
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def traffic_record():
    return {
        "request": {
            "headers": {"User-Agent": "pytest"},
            "method": "GET",
            "url": "https://example.com/api/users?page=1",
            "body": "",
        },
        "response": {
            "status": "OK",
            "headers": {"Content-Type": "application/json"},
            "status_code": 200,
            "body": "{}",
        },
        "metadata": {
            "timestamp": "2026-08-28T10:00:00Z",
            "source_ip": "127.0.0.1",
            "response_time_ms": 12.5,
        },
    }


@pytest.fixture(scope="session", autouse=True)
async def dispose_engine():
    yield
    await engine.dispose()
