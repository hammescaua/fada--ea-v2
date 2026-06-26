"""DTOs do Cartão de Decisão (contrato §4 do guia)."""

from __future__ import annotations

from pydantic import BaseModel


class EvidenceOut(BaseModel):
    label: str
    detail: str


class DecisionEffectOut(BaseModel):
    basis: str
    yield_sc_ha: tuple[float, float, float] | None = None
    profit_brl_ha: tuple[float, float, float] | None = None


class DecisionCardOut(BaseModel):
    id: str
    source: str
    decision: str
    recommendation: str
    confidence: str
    horizon: str
    disclaimer: str
    n_data: int
    severity: str
    effect: DecisionEffectOut | None = None
    why: list[EvidenceOut] = []


class DecisionCardsResponse(BaseModel):
    farm_id: int
    field_id: int | None
    n_cards: int
    cards: list[DecisionCardOut]
    note: str
