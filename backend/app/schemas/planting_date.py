"""DTOs dos endpoints de What-If de data de plantio."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.regional_intelligence import ScenarioDTO


class PhenologyDTO(BaseModel):
    r1_begin_flowering: str
    r6_full_seed: str


class _OutcomeDTO(BaseModel):
    expected_yield_sc_ha: float
    delta_vs_baseline_sc_ha: float
    confidence_interval_sc_ha: tuple[float, float]
    scenarios: list[ScenarioDTO]
    downside_sc_ha: float
    stability_iqr_sc_ha: float
    risk_score: float
    risk_drivers: dict[str, float]
    n_years: int


class PlantingDateSimulationRequest(BaseModel):
    municipality: str = Field(..., examples=["Horizontina"])
    uf: str = Field("RS", examples=["RS"])
    crop: str = Field("soja", examples=["soja"])
    season: str = Field(..., examples=["2026/27"])
    planting_date: str = Field(..., examples=["2026-11-01"], description="ISO AAAA-MM-DD")
    risk_aversion: float = Field(0.5, ge=0.0, le=2.0)


class PlantingDateSimulationResponse(_OutcomeDTO):
    municipality: str
    municipality_code: int
    crop: str
    season: str
    harvest_year: int
    requested_planting_date: str
    evaluated_planting_date: str
    snapped_note: str | None
    within_zarc: bool
    phenology: PhenologyDTO
    explanation: str
    scope_note: str


class PlantingWindowOptimizationRequest(BaseModel):
    municipality: str = Field(..., examples=["Horizontina"])
    uf: str = Field("RS", examples=["RS"])
    crop: str = Field("soja", examples=["soja"])
    season: str = Field(..., examples=["2026/27"])
    risk_aversion: float = Field(0.5, ge=0.0, le=2.0)
    top_n: int = Field(5, ge=1, le=17)


class RecommendationDTO(_OutcomeDTO):
    planting_date: str
    phenology: PhenologyDTO
    justification: str


class PlantingWindowOptimizationResponse(BaseModel):
    municipality: str
    municipality_code: int
    crop: str
    season: str
    harvest_year: int
    risk_aversion: float
    objective: str
    zarc_window: str
    baseline_expected_sc_ha: float
    top_recommendations: list[RecommendationDTO]
    scope_note: str
