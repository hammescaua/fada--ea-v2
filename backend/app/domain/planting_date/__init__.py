"""Planting date — análise What-If de data de plantio.

Domínio determinístico que recoloca as janelas fenológicas em função da data de
plantio (tempo térmico / GDD) e agrega o backtest climatológico em produtividade
esperada, cenários, intervalo e risco. Ver ADR-0007 e ADR-0008.
"""

from app.domain.planting_date.phenology import PhenologyModel, SOYBEAN_PHENOLOGY_RS
from app.domain.planting_date.simulation import (
    PlantingDateOutcome,
    optimize_planting_window,
    simulate_planting_date,
)

__all__ = [
    "PhenologyModel",
    "SOYBEAN_PHENOLOGY_RS",
    "PlantingDateOutcome",
    "simulate_planting_date",
    "optimize_planting_window",
]
