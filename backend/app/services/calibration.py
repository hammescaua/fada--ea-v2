"""Serviço de calibração — somente leitura do artefato (não altera previsões)."""

from __future__ import annotations

import json
from functools import lru_cache

from app.core.config import settings

REPORT_PATH = settings.model_path.parent / "calibration_report.json"


class CalibrationUnavailable(Exception):
    pass


@lru_cache
def load_calibration_report() -> dict:
    if not REPORT_PATH.exists():
        raise CalibrationUnavailable(str(REPORT_PATH))
    return json.loads(REPORT_PATH.read_text())
