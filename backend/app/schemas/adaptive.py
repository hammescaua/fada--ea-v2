"""DTOs de Adaptive Farm Intelligence."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.regional_intelligence import ScenarioDTO


class ResidualPointDTO(BaseModel):
    harvest_year: int
    actual_sc_ha: float
    regional_fitted_sc_ha: float
    residual_sc_ha: float
    residual_pct: float


class FarmProfileOut(BaseModel):
    farm_id: int
    number_of_cycles: int
    bias_percentage: float
    mean_relative_residual: float
    mean_residual_sc_ha: float
    median_residual_sc_ha: float
    variance_relative: float
    last_updated: datetime | None = None
    residual_history: list[ResidualPointDTO]


class RegionalPredictionDTO(BaseModel):
    point_sc_ha: float
    interval_sc_ha: tuple[float, float]


class FarmAdjustmentDTO(BaseModel):
    applied_pct: float
    observed_bias_pct: float
    n_cycles: int


class PersonalizedPredictionDTO(BaseModel):
    point_sc_ha: float
    interval_sc_ha: tuple[float, float]
    scenarios: list[ScenarioDTO]


class PersonalizedIntelligenceRequest(BaseModel):
    farm_id: int = Field(..., examples=[1])
    season: str = Field(..., examples=["2026/27"])


class PersonalizedIntelligenceResponse(BaseModel):
    farm_id: int
    municipality_code: int
    season: str
    harvest_year: int
    regional_prediction: RegionalPredictionDTO
    farm_adjustment: FarmAdjustmentDTO
    personalized_prediction: PersonalizedPredictionDTO
    confidence_score: float
    adaptation_level: str
    explanation: str
