"""DTOs da camada de decisão."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AttentionFlagDTO(BaseModel):
    code: str
    severity: str
    title: str
    detail: str
    confidence: str
    evidence: dict[str, Any]


class FieldAttentionDTO(BaseModel):
    field_id: int
    field_name: str
    attention_level: str
    flags: list[AttentionFlagDTO]


class RankingItemDTO(BaseModel):
    field_id: int
    field_name: str
    value: float


class DecisionsResponse(BaseModel):
    farm_id: int
    season: str | None
    n_fields: int
    fields: list[FieldAttentionDTO]
    rankings: dict[str, list[RankingItemDTO]]
    note: str


class CostProjectionResponse(BaseModel):
    crop_cycle_id: int
    actual_total_cost: float
    remaining_planned_cost: float | None
    projected_total_cost: float | None
    projected_cost_per_ha: float | None
    basis: str
