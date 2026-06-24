"""DTOs de benchmark de custo (referência CONAB)."""

from __future__ import annotations

from pydantic import BaseModel


class CostComponentOut(BaseModel):
    item: str
    value_per_ha: float
    share_pct: float


class CostBenchmarkResponse(BaseModel):
    crop: str
    uf: str
    safra: str
    technology: str
    source: str
    fetched_at: str
    coe_per_ha: float
    cot_per_ha: float
    ct_per_ha: float
    components: list[CostComponentOut]
    disclaimer: str


class CostComparisonOut(BaseModel):
    actual_per_ha: float
    reference_label: str
    reference_per_ha: float
    delta_per_ha: float
    ratio_pct: float
    descriptor: str


class CostBenchmarkComparisonResponse(BaseModel):
    crop: str
    uf: str
    safra: str
    technology: str
    source: str
    fetched_at: str
    coe_per_ha: float
    cot_per_ha: float
    ct_per_ha: float
    actual_cost_per_ha: float
    primary: str
    references: dict[str, CostComparisonOut]
    components: list[CostComponentOut]
    disclaimer: str
