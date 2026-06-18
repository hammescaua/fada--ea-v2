"""Endpoint de calibração (somente leitura)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.calibration import CalibrationResponse
from app.services.calibration import CalibrationUnavailable, load_calibration_report

router = APIRouter()


@router.get("/calibration", response_model=CalibrationResponse)
def calibration() -> CalibrationResponse:
    try:
        return CalibrationResponse(**load_calibration_report())
    except CalibrationUnavailable as exc:
        raise HTTPException(
            503, "Relatório de calibração ausente. Rode pipelines.backtest_calibration."
        ) from exc
