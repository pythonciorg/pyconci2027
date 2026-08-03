# PyCon Côte d'Ivoire 2027 Backend

Backend FastAPI pour PyCon Côte d'Ivoire 2027, avec billetterie, CFP, paiement GeniusPay, génération de billets et programme.

## Prérequis

- Python 3.12+
- Docker / Docker Compose

## Installation

1. Copier le fichier d'exemple :

```bash
copy .env.example .env
```

2. Construire et lancer le projet :

```bash
docker compose up --build
```

3. Accéder à l'API :

- `http://localhost:8000`
- Documentation Swagger : `http://localhost:8000/docs`

## Configuration GeniusPay sandbox

Dans `.env` :

```env
GENIUSPAY_API_KEY=pk_sandbox_example
GENIUSPAY_API_SECRET=sk_sandbox_example
GENIUSPAY_WEBHOOK_SECRET=wh_sandbox_example
GENIUSPAY_ENVIRONMENT=sandbox
```

## Alembic

Créer la base et exécuter les migrations :

```bash
alembic upgrade head
```

## Tests

```bash
pytest
```

## Endpoints clés

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /cfp/submissions`
- `GET /cfp/submissions`
- `PATCH /cfp/submissions/{id}/status`
- `GET /tickets/categories`
- `POST /orders`
- `POST /payments`
- `GET /payments/{reference}`
- `POST /payments/webhook/geniuspay`
- `GET /tickets/{qr_code}/verify`
- `POST /program/rooms`
- `POST /program/sessions`
- `GET /program`
