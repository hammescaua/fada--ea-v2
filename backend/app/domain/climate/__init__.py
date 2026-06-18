"""Climate — índices agroclimáticos determinísticos.

Funções puras sobre séries diárias de clima (sem I/O). São os *features* base que
alimentam a estimativa de produtividade e a análise de risco.
"""

from app.domain.climate.indices import (
    DailyWeather,
    DrySpellSummary,
    accumulated_rainfall,
    days_above,
    dry_spells,
    growing_degree_days,
    hargreaves_et0,
    simple_water_deficit,
    with_hargreaves_et0,
)

__all__ = [
    "DailyWeather",
    "DrySpellSummary",
    "growing_degree_days",
    "accumulated_rainfall",
    "dry_spells",
    "days_above",
    "hargreaves_et0",
    "with_hargreaves_et0",
    "simple_water_deficit",
]
