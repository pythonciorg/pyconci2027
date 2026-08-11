import time
import pytest

from app.models.ticket_category import TicketCategory
from app.models.order import Order
import app.api.v1.routers.payments as payments_module


class FakeGeniusPayClient:
    def __init__(self, should_fail=False, valid_signature=True):
        self.should_fail = should_fail
        self.valid_signature = valid_signature

    async def create_checkout_payment(self, **kwargs):
        if self.should_fail:
            from app.services.geniuspay_client import GeniusPayClientError
            raise GeniusPayClientError("Erreur simulée GeniusPay")
        return {
            "id": "pay_test_123",
            "reference": "REF-TEST-123",
            "fees": 100.0,
            "net_amount": kwargs["amount"] - 100.0,
            "checkout_url": "https://sandbox.geniuspay.test/checkout/REF-TEST-123",
        }

    def verify_webhook_signature(self, body, timestamp, signature):
        return self.valid_signature


async def _create_ticket_category(db_session, quota=10, price=15000):
    category = TicketCategory(name="Standard", price=price, currency="XOF", quota=quota)
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


async def _create_order(db_session, category, quantity=1):
    order = Order(
        user_id=None,
        customer_name="Client Test",
        customer_email="client@test.com",
        customer_phone="+225000000",
        ticket_category_id=category.id,
        quantity=quantity,
        total_amount=float(category.price * quantity),
    )
    db_session.add(order)
    category.quota -= quantity
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.mark.asyncio
async def test_create_order_success(client, db_session):
    category = await _create_ticket_category(db_session)

    response = await client.post(
        "/orders",
        json={
            "ticket_category_id": category.id,
            "quantity": 2,
            "customer_name": "Jean Test",
            "customer_email": "jean@test.com",
            "customer_phone": "+225010101",
            "user_id": None,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 2
    assert data["total_amount"] == category.price * 2


@pytest.mark.asyncio
async def test_create_order_exceeds_quota(client, db_session):
    category = await _create_ticket_category(db_session, quota=1)

    response = await client.post(
        "/orders",
        json={
            "ticket_category_id": category.id,
            "quantity": 5,
            "customer_name": "Jean Test",
            "customer_email": "jean@test.com",
            "customer_phone": "+225010101",
            "user_id": None,
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_payment_success(client, db_session, monkeypatch):
    category = await _create_ticket_category(db_session)
    order = await _create_order(db_session, category)

    fake_client = FakeGeniusPayClient()
    monkeypatch.setattr(payments_module, "get_geniuspay_client", lambda: fake_client)

    response = await client.post(
        "/payments",
        json={
            "order_id": order.id,
            "success_url": "https://pyconci.ci/success",
            "error_url": "https://pyconci.ci/error",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reference"] == "REF-TEST-123"
    assert data["checkout_url"].startswith("https://sandbox.geniuspay.test")


@pytest.mark.asyncio
async def test_create_payment_geniuspay_error(client, db_session, monkeypatch):
    category = await _create_ticket_category(db_session)
    order = await _create_order(db_session, category)

    fake_client = FakeGeniusPayClient(should_fail=True)
    monkeypatch.setattr(payments_module, "get_geniuspay_client", lambda: fake_client)

    response = await client.post(
        "/payments",
        json={
            "order_id": order.id,
            "success_url": "https://pyconci.ci/success",
            "error_url": "https://pyconci.ci/error",
        },
    )

    assert response.status_code == 502


@pytest.mark.asyncio
async def test_webhook_missing_headers(client):
    response = await client.post("/payments/webhook/geniuspay", json={})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client, monkeypatch):
    fake_client = FakeGeniusPayClient(valid_signature=False)
    monkeypatch.setattr(payments_module, "get_geniuspay_client", lambda: fake_client)

    response = await client.post(
        "/payments/webhook/geniuspay",
        json={"metadata": {"order_id": 1}},
        headers={
            "x-webhook-signature": "fake",
            "x-webhook-timestamp": "9999999999",
            "x-webhook-event": "payment.success",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_payment_success_flow(client, db_session, monkeypatch):
    category = await _create_ticket_category(db_session)
    order = await _create_order(db_session, category, quantity=2)

    fake_client = FakeGeniusPayClient(valid_signature=True)
    monkeypatch.setattr(payments_module, "get_geniuspay_client", lambda: fake_client)
    monkeypatch.setattr(payments_module, "send_notification_email", lambda *a, **kw: None)

    response = await client.post(
        "/payments/webhook/geniuspay",
        json={"metadata": {"order_id": order.id}},
        headers={
            "x-webhook-signature": "fake",
            "x-webhook-timestamp": str(int(time.time())),
            "x-webhook-event": "payment.success",
        },
    )

    assert response.status_code == 200
    assert response.json()["event"] == "payment.success"