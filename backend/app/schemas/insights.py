"""DTOs de Field Intelligence e Insight Engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FieldSummaryDTO(BaseModel):
    field_id: int
    field_name: str
    n_seasons: int
    mean_actual_sc_ha: float
    bias_vs_region_pct: float
    yield_stability_std_pct: float | None
    mean_cost_per_ha: float | None
    n_seasons_with_cost: int
    latest_year: int
    latest_actual_sc_ha: float
    cost_trend: dict[str, Any] | None


class FieldAnalyticsResponse(BaseModel):
    farm_id: int
    n_fields: int
    n_records: int
    fields: list[FieldSummaryDTO]


class InsightDTO(BaseModel):
    type: str
    scope: str
    field_id: int | None
    title: str
    detail: str
    evidence: dict[str, Any]
    confidence: str


class InsightsResponse(BaseModel):
    farm_id: int
    n_insights: int
    insights: list[InsightDTO]
    note: str
