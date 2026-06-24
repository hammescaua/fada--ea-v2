"""Aplica o ajuste agronômico (a priori) à estimativa regional — puro.

Desloca o ponto pela multiplicação do perfil e **alarga** o intervalo: o ajuste a
priori adiciona incerteza (não a remove). Espelha a disciplina do shrinkage
(ADR-0012): personalização nunca estreita artificialmente a faixa.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.agronomy.profile import AdjustmentResult

# Incerteza relativa do ajuste a priori: piso de 5% + 25% do |efeito total|.
_PROFILE_SE_FLOOR = 0.05
_PROFILE_SE_SLOPE = 0.25


@dataclass(frozen=True)
class PersonalizedEstimate:
    regional_point_sc_ha: float
    regional_interval_sc_ha: tuple[float, float]
    personalized_point_sc_ha: float
    personalized_interval_sc_ha: tuple[float, float]
    multiplier: float
    total_effect_pct: float
    scenarios_sc_ha: dict[str, float]


def apply_adjustment(
    regional_point_sc_ha: float,
    regional_interval_sc_ha: tuple[float, float],
    scenarios_sc_ha: dict[str, float],
    adjustment: AdjustmentResult,
) -> PersonalizedEstimate:
    m = adjustment.multiplier
    point = regional_point_sc_ha * m

    lo, hi = regional_interval_sc_ha
    h_reg = (hi - lo) / 2.0
    rel_se = _PROFILE_SE_FLOOR + _PROFILE_SE_SLOPE * abs(m - 1.0)
    abs_se = point * rel_se
    h = math.sqrt(h_reg ** 2 + abs_se ** 2)

    return PersonalizedEstimate(
        regional_point_sc_ha=round(regional_point_sc_ha, 1),
        regional_interval_sc_ha=(round(lo, 1), round(hi, 1)),
        personalized_point_sc_ha=round(point, 1),
        personalized_interval_sc_ha=(round(point - h, 1), round(point + h, 1)),
        multiplier=m,
        total_effect_pct=adjustment.total_effect_pct,
        scenarios_sc_ha={name: round(y * m, 1) for name, y in scenarios_sc_ha.items()},
    )
