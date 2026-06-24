"""Domínio agronômico — perfil padronizado e ajuste a priori da produtividade."""

from __future__ import annotations

from app.domain.agronomy.cost_profile import (
    COST_FACTOR_EFFECTS,
    AppliedCostFactor,
    CostAdjustmentResult,
    compute_cost_adjustment,
)
from app.domain.agronomy.estimate import PersonalizedEstimate, apply_adjustment
from app.domain.agronomy.profile import (
    FACTORS,
    AdjustmentResult,
    AppliedFactor,
    Factor,
    UnknownFactor,
    compute_adjustment,
    validate_profile,
)

__all__ = [
    "COST_FACTOR_EFFECTS",
    "FACTORS",
    "AdjustmentResult",
    "AppliedCostFactor",
    "AppliedFactor",
    "CostAdjustmentResult",
    "Factor",
    "PersonalizedEstimate",
    "UnknownFactor",
    "apply_adjustment",
    "compute_adjustment",
    "compute_cost_adjustment",
    "validate_profile",
]
