"""Value Objects da camada de decisão (imutáveis, computados na hora)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldDecisionInput:
    """Estado do talhão na safra-alvo + contexto histórico (coletado pelo serviço)."""

    field_id: int
    field_name: str
    area_ha: float | None
    target_yield_sc_ha: float | None = None
    expected_yield_sc_ha: float | None = None     # regional/real (sc/ha)
    actual_total_cost: float | None = None
    actual_cost_per_ha: float | None = None
    planned_total_cost: float | None = None
    pct_budget_consumed: float | None = None       # 0..100+
    over_budget: bool = False
    has_pending_planned: bool = False
    n_seasons: int = 0                              # histórico
    bias_vs_region_pct: float | None = None        # histórico
    stability_std_pct: float | None = None         # histórico


@dataclass(frozen=True)
class AttentionFlag:
    code: str
    severity: str            # "alta" | "média"
    title: str
    detail: str
    confidence: str          # "alta" | "moderada" | "exploratória"
    evidence: dict = field(default_factory=dict)


@dataclass(frozen=True)
class FieldAttention:
    field_id: int
    field_name: str
    attention_level: str     # "alta" | "média" | "saudável"
    flags: list[AttentionFlag]
