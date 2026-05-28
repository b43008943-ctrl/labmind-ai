"""
LabMind AI — FastAPI Application Entrypoint
Initializes the app, CORS middleware, and registers all routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_ai import router as ai_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_analyses import router as analyses_router
from app.api.routes_assets import router as assets_router
from app.api.routes_auth import router as auth_router
from app.api.routes_cases import router as cases_router
from app.api.routes_patients import router as patients_router
from app.api.routes_reports import router as reports_router
from app.api.routes_urinalysis import router as urinalysis_router
from app.api.routes_parasitology import router as parasitology_router
from app.api.routes_hematology import router as hematology_router
from app.api.routes_microbiology import router as microbiology_router
from app.api.routes_lab_results import router as lab_results_router
from app.api.routes_video_generator import router as video_generator_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    settings = get_settings()
    print("=" * 56)
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"  DEBUG={settings.DEBUG}")
    print("=" * 56)
    yield
    print("[SHUTDOWN] LabMind AI Backend stopped.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ──
    # Allow all network IPs and Cloudflare tunnels dynamically
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──
    app.include_router(auth_router)
    app.include_router(patients_router)
    app.include_router(cases_router)
    app.include_router(assets_router)
    app.include_router(analyses_router)
    app.include_router(reports_router)
    app.include_router(alerts_router)
    app.include_router(ai_router)
    app.include_router(urinalysis_router)
    app.include_router(parasitology_router)
    app.include_router(hematology_router)
    app.include_router(microbiology_router)
    app.include_router(lab_results_router)
    app.include_router(video_generator_router)

    # Health check
    @app.get("/health", tags=["System"])
    def health_check():
        return {"status": "online", "service": settings.APP_NAME}

    return app


app = create_app()
