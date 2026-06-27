"""DTOs da projeção plurianual por talhão (ADR-0031)."""

from __future__ import annotations

from pydantic import BaseModel


class ScenarioEconomicsOut(BaseModel):
    name: str
    yield_sc_ha: float
    price_per_bag: float
    revenue_per_ha: float
    profit_per_ha: float
    margin_pct: float


class SeasonProjectionOut(BaseModel):
    season: str
    year_index: int
    price_per_bag: float
    cost_per_ha: float
    expected_profit_per_ha: float
    scenarios: list[ScenarioEconomicsOut]


class ProductivityOut(BaseModel):
    point_sc_ha: float
    interval_sc_ha: list[float]
    scenarios: list[dict]
    note: str


class AssumptionsOut(BaseModel):
    price_per_bag: float
    price_source: str | None = None
    cost_per_ha: float
    cost_source: str | None = None
    price_trend_pct: float
    cost_trend_pct: float


class MultiSeasonResponse(BaseModel):
    field_id: int
    field_name: str
    municipality: str
    crop: str
    area_ha: float
    productivity: ProductivityOut
    assumptions: AssumptionsOut
    seasons: list[SeasonProjectionOut]
    data_sources: list[str]
    narrative: str | None = None
    disclaimer: str
