"""Calendário agrícola e janelas fenológicas.

Convenção de safra: a "safra 2026/27" é semeada no fim de 2026 e colhida no início
de 2027. O IBGE reporta a produção pelo **ano de colheita** (aqui, 2027). Portanto,
para um ``harvest_year`` Y:

- janela vegetativa  : out–dez de (Y−1)
- janela reprodutiva : ~21/dez (Y−1) a 28/fev (Y)  (R1–R6: floração a enchimento)
- janela da safra    : 01/out (Y−1) a 31/mar (Y)

As datas são padrões agronômicos para soja no Noroeste do RS, configuráveis por
cultura/região. Não há fenologia observada por talhão neste estágio (ADR-0003).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SeasonWindows:
    """Intervalos de datas concretos para um ano de colheita específico."""

    season: tuple[date, date]
    vegetative: tuple[date, date]
    reproductive: tuple[date, date]


@dataclass(frozen=True)
class CropCalendar:
    """Calendário relativo de uma cultura, definido por (mês, dia).

    Cada janela é (mês_início, dia_início, mês_fim, dia_fim) e ``*_prev_year`` indica
    se o início cai no ano anterior ao de colheita.
    """

    crop: str
    season_start: tuple[int, int]
    reproductive_start: tuple[int, int]
    reproductive_start_prev_year: bool
    reproductive_end: tuple[int, int]
    season_end: tuple[int, int]
    # Recomendação regional de semeadura (estilo ZARC) — (mês, dia)
    planting_window: tuple[tuple[int, int], tuple[int, int]]
    planting_optimal: tuple[tuple[int, int], tuple[int, int]]

    def windows_for(self, harvest_year: int) -> SeasonWindows:
        prev = harvest_year - 1
        season_start = date(prev, *self.season_start)
        repro_start_year = prev if self.reproductive_start_prev_year else harvest_year
        reproductive = (
            date(repro_start_year, *self.reproductive_start),
            date(harvest_year, *self.reproductive_end),
        )
        vegetative = (season_start, reproductive[0])
        season = (season_start, date(harvest_year, *self.season_end))
        return SeasonWindows(season=season, vegetative=vegetative, reproductive=reproductive)

    def planting_window_for(self, harvest_year: int) -> tuple[date, date]:
        prev = harvest_year - 1
        return (date(prev, *self.planting_window[0]), date(prev, *self.planting_window[1]))

    def planting_optimal_for(self, harvest_year: int) -> tuple[date, date]:
        prev = harvest_year - 1
        return (date(prev, *self.planting_optimal[0]), date(prev, *self.planting_optimal[1]))


# Soja, Noroeste do Rio Grande do Sul.
# Janela de semeadura coerente com o Zoneamento Agrícola de Risco Climático (ZARC)
# para a região; reprodutivo cobrindo enchimento de grãos (principal período crítico).
SOYBEAN_RS = CropCalendar(
    crop="soja",
    season_start=(10, 1),
    reproductive_start=(12, 21),
    reproductive_start_prev_year=True,
    reproductive_end=(2, 28),
    season_end=(3, 31),
    planting_window=((10, 11), (12, 10)),
    planting_optimal=((10, 21), (11, 20)),
)
