"""Bootstrap da aplicação FastAPI."""

from fastapi import FastAPI

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.infra.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__)
    init_db()  # cria as tabelas (idempotente)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
