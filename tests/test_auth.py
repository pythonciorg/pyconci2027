import re

import pytest

from tests.helpers import OUTBOX, last_code, login


async def _register(client, email, password="MotDePasse123"):
    response = await client.post(
        "/auth/register",
        json={"email": email, "full_name": "Test", "password": password},
    )
    assert response.status_code == 200, response.text
    return response


@pytest.mark.asyncio
async def test_register_sends_code(client):
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
    assert "otp_token" in data
    assert "access_token" not in data  # pas de tokens avant la saisie du code
    code = last_code("testeur@pyconci.ci")
    assert code

    # l'utilisateur ne saisit que le code ; le site renvoie l'otp_token reçu
    response = await client.post("/auth/otp/verify", json={"otp_token": data["otp_token"], "code": code})
    assert response.status_code == 200
    access_token = response.json()["access_token"]

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "testeur@pyconci.ci"
    assert me.json()["role"] == "participant"
    assert "hashed_password" not in me.json()  # le mot de passe ne doit jamais être renvoyé


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
async def test_login_sends_code_instead_of_tokens(client):
    await _register(client, "login-test@pyconci.ci")
    OUTBOX.clear()

    response = await client.post(
        "/auth/login",
        json={"email": "login-test@pyconci.ci", "password": "MotDePasse123"},
    )
    assert response.status_code == 200
    assert "access_token" not in response.json()
    otp_token = response.json()["otp_token"]

    code = last_code("login-test@pyconci.ci")
    assert code

    response = await client.post("/auth/otp/verify", json={"otp_token": otp_token, "code": code})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await _register(client, "wrongpass@pyconci.ci")
    OUTBOX.clear()

    response = await client.post(
        "/auth/login",
        json={"email": "wrongpass@pyconci.ci", "password": "MauvaisMotDePasse"},
    )

    assert response.status_code == 401
    assert OUTBOX == []  # aucun code envoyé sans le bon mot de passe


@pytest.mark.asyncio
async def test_me_requires_authentication(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client):
    await _register(client, "me-test@pyconci.ci")
    token = await login(client, "me-test@pyconci.ci")

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "me-test@pyconci.ci"


async def _request_reset_token(client, email):
    OUTBOX.clear()
    response = await client.post("/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    if not OUTBOX:
        return None
    return re.search(r"token=(\S+)", OUTBOX[-1]["message"]).group(1)


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_does_not_leak(client):
    token = await _request_reset_token(client, "inconnu@pyconci.ci")
    assert token is None  # aucun email envoyé, mais la réponse reste un 200 générique


@pytest.mark.asyncio
async def test_reset_password_flow(client):
    await _register(client, "reset@pyconci.ci")
    token = await _request_reset_token(client, "reset@pyconci.ci")
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
    await _register(client, "reset-type@pyconci.ci")
    access_token = await login(client, "reset-type@pyconci.ci")

    response = await client.post(
        "/auth/reset-password",
        json={"token": access_token, "new_password": "NouveauMotDePasse456"},
    )
    assert response.status_code == 400


async def _verify(client, otp_token, code):
    return await client.post("/auth/otp/verify", json={"otp_token": otp_token, "code": code})


def _wrong(code):
    return "000000" if code != "000000" else "111111"


@pytest.mark.asyncio
async def test_otp_code_single_use(client):
    otp_token = (await _register(client, "otp@pyconci.ci")).json()["otp_token"]
    code = last_code("otp@pyconci.ci")

    assert (await _verify(client, otp_token, code)).status_code == 200
    assert (await _verify(client, otp_token, code)).status_code == 400


@pytest.mark.asyncio
async def test_otp_wrong_code(client):
    otp_token = (await _register(client, "otp-faux@pyconci.ci")).json()["otp_token"]
    code = last_code("otp-faux@pyconci.ci")

    response = await _verify(client, otp_token, _wrong(code))
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_otp_code_belongs_to_its_account(client):
    # Le code d'un compte ne doit pas ouvrir un autre compte, même avec un otp_token valide.
    token_a = (await _register(client, "otp-a@pyconci.ci")).json()["otp_token"]
    await _register(client, "otp-b@pyconci.ci")
    code_a = last_code("otp-a@pyconci.ci")
    code_b = last_code("otp-b@pyconci.ci")
    if code_a == code_b:
        pytest.skip("les deux codes tirés au hasard sont identiques")

    response = await _verify(client, token_a, code_b)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_otp_rejects_other_token_types(client):
    await _register(client, "otp-type@pyconci.ci")
    access_token = await login(client, "otp-type@pyconci.ci")

    response = await _verify(client, access_token, "123456")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_otp_blocked_after_max_attempts(client, db_session):
    from sqlalchemy import select

    from app.models.user import User

    otp_token = (await _register(client, "otp-essais@pyconci.ci")).json()["otp_token"]
    code = last_code("otp-essais@pyconci.ci")

    # On simule 4 essais déjà ratés (le rate limit empêche d'en faire 6 en une minute).
    user = (await db_session.execute(select(User).filter_by(email="otp-essais@pyconci.ci"))).scalar_one()
    user.otp_attempts = 4
    await db_session.commit()

    await _verify(client, otp_token, _wrong(code))
    response = await _verify(client, otp_token, code)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_otp_expired(client, db_session):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.models.user import User

    otp_token = (await _register(client, "otp-expire@pyconci.ci")).json()["otp_token"]
    code = last_code("otp-expire@pyconci.ci")

    user = (await db_session.execute(select(User).filter_by(email="otp-expire@pyconci.ci"))).scalar_one()
    user.otp_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    response = await _verify(client, otp_token, code)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_new_login_replaces_old_code(client):
    await _register(client, "otp-nouveau@pyconci.ci")
    first = last_code("otp-nouveau@pyconci.ci")
    response = await client.post("/auth/login", json={"email": "otp-nouveau@pyconci.ci", "password": "MotDePasse123"})
    otp_token = response.json()["otp_token"]
    second = last_code("otp-nouveau@pyconci.ci")
    if first == second:
        pytest.skip("les deux codes tirés au hasard sont identiques")

    assert (await _verify(client, otp_token, first)).status_code == 400
    assert (await _verify(client, otp_token, second)).status_code == 200


@pytest.mark.asyncio
async def test_otp_rejects_malformed_code(client):
    otp_token = (await _register(client, "otp-format@pyconci.ci")).json()["otp_token"]
    response = await _verify(client, otp_token, "12ab")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_otp_request_route_removed(client):
    response = await client.post("/auth/otp/request", json={"email": "otp@pyconci.ci"})
    assert response.status_code == 404


async def _skip_resend_cooldown(db_session, email):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.models.user import User

    user = (await db_session.execute(select(User).filter_by(email=email))).scalar_one()
    user.otp_sent_at = datetime.now(timezone.utc) - timedelta(seconds=61)
    await db_session.commit()


@pytest.mark.asyncio
async def test_otp_resend_flow(client, db_session):
    old_token = (await _register(client, "renvoi@pyconci.ci")).json()["otp_token"]
    old_code = last_code("renvoi@pyconci.ci")
    await _skip_resend_cooldown(db_session, "renvoi@pyconci.ci")

    response = await client.post("/auth/otp/resend", json={"otp_token": old_token})
    assert response.status_code == 200
    new_token = response.json()["otp_token"]
    new_code = last_code("renvoi@pyconci.ci")
    assert len(OUTBOX) == 2  # inscription + renvoi

    if old_code != new_code:
        # l'ancien code est annulé
        assert (await _verify(client, new_token, old_code)).status_code == 400
    assert (await _verify(client, new_token, new_code)).status_code == 200


@pytest.mark.asyncio
async def test_otp_resend_cooldown(client):
    otp_token = (await _register(client, "renvoi-delai@pyconci.ci")).json()["otp_token"]

    response = await client.post("/auth/otp/resend", json={"otp_token": otp_token})
    assert response.status_code == 429
    assert 0 < int(response.headers["Retry-After"]) <= 60
    assert len(OUTBOX) == 1  # aucun nouvel email


@pytest.mark.asyncio
async def test_otp_resend_invalid_token(client):
    response = await client.post("/auth/otp/resend", json={"otp_token": "pas-un-token"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_otp_resend_rejects_other_token_types(client):
    await _register(client, "renvoi-type@pyconci.ci")
    access_token = await login(client, "renvoi-type@pyconci.ci")

    response = await client.post("/auth/otp/resend", json={"otp_token": access_token})
    assert response.status_code == 400
