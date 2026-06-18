"""Encolhimento hierárquico (Normal-Normal, prior fixo) — o núcleo científico.

Modelo: o bias multiplicativo verdadeiro da fazenda b ~ Normal(0, tau²); cada resíduo
observado r_i ~ Normal(b, s²). A média posterior encolhe a média amostral para 0
(regional) com peso w = n/(n+k), k = s²/tau². A incerteza da estimativa do bias é
adicionada ao intervalo regional — que nunca encolhe artificialmente (ADR-0012).

Funções puras e determinísticas. ``statistics``/``math`` apenas.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class ShrinkagePrior:
    """Hiperparâmetros do prior (ajustáveis; ver ADR-0012 para os defaults)."""

    tau: float = 0.07          # desvio típico ENTRE fazendas (prior, fração)
    sigma0: float = 0.20       # desvio do resíduo de UMA observação (prior, fração)
    nu0: float = 5.0           # força do prior sobre a variância (pseudo-observações)


@dataclass(frozen=True)
class ProfileStats:
    n: int
    mean_relative_residual: float
    mean_residual_sc_ha: float
    median_residual_sc_ha: float
    variance_relative: float


@dataclass(frozen=True)
class PersonalizedPrediction:
    regional_point_sc_ha: float
    regional_interval_sc_ha: tuple[float, float]
    personalized_point_sc_ha: float
    personalized_interval_sc_ha: tuple[float, float]
    farm_adjustment_pct: float          # bias aplicado (encolhido), em %
    observed_bias_pct: float            # bias bruto observado, em %
    confidence_score: float             # peso w ∈ [0,1]
    adaptation_level: str
    n_cycles: int
    scenarios_sc_ha: dict[str, float]


def compute_profile_stats(
    residuals_relative: list[float], residuals_sc_ha: list[float]
) -> ProfileStats:
    """Estatísticas suficientes a partir dos resíduos (clima-condicionados)."""
    n = len(residuals_relative)
    if n == 0:
        return ProfileStats(0, 0.0, 0.0, 0.0, 0.0)
    return ProfileStats(
        n=n,
        mean_relative_residual=statistics.fmean(residuals_relative),
        mean_residual_sc_ha=statistics.fmean(residuals_sc_ha),
        median_residual_sc_ha=statistics.median(residuals_sc_ha),
        variance_relative=statistics.variance(residuals_relative) if n >= 2 else 0.0,
    )


def _regularized_within_var(n: int, variance_relative: float, prior: ShrinkagePrior) -> float:
    """Variância do resíduo de uma observação, regularizada pelo prior.

    Com n<2 não há variância amostral -> usa o prior. Caso contrário, mistura o
    prior (nu0 pseudo-obs de sigma0²) com a variância observada.
    """
    if n < 2:
        return prior.sigma0 ** 2
    return (prior.nu0 * prior.sigma0 ** 2 + (n - 1) * variance_relative) / (prior.nu0 + (n - 1))


def shrinkage_weight(
    n: int, variance_relative: float, prior: ShrinkagePrior
) -> tuple[float, float]:
    """Retorna (w, se_bias): peso de confiança e desvio-padrão posterior do bias."""
    if n <= 0:
        # Sem dados: fallback neutro ao regional (nenhuma correção, nenhuma incerteza
        # adicional além da regional). A partir de n>=1 o bias passa a ser estimado.
        return 0.0, 0.0
    s2 = _regularized_within_var(n, variance_relative, prior)
    tau2 = prior.tau ** 2
    k = s2 / tau2
    w = n / (n + k)
    posterior_var = 1.0 / (n / s2 + 1.0 / tau2)  # Normal-Normal
    return w, math.sqrt(posterior_var)


def adaptation_level(w: float) -> str:
    if w < 0.15:
        return "nenhuma"
    if w < 0.40:
        return "baixa"
    if w < 0.70:
        return "moderada"
    return "alta"


def personalize(
    regional_point_sc_ha: float,
    regional_interval_sc_ha: tuple[float, float],
    scenarios_sc_ha: dict[str, float],
    n_cycles: int,
    observed_bias: float,
    variance_relative: float,
    prior: ShrinkagePrior | None = None,
) -> PersonalizedPrediction:
    """Aplica a correção encolhida ao regional, preservando a incerteza.

    Args:
        observed_bias: média relativa dos resíduos (fração). 0 se sem dados.
    """
    prior = prior or ShrinkagePrior()
    w, se_bias = shrinkage_weight(n_cycles, variance_relative, prior)
    shrunk_bias = w * observed_bias

    point = round(regional_point_sc_ha * (1.0 + shrunk_bias), 1)

    lo, hi = regional_interval_sc_ha
    h_reg = (hi - lo) / 2.0
    abs_se = regional_point_sc_ha * se_bias
    # Largura climática regional (irredutível) + incerteza da estimativa do bias.
    h_pers = math.sqrt(h_reg ** 2 + abs_se ** 2)
    interval = (round(point - h_pers, 1), round(point + h_pers, 1))

    scenarios = {name: round(y * (1.0 + shrunk_bias), 1) for name, y in scenarios_sc_ha.items()}

    return PersonalizedPrediction(
        regional_point_sc_ha=round(regional_point_sc_ha, 1),
        regional_interval_sc_ha=(round(lo, 1), round(hi, 1)),
        personalized_point_sc_ha=point,
        personalized_interval_sc_ha=interval,
        farm_adjustment_pct=round(100 * shrunk_bias, 1),
        observed_bias_pct=round(100 * observed_bias, 1),
        confidence_score=round(w, 3),
        adaptation_level=adaptation_level(w),
        n_cycles=n_cycles,
        scenarios_sc_ha=scenarios,
    )
