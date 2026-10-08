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


async def _request_reset_token(client, monkeypatch, email):
    import re

    from app.api.v1.routers import auth as auth_module

    sent = []
    monkeypatch.setattr(
        auth_module,
        "send_notification_email",
        lambda background_tasks, recipient, subject, message, attachments=None: sent.append(message),
    )
    response = await client.post("/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    if not sent:
        return None
    return re.search(r"token=(\S+)", sent[0]).group(1)


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_does_not_leak(client, monkeypatch):
    token = await _request_reset_token(client, monkeypatch, "inconnu@pyconci.ci")
    assert token is None  # aucun email envoyé, mais la réponse reste un 200 générique


@pytest.mark.asyncio
async def test_reset_password_flow(client, monkeypatch):
    await client.post(
        "/auth/register",
        json={"email": "reset@pyconci.ci", "full_name": "Reset Test", "password": "MotDePasse123"},
    )
    token = await _request_reset_token(client, monkeypatch, "reset@pyconci.ci")
    assert token

    response = await client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "NouveauMotDePasse456"},
    )
    assert response.status_code == 200

    old_login = await client.post("/auth/login", json={"email": "reset@pyconci.ci", "password": "MotDePasse123"})
    assert old_login.status_code == 401
    new_login = await client.post("/auth/login", json={"email": "reset@pyconci.ci", "password": "NouveauMotDePasse456"})
    assert new_login.status_code == 200

    # le token ne doit pas être réutilisable
    reuse = await client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "EncoreUnAutre789"},
    )
    assert reuse.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_rejects_non_reset_token(client):
    await client.post(
        "/auth/register",
        json={"email": "reset-type@pyconci.ci", "full_name": "Reset Type", "password": "MotDePasse123"},
    )
    login_response = await client.post(
        "/auth/login",
        json={"email": "reset-type@pyconci.ci", "password": "MotDePasse123"},
    )
    access_token = login_response.json()["access_token"]

    response = await client.post(
        "/auth/reset-password",
        json={"token": access_token, "new_password": "NouveauMotDePasse456"},
    )
    assert response.status_code == 400