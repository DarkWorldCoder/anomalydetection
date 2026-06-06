import pytest 
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete 

from app.db.session import AsyncSessionLocal, engine 
from app.main import app 
from app.models.revoked_token import RevokedToken
from app.models.user import User

@pytest.fixture(autouse=True)
async def cleanup_db():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(RevokedToken))
        await session.execute(delete(User))
        await session.commit()
    yield 
    async with AsyncSessionLocal() as session:
        await session.execute(delete(RevokedToken))
        await session.execute(delete(User))
        await session.commit()

@pytest.fixture 
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
        
async def test_register_user(async_client:AsyncClient):
    payload = {
        "full_name": "Test User",
        "email": "ayush@example.com",
        "password": "password123"
    }
    return await async_client.post("/auth/register", json=payload)

async def test_login_user(async_client:AsyncClient):
    login_payload = {
        "email": "ayush@example.com",
        "password": "password123"
    }
    return await async_client.post("/auth/login", json=login_payload)
    

@pytest.mark.asyncio
async def test_register_success(async_client:AsyncClient):
    response = await test_register_user(async_client)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert data["data"]["email"] == "ayush@example.com"
    assert "hashed_password" not in data["data"]
    
@pytest.mark.asyncio
async def test_register_duplicate_email(async_client:AsyncClient):
    await test_register_user(async_client)
    response = await test_register_user(async_client)
    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_success(async_client:AsyncClient):
    await test_register_user(async_client)
    response = await test_login_user(async_client)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "ayush@example.com"

@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client:AsyncClient):
    await test_register_user(async_client)
    login_payload = {
        "email": "ayush@example.com",
        "password": "wrongpassword"
    }
    response = await async_client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client:AsyncClient):
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "password123"
    }
    response = await async_client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_read_current_user(async_client:AsyncClient):
    await test_register_user(async_client)
    login_response = await test_login_user(async_client)
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Current user retrieved successfully"
    assert data["data"]["email"] == "ayush@example.com"
    
@pytest.mark.asyncio
async def tet_me_reject_invalid_token(async_client:AsyncClient):
    response = await async_client.get("/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_logout_user(async_client:AsyncClient):
    await test_register_user(async_client)
    login_response = await test_login_user(async_client)
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    logout_response = await async_client.post("/auth/logout", headers=headers)
    
    assert logout_response.status_code == 200
    data = logout_response.json()
    assert data["message"] == "Logout successful"
    
    # Try to access protected route with the same token after logout
    response = await async_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    
@pytest.fixture(scope="session",autouse=True)
async def teardown():
    yield 
    await engine.dispose()