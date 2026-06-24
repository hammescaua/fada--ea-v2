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
    planting_window_class,
    validate_profile,
)
from app.domain.agronomy.recommendations import (
    MANAGEABLE_FACTORS,
    Recommendation,
    recommendations,
)
from app.domain.agronomy.soil import SoilAnalysis, classify_soil_analysis

__all__ = [
    "COST_FACTOR_EFFECTS",
    "FACTORS",
    "AdjustmentResult",
    "AppliedCostFactor",
    "AppliedFactor",
    "CostAdjustmentResult",
    "Factor",
    "MANAGEABLE_FACTORS",
    "PersonalizedEstimate",
    "Recommendation",
    "SoilAnalysis",
    "UnknownFactor",
    "apply_adjustment",
    "classify_soil_analysis",
    "compute_adjustment",
    "compute_cost_adjustment",
    "planting_window_class",
    "recommendations",
    "validate_profile",
]
