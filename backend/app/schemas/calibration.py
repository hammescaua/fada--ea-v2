"""DTOs do relatório de calibração."""

from __future__ import annotations

from pydantic import BaseModel


class CoverageDetailDTO(BaseModel):
    nominal: float
    observed: float
    wilson_low: float
    wilson_high: float
    verdict: str


class ReliabilityPointDTO(BaseModel):
    nominal: float
    observed: float
    wilson_low: float
    wilson_high: float


class CalibrationReportDTO(BaseModel):
    label: str
    n_predictions: int
    coverage_50: float
    coverage_80: float
    coverage_90: float
    coverage_95: float
    coverage_detail: list[CoverageDetailDTO]
    mean_width: float
    median_width: float
    relative_width_pct: float
    mae: float
    rmse: float
    bias: float
    pinball: dict[str, float]
    reliability_curve: list[ReliabilityPointDTO]
    overconfident: bool
    underconfident: bool
    interpretation: str


class CalibrationResponse(BaseModel):
    method: str
    ground_truth: str
    note: str
    regional: CalibrationReportDTO
    personalized: CalibrationReportDTO
