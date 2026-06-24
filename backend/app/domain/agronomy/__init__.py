"""Domínio agronômico — perfil padronizado e ajuste a priori da produtividade."""

from __future__ import annotations

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
    "FACTORS",
    "AdjustmentResult",
    "AppliedFactor",
    "Factor",
    "PersonalizedEstimate",
    "UnknownFactor",
    "apply_adjustment",
    "compute_adjustment",
    "validate_profile",
]
