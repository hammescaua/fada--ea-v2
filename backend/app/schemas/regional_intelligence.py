"""DTOs do endpoint de Inteligência Regional (Camada 1, Modo Básico)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegionalIntelligenceRequest(BaseModel):
    municipality: str = Field(..., examples=["Horizontina"])
    uf: str = Field("RS", examples=["RS"])
    crop: str = Field("soja", examples=["soja"])
    season: str = Field(..., examples=["2026/27"], description="Formato AAAA/AA")


class ScenarioDTO(BaseModel):
    name: str
    yield_sc_ha: float


class RiskDTO(BaseModel):
    factor: str
    severity: str
    description: str
    metric: dict[str, float]


class PlantingWindowDTO(BaseModel):
    start: str
    end: str
    optimal_start: str
    optimal_end: str
    rationale: str


class RegionalIntelligenceResponse(BaseModel):
    municipality: str
    municipality_code: int
    crop: str
    season: str
    harvest_year: int
    estimated_yield_sc_ha: float
    confidence_interval_sc_ha: tuple[float, float]
    scenarios: list[ScenarioDTO]
    climatic_risks: list[RiskDTO]
    planting_window: PlantingWindowDTO
    explanation: str
    data_sources: list[str]
    disclaimer: str
