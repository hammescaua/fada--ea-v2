"""DTOs do Perfil Agronômico e da estimativa personalizada."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FactorOptionOut(BaseModel):
    value: str
    label: str
    effect_pct: float


class FactorOut(BaseModel):
    key: str
    question: str
    rationale: str
    confidence: str
    options: list[FactorOptionOut]


class AgronomicEstimateRequest(BaseModel):
    municipality: str
    crop: str = "soja"
    season: str = "2026/27"
    # Perfil padronizado: {chave_do_fator: valor_escolhido}. Campos omitidos
    # assumem o nível típico (efeito 0).
    profile: dict[str, str] = Field(default_factory=dict)


class SaveProfileRequest(BaseModel):
    profile: dict[str, str] = Field(default_factory=dict)


class AgronomicProfileResponse(BaseModel):
    field_id: int
    profile: dict[str, str]


class AppliedFactorOut(BaseModel):
    key: str
    question: str
    option_label: str
    effect_pct: float
    rationale: str
    confidence: str


class PointInterval(BaseModel):
    point_sc_ha: float
    interval_sc_ha: list[float]


class ScenarioOut(BaseModel):
    name: str
    yield_sc_ha: float


class PersonalizedBlock(BaseModel):
    point_sc_ha: float
    interval_sc_ha: list[float]
    scenarios: list[ScenarioOut]


class AdjustmentBlock(BaseModel):
    multiplier: float
    total_effect_pct: float
    clamped: bool
    n_factors: int
    factors: list[AppliedFactorOut]


class AgronomicEstimateResponse(BaseModel):
    municipality: str
    municipality_code: int
    crop: str
    season: str
    harvest_year: int
    regional: PointInterval
    personalized: PersonalizedBlock
    adjustment: AdjustmentBlock
    climatic_risks: list[dict]
    data_sources: list[str]
    disclaimer: str
