"""Domínio agronômico — perfil padronizado e ajuste a priori da produtividade."""

from __future__ import annotations

from app.domain.agronomy.cost_profile import (
    COST_FACTOR_EFFECTS,
    AppliedCostFactor,
    CostAdjustmentResult,
    compute_cost_adjustment,
)
from app.domain.agronomy.estimate import PersonalizedEstimate, apply_adjustment
from app.domain.agronomy.knowledge import KnowledgeEntry, for_factor, guide
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
    EconomicRecommendation,
    Recommendation,
    economic_recommendations,
    recommendations,
)
from app.domain.agronomy.scenario import (
    WATER_FACTORS,
    scenario_multipliers,
    water_sensitivity_note,
)
from app.domain.agronomy.soil import SoilAnalysis, classify_soil_analysis

__all__ = [
    "COST_FACTOR_EFFECTS",
    "FACTORS",
    "AdjustmentResult",
    "AppliedCostFactor",
    "AppliedFactor",
    "CostAdjustmentResult",
    "EconomicRecommendation",
    "Factor",
    "KnowledgeEntry",
    "MANAGEABLE_FACTORS",
    "PersonalizedEstimate",
    "Recommendation",
    "SoilAnalysis",
    "UnknownFactor",
    "WATER_FACTORS",
    "apply_adjustment",
    "classify_soil_analysis",
    "compute_adjustment",
    "compute_cost_adjustment",
    "economic_recommendations",
    "for_factor",
    "guide",
    "planting_window_class",
    "recommendations",
    "scenario_multipliers",
    "validate_profile",
    "water_sensitivity_note",
]
