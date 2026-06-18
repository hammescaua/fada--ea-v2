"""Adaptive — Adaptive Farm Intelligence.

Personalização progressiva por fazenda como CORREÇÃO sobre o modelo regional
(nunca substituição): Prediction = Regional + BiasCorrection, com encolhimento
hierárquico (prior fixo) e incerteza preservada. Sem treino, sem deep learning
(ADR-0012).
"""

from app.domain.adaptive.profile import FarmPerformanceProfile
from app.domain.adaptive.shrinkage import (
    PersonalizedPrediction,
    ShrinkagePrior,
    adaptation_level,
    compute_profile_stats,
    personalize,
    shrinkage_weight,
)

__all__ = [
    "FarmPerformanceProfile",
    "ShrinkagePrior",
    "PersonalizedPrediction",
    "compute_profile_stats",
    "shrinkage_weight",
    "personalize",
    "adaptation_level",
]
