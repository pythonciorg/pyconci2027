from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.cfp import router as cfp_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.payments import router as payments_router
from app.api.v1.routers.program import router as program_router
from app.api.v1.routers.tickets import router as tickets_router
from app.api.v1.routers.speakers import router as speakers_router
from app.api.v1.routers.sponsor import router as sponsors_router
from app.api.v1.routers.articles import router as articles_router
from app.api.v1.routers.conduct_reports import router as conduct_reports_router
from app.api.v1.routers.cfp_admin import router as cfp_admin_router
from app.api.v1.routers.admin_stats import router as admin_stats_router
from app.api.v1.routers.translations import router as translations_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import get_settings

settings = get_settings()

MAX_BODY_SIZE = 1_000_000  # 1 Mo
class LimitBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Corps de requête trop volumineux"},
            )
        return await call_next(request)
def create_app() -> FastAPI:
    app = FastAPI(
        title="PyCon Côte d'Ivoire 2027 API",
        version="0.1.0",
        description="API backend pour la première édition de PyCon CI 2027, incluant billetterie, CFP, paiement GeniusPay et programme.",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(LimitBodySizeMiddleware)
    app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
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
    app.include_router(speakers_router)
    app.include_router(sponsors_router)
    app.include_router(articles_router)
    app.include_router(conduct_reports_router)
    app.include_router(cfp_admin_router)
    app.include_router(admin_stats_router)
    app.include_router(translations_router)

    @app.get("/", tags=["Health"])
    async def health_check():
        return {"status": "ok", "service": "pyconci-backend"}

    return app


app = create_app()