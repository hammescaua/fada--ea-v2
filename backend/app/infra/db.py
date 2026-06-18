"""Engine, sessão e bootstrap do schema.

SQLAlchemy 2.0 síncrono. SQLite por padrão (ver ADR-0009); Postgres via
FADA_DATABASE_URL. Schema criado com create_all() — Alembic entra quando estabilizar.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Cria as tabelas (idempotente). Importa os modelos para registrá-los."""
    from app.infra import models  # noqa: F401 — registra as tabelas no metadata

    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    """Dependency do FastAPI: sessão por request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
