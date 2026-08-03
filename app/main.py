from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.cfp import router as cfp_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.payments import router as payments_router
from app.api.v1.routers.program import router as program_router
from app.api.v1.routers.tickets import router as tickets_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="PyCon Côte d'Ivoire 2027 API",
        version="0.1.0",
        description="API backend pour la première édition de PyCon CI 2027, incluant billetterie, CFP, paiement GeniusPay et programme.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(cfp_router)
    app.include_router(orders_router)
    app.include_router(payments_router)
    app.include_router(tickets_router)
    app.include_router(program_router)

    @app.get("/", tags=["Health"])
    async def health_check():
        return {"status": "ok", "service": "pyconci-backend"}

    return app


app = create_app()
