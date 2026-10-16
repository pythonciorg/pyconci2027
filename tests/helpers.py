import re

# Emails envoyés par le module auth pendant un test (vidée avant chaque test par conftest).
OUTBOX: list[dict] = []


def last_code(email: str) -> str | None:
    for sent in reversed(OUTBOX):
        if sent["recipient"] == email:
            match = re.search(r"\b(\d{6})\b", sent["message"])
            if match:
                return match.group(1)
    return None


async def login(client, email: str, password: str = "MotDePasse123") -> str:
    """Connexion complète : mot de passe, puis code reçu par email. Renvoie l'access_token."""
    response = await client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    otp_token = response.json()["otp_token"]
    response = await client.post("/auth/otp/verify", json={"otp_token": otp_token, "code": last_code(email)})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
