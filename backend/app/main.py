"""Bootstrap da aplicação FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.infra.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__)
    # CORS: sem isto o browser bloqueia o frontend (causa raiz do "Failed to fetch").
    # Sem cookies -> allow_credentials=False permite usar "*" com segurança.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    init_db()  # cria as tabelas (idempotente)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        # A raiz não é a API — orienta quem abre o backend no navegador.
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": "/api/v1/health",
            "status": "/api/v1/system/status",
        }

    return app


app = create_app()
