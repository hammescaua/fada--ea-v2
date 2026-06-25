"""DTOs financeiros (Cost Engine)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CostBreakdownOut(BaseModel):
    total_cost: float
    area_ha: float
    cost_per_hectare: float
    cost_per_bag: float | None
    yield_sc_ha: float | None
    n_applications: int
    cost_by_category: dict[str, float]


class ScenarioResultOut(BaseModel):
    name: str
    yield_sc_ha: float
    price_per_bag: float
    revenue: float
    total_cost: float
    profit: float
    margin_pct: float
    profit_per_hectare: float


class FinancialsRequest(BaseModel):
    price_per_bag: float | None = Field(
        None, gt=0, examples=[125.0],
        description="Preço da saca (R$/sc). Opcional: se omitido, usa o preço "
                    "esperado da safra ou a cotação CEPEA/ESALQ ao vivo.",
    )


class FinancialsResponse(BaseModel):
    breakdown: CostBreakdownOut
    price_per_bag: float
    price_source: str
    break_even_yield_sc_ha: float
    yield_source: str
    scenarios: list[ScenarioResultOut]
