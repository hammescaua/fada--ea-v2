"""Climate — índices agroclimáticos determinísticos.

Funções puras sobre séries diárias de clima (sem I/O). São os *features* base que
alimentam a estimativa de produtividade e a análise de risco.
"""

from app.domain.climate.indices import (
    DailyWeather,
    DrySpellSummary,
    accumulated_rainfall,
    dry_spells,
    growing_degree_days,
    simple_water_deficit,
)

__all__ = [
    "DailyWeather",
    "DrySpellSummary",
    "growing_degree_days",
    "accumulated_rainfall",
    "dry_spells",
    "simple_water_deficit",
]
