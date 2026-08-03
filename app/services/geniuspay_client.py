import hmac
import json
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()
BASE_URL = "https://geniuspay.ci/api/v1/merchant"


class GeniusPayClientError(Exception):
    pass


class GeniusPayClient:
    def __init__(self, api_key: str, api_secret: str, environment: str = "sandbox"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.environment = environment
        self.base_url = BASE_URL
        self.headers = {
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret,
            "Content-Type": "application/json",
        }

    async def create_checkout_payment(self, amount: int, currency: str, description: str, customer: dict[str, Any], success_url: str, error_url: str, metadata: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "amount": amount,
            "currency": currency,
            "description": description,
            "customer": customer,
            "success_url": success_url,
            "error_url": error_url,
            "metadata": metadata,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.base_url}/payments", headers=self.headers, json=payload)
        return self._handle_response(response)

    async def get_payment(self, reference: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/payments/{reference}", headers=self.headers)
        return self._handle_response(response)

    def verify_webhook_signature(self, payload_body: bytes, timestamp: str, signature: str) -> bool:
        expected = hmac.new(self.api_secret.encode(), msg=f"{timestamp}.{payload_body.decode('utf-8')}".encode("utf-8"), digestmod="sha256").hexdigest()
        return hmac.compare_digest(expected, signature)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code not in (200, 201):
            try:
                errors = response.json()
            except ValueError:
                response.raise_for_status()
            raise GeniusPayClientError(errors)
        return response.json()


def get_geniuspay_client() -> GeniusPayClient:
    return GeniusPayClient(
        api_key=settings.geniuspay_api_key,
        api_secret=settings.geniuspay_api_secret,
        environment=settings.geniuspay_environment,
    )
