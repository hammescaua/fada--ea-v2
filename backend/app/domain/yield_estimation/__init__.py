"""Yield estimation — inferência e cenários de produtividade.

Carrega o artefato linear (JSON) e produz estimativa pontual, intervalo de
confiança e cenários (pessimista/normal/otimista) a partir da climatologia.
Runtime depende apenas de numpy (sem sklearn/xgboost). Ver ADR-0006.
"""

from app.domain.yield_estimation.predictor import (
    RegionalYieldModel,
    Scenario,
    YieldEstimate,
)

__all__ = ["RegionalYieldModel", "YieldEstimate", "Scenario"]
