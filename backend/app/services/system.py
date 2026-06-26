"""Status do sistema — observabilidade determinística (db, modelo, contagens)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import settings
from app.infra.models import (
    AgriculturalEventORM,
    CropCycleORM,
    FarmORM,
    FieldORM,
)
from app.services.calibration import REPORT_PATH
from app.services.data_health import data_sources_health


def system_status(session: Session) -> dict:
    db_ok, counts = _database(session)
    return {
        "status": "ok" if db_ok and settings.model_path.exists() else "degraded",
        "version": __version__,
        "database": {"status": "ok" if db_ok else "erro", "url_scheme": _scheme()},
        "model": {
            "status": "ok" if settings.model_path.exists() else "ausente",
            "path": settings.model_path.name,
        },
        "calibration_report": {"present": REPORT_PATH.exists()},
        "counts": counts,
        "data_sources": data_sources_health(),
    }


def _scheme() -> str:
    return settings.database_url.split("://", 1)[0]


def _database(session: Session) -> tuple[bool, dict]:
    try:
        counts = {
            "farms": session.scalar(select(func.count()).select_from(FarmORM)) or 0,
            "fields": session.scalar(select(func.count()).select_from(FieldORM)) or 0,
            "crop_cycles": session.scalar(select(func.count()).select_from(CropCycleORM)) or 0,
            "events": session.scalar(select(func.count()).select_from(AgriculturalEventORM)) or 0,
        }
        return True, counts
    except Exception:  # noqa: BLE001
        return False, {"farms": 0, "fields": 0, "crop_cycles": 0, "events": 0}
