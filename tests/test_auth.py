import pytest


@pytest.mark.asyncio
async def test_register_creates_user(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "testeur@pyconci.ci",
            "full_name": "Testeur DMA",
            "password": "MotDePasse123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testeur@pyconci.ci"
    assert data["role"] == "participant"
    assert "hashed_password" not in data  # le mot de passe ne doit jamais être renvoyé


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client):
    payload = {
        "email": "duplicate@pyconci.ci",
        "full_name": "Premier",
        "password": "MotDePasse123",
    }
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 200

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 400
    assert "déjà utilisé" in second.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={
            "email": "login-test@pyconci.ci",
            "full_name": "Login Test",
            "password": "MotDePasse123",
        },
    )

    response = await client.post(
        "/auth/login",
        json={"email": "login-test@pyconci.ci", "password": "MotDePasse123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={
            "email": "wrongpass@pyconci.ci",
            "full_name": "Wrong Pass",
            "password": "MotDePasse123",
        },
    )

    response = await client.post(
        "/auth/login",
        json={"email": "wrongpass@pyconci.ci", "password": "MauvaisMotDePasse"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_authentication(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client):
    await client.post(
        "/auth/register",
        json={
            "email": "me-test@pyconci.ci",
            "full_name": "Me Test",
            "password": "MotDePasse123",
        },
    )
    login_response = await client.post(
        "/auth/login",
        json={"email": "me-test@pyconci.ci", "password": "MotDePasse123"},
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "me-test@pyconci.ci"