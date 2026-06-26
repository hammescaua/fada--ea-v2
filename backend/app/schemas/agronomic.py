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
    essential: bool = False
    explanation: str | None = None
    sources: list[str] = []
    options: list[FactorOptionOut]


class KnowledgeEntryOut(BaseModel):
    key: str
    title: str
    explanation: str
    practical: str
    sources: list[str]


class AgronomicEstimateRequest(BaseModel):
    municipality: str
    crop: str = "soja"
    season: str = "2026/27"
    # Perfil padronizado: {chave_do_fator: valor_escolhido}. Campos omitidos
    # assumem o nível típico (efeito 0).
    profile: dict[str, str] = Field(default_factory=dict)


class SaveProfileRequest(BaseModel):
    profile: dict[str, str] = Field(default_factory=dict)


class SoilAnalysisRequest(BaseModel):
    p_mehlich: float | None = Field(None, ge=0, description="Fósforo Mehlich-1 (mg/dm³)")
    k_mehlich: float | None = Field(None, ge=0, description="Potássio Mehlich-1 (mg/dm³)")
    clay_pct: float | None = Field(None, ge=0, le=100, description="Argila (%)")
    ctc: float | None = Field(None, ge=0, description="CTC a pH 7 (cmolc/dm³)")
    ph_water: float | None = Field(None, ge=0, le=14, description="pH em água")
    al_saturation_pct: float | None = Field(None, ge=0, le=100, description="Saturação por Al (m%)")
    organic_matter_pct: float | None = Field(None, ge=0, le=100, description="Matéria orgânica (%)")


class SoilClassificationNote(BaseModel):
    factor: str
    value: str
    basis: str


class SoilAnalysisResponse(BaseModel):
    profile_fragment: dict[str, str]
    notes: list[SoilClassificationNote]
    disclaimer: str


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


class RecommendationOut(BaseModel):
    key: str
    question: str
    current_label: str
    target_label: str
    gain_pct: float
    gain_sc_ha: float
    rationale: str
    confidence: str


class AgronomicEstimateResponse(BaseModel):
    municipality: str
    municipality_code: int
    crop: str
    season: str
    harvest_year: int
    regional: PointInterval
    personalized: PersonalizedBlock
    adjustment: AdjustmentBlock
    recommendations: list[RecommendationOut]
    narrative: str | None = None
    water_sensitivity_note: str | None = None
    climatic_risks: list[dict]
    data_sources: list[str]
    disclaimer: str
