import pytest

from app.models.user import User, UserRole
from app.core.security import get_password_hash
from tests.helpers import login


async def _register_and_login(client, email="speaker@pyconci.ci", role_setup=None):
    await client.post(
        "/auth/register",
        json={"email": email, "full_name": "Speaker Test", "password": "MotDePasse123"},
    )
    return await login(client, email)


async def _create_admin_and_login(client, db_session, email="admin-cfp@pyconci.ci"):
    admin = User(
        email=email,
        full_name="Admin Test",
        hashed_password=get_password_hash("MotDePasse123"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()

    return await login(client, email)


@pytest.mark.asyncio
async def test_create_submission_requires_auth(client):
    response = await client.post(
        "/cfp/submissions",
        json={
            "title": "Talk sans auth",
            "description": "Une description suffisamment longue pour passer la validation.",
            "topic": "Backend",
            "level": "Débutant",
            "format": "talk",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_submission_success(client):
    token = await _register_and_login(client)

    response = await client.post(
        "/cfp/submissions",
        json={
            "title": "Introduction à FastAPI",
            "description": "Une description suffisamment longue pour passer la validation.",
            "topic": "Backend",
            "level": "Débutant",
            "format": "talk",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Introduction à FastAPI"
    assert data["status"] == "soumis"


@pytest.mark.asyncio
async def test_list_submissions_requires_admin_role(client):
    token = await _register_and_login(client, email="participant@pyconci.ci")

    response = await client.get(
        "/cfp/submissions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_submission_by_id(client):
    token = await _register_and_login(client, email="speaker2@pyconci.ci")

    create_response = await client.post(
        "/cfp/submissions",
        json={
            "title": "Talk à consulter",
            "description": "Une description suffisamment longue pour passer la validation.",
            "topic": "Backend",
            "level": "Avancé",
            "format": "atelier",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    submission_id = create_response.json()["id"]

    response = await client.get(
        f"/cfp/submissions/{submission_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == submission_id


@pytest.mark.asyncio
async def test_get_submission_not_found(client):
    token = await _register_and_login(client, email="speaker3@pyconci.ci")

    response = await client.get(
        "/cfp/submissions/9999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_submissions_as_admin(client, db_session):
    speaker_token = await _register_and_login(client, email="speaker4@pyconci.ci")
    await client.post(
        "/cfp/submissions",
        json={
            "title": "Talk pour liste admin",
            "description": "Une description suffisamment longue pour passer la validation.",
            "topic": "Backend",
            "level": "Débutant",
            "format": "talk",
        },
        headers={"Authorization": f"Bearer {speaker_token}"},
    )

    admin_token = await _create_admin_and_login(client, db_session)

    response = await client.get(
        "/cfp/submissions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_update_submission_status_as_admin(client, db_session):
    speaker_token = await _register_and_login(client, email="speaker5@pyconci.ci")
    create_response = await client.post(
        "/cfp/submissions",
        json={
            "title": "Talk à accepter",
            "description": "Une description suffisamment longue pour passer la validation.",
            "topic": "Backend",
            "level": "Intermédiaire",
            "format": "talk",
        },
        headers={"Authorization": f"Bearer {speaker_token}"},
    )
    submission_id = create_response.json()["id"]

    admin_token = await _create_admin_and_login(client, db_session)

    response = await client.patch(
        f"/cfp/submissions/{submission_id}/status",
        json={"status": "accepté"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepté"

SUBMISSION_PAYLOAD = {
    "title": "Talk à modifier",
    "description": "Une description suffisamment longue pour passer la validation.",
    "topic": "Backend",
    "level": "Débutant",
    "format": "talk",
}


@pytest.mark.asyncio
async def test_update_submission_by_owner(client):
    token = await _register_and_login(client, email="speaker6@pyconci.ci")
    create_response = await client.post(
        "/cfp/submissions",
        json=SUBMISSION_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    submission_id = create_response.json()["id"]

    response = await client.patch(
        f"/cfp/submissions/{submission_id}",
        json={"title": "Titre modifié", "format": "atelier"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Titre modifié"
    assert data["format"] == "atelier"
    # Les champs non envoyés restent inchangés.
    assert data["topic"] == "Backend"
    assert data["status"] == "soumis"


@pytest.mark.asyncio
async def test_update_submission_not_owner(client):
    owner_token = await _register_and_login(client, email="speaker7@pyconci.ci")
    create_response = await client.post(
        "/cfp/submissions",
        json=SUBMISSION_PAYLOAD,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    submission_id = create_response.json()["id"]

    other_token = await _register_and_login(client, email="intrus@pyconci.ci")
    response = await client.patch(
        f"/cfp/submissions/{submission_id}",
        json={"title": "Piratage"},
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_submission_not_found(client):
    token = await _register_and_login(client, email="speaker8@pyconci.ci")

    response = await client.patch(
        "/cfp/submissions/9999",
        json={"title": "Inexistant"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_submission_cannot_change_status(client):
    token = await _register_and_login(client, email="speaker9@pyconci.ci")
    create_response = await client.post(
        "/cfp/submissions",
        json=SUBMISSION_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    submission_id = create_response.json()["id"]

    response = await client.patch(
        f"/cfp/submissions/{submission_id}",
        json={"status": "accepté"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "soumis"


@pytest.mark.asyncio
async def test_update_submission_blocked_once_in_review(client, db_session):
    speaker_token = await _register_and_login(client, email="speaker10@pyconci.ci")
    create_response = await client.post(
        "/cfp/submissions",
        json=SUBMISSION_PAYLOAD,
        headers={"Authorization": f"Bearer {speaker_token}"},
    )
    submission_id = create_response.json()["id"]

    admin_token = await _create_admin_and_login(client, db_session)
    await client.patch(
        f"/cfp/submissions/{submission_id}/status",
        json={"status": "en_revue"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.patch(
        f"/cfp/submissions/{submission_id}",
        json={"title": "Trop tard"},
        headers={"Authorization": f"Bearer {speaker_token}"},
    )

    assert response.status_code == 409
