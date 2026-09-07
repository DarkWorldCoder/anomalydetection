import pytest
from httpx import AsyncClient


async def register_user(client: AsyncClient, email: str = "ayush@example.com"):
    return await client.post(
        "/auth/register",
        json={
            "full_name": "Ayush Niroula",
            "email": email,
            "password": "strongpass123",
        },
    )


async def login_user(client: AsyncClient, email: str = "ayush@example.com"):
    return await client.post(
        "/auth/login",
        json={"email": email, "password": "strongpass123"},
    )


@pytest.mark.asyncio
async def test_register_succeeds(client: AsyncClient):
    response = await register_user(client)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "ayush@example.com"
    assert body["data"]["role"] == "student"
    assert "hashed_password" not in body["data"]


@pytest.mark.asyncio
async def test_register_accepts_supported_role(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "full_name": "API Analyst",
            "email": "analyst@example.com",
            "password": "strongpass123",
            "role": "analyst",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "analyst"


@pytest.mark.asyncio
async def test_duplicate_email_returns_conflict(client: AsyncClient):
    await register_user(client)
    response = await register_user(client)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_succeeds(client: AsyncClient):
    await register_user(client)
    response = await login_user(client)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["access_token"]
    assert body["data"]["user"]["email"] == "ayush@example.com"


@pytest.mark.asyncio
async def test_login_fails_with_wrong_password(client: AsyncClient):
    await register_user(client)
    response = await client.post(
        "/auth/login",
        json={"email": "ayush@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient):
    await register_user(client)
    login_response = await login_user(client)
    token = login_response.json()["data"]["access_token"]

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "ayush@example.com"


@pytest.mark.asyncio
async def test_me_rejects_missing_token(client: AsyncClient):
    response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_can_update_profile(client: AsyncClient):
    await register_user(client)
    login_response = await login_user(client)
    token = login_response.json()["data"]["access_token"]

    response = await client.patch(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "  Ayush Updated  ", "email": "UPDATED@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["full_name"] == "Ayush Updated"
    assert response.json()["data"]["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_profile_update_rejects_duplicate_email(client: AsyncClient):
    await register_user(client)
    await register_user(client, "other@example.com")
    login_response = await login_user(client)
    token = login_response.json()["data"]["access_token"]

    response = await client.patch(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "other@example.com"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_logout_revokes_token(client: AsyncClient):
    await register_user(client)
    login_response = await login_user(client)
    token = login_response.json()["data"]["access_token"]

    logout_response = await client.get(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    me_response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert logout_response.status_code == 200
    assert logout_response.json()["success"] is True
    assert me_response.status_code == 401
