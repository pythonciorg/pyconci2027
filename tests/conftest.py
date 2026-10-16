import os
os.environ["DATABASE_URL"] = "postgresql+asyncpg://pycon_admin:password@db:5432/pyconci_test_suite"
# Les tests n'envoient jamais de vrais emails : sans SMTP_HOST, ils sont affichés dans la console.
os.environ["SMTP_HOST"] = ""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.models.base import Base
from app.db.session import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://pycon_admin:password@db:5432/pyconci_test_suite"

from app.core.limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield


@pytest.fixture(autouse=True)
def capture_auth_emails(monkeypatch):
    # Les emails d'auth (codes, réinitialisation) sont capturés au lieu d'être envoyés.
    from app.api.v1.routers import auth as auth_module
    from tests.helpers import OUTBOX

    OUTBOX.clear()
    monkeypatch.setattr(
        auth_module,
        "send_notification_email",
        lambda background_tasks, recipient, subject, message, attachments=None: OUTBOX.append(
            {"recipient": recipient, "subject": subject, "message": message}
        ),
    )
    yield
@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine_test = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    TestSessionLocal = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine_test.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()