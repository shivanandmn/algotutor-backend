import pytest
from typing import Dict
from httpx import AsyncClient
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_google_login(client: AsyncClient):
    response = await client.post("/api/v1/auth/login/google", json={
        "email": "new@example.com",
        "name": "New User",
        "google_id": "new123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@example.com"

async def test_get_current_user(client: AsyncClient, test_user: User, auth_headers: Dict[str, str]):
    headers = await auth_headers
    user = await test_user
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["role"] == user.role

async def test_update_user(client: AsyncClient, test_user: User, auth_headers: Dict[str, str]):
    headers = await auth_headers
    user = await test_user
    response = await client.put(
        "/api/v1/auth/me",
        headers=headers,
        json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == user.email

async def test_list_users_as_admin(client: AsyncClient, admin_auth_headers: Dict[str, str]):
    headers = await admin_auth_headers
    response = await client.get("/api/v1/auth/users", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

async def test_list_users_as_user(client: AsyncClient, auth_headers: Dict[str, str]):
    headers = await auth_headers
    response = await client.get("/api/v1/auth/users", headers=headers)
    assert response.status_code == 403

async def test_update_user_role(client: AsyncClient, test_user: User, admin_auth_headers: Dict[str, str]):
    headers = await admin_auth_headers
    user = await test_user
    response = await client.put(
        f"/api/v1/auth/users/{str(user.id)}/role",
        headers=headers,
        json={"role": "admin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
