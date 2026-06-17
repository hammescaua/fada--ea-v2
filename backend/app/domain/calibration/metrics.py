"""Métricas de calibração e sharpness (puras).

Convenções:
- ``actuals``, ``lowers``, ``uppers``, ``points`` são listas alinhadas (sc/ha).
- Cobertura observada vem com **intervalo de Wilson** — a própria métrica tem
  incerteza amostral; só declaramos over/underconfidence se o CI exclui o nominal.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC de Wilson para uma proporção (mais honesto que normal em caudas/n pequeno)."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


@dataclass(frozen=True)
class CoverageResult:
    nominal: float
    observed: float
    wilson_low: float
    wilson_high: float
    n: int
    verdict: str  # "calibrado" | "overconfident" | "underconfident"


def coverage(
    actuals: list[float], lowers: list[float], uppers: list[float], nominal: float
) -> CoverageResult:
    """Fração de observações dentro de [lower, upper], com veredito significativo."""
    n = len(actuals)
    inside = sum(1 for a, lo, hi in zip(actuals, lowers, uppers, strict=True) if lo <= a <= hi)
    observed = inside / n if n else 0.0
    wlo, whi = wilson_interval(inside, n)
    if whi < nominal:
        verdict = "overconfident"   # significativamente abaixo -> intervalos estreitos demais
    elif wlo > nominal:
        verdict = "underconfident"  # significativamente acima -> largos demais
    else:
        verdict = "calibrado"
    return CoverageResult(nominal, round(observed, 4), round(wlo, 4), round(whi, 4), n, verdict)


def sharpness(lowers: list[float], uppers: list[float], reference: list[float]) -> dict:
    """Largura dos intervalos (utilidade). ``reference`` = produtividade média (escala)."""
    widths = [hi - lo for lo, hi in zip(lowers, uppers, strict=True)]
    mean_w = statistics.fmean(widths)
    ref = statistics.fmean(reference) if reference else 0.0
    return {
        "mean_width": round(mean_w, 2),
        "median_width": round(statistics.median(widths), 2),
        "relative_width_pct": round(100 * mean_w / ref, 1) if ref else 0.0,
    }


def point_errors(actuals: list[float], points: list[float]) -> dict:
    """MAE, RMSE e bias (sinal). bias>0 => o sistema super-prevê na média."""
    errs = [p - a for a, p in zip(actuals, points, strict=True)]
    return {
        "mae": round(statistics.fmean(abs(e) for e in errs), 2),
        "rmse": round(math.sqrt(statistics.fmean(e * e for e in errs)), 2),
        "bias": round(statistics.fmean(errs), 2),
    }


def pinball_loss(actuals: list[float], quantile_preds: list[float], tau: float) -> float:
    """Pinball (quantile) loss no nível tau — proper scoring rule para quantis."""
    losses = []
    for a, q in zip(actuals, quantile_preds, strict=True):
        losses.append(tau * (a - q) if a >= q else (1 - tau) * (q - a))
    return round(statistics.fmean(losses), 3)


def reliability_curve(
    actuals: list[float], intervals_by_level: dict[float, tuple[list[float], list[float]]]
) -> list[dict]:
    """Curva esperado×observado: para cada nível nominal, a cobertura observada."""
    curve = []
    for level in sorted(intervals_by_level):
        los, his = intervals_by_level[level]
        cr = coverage(actuals, los, his, level)
        curve.append({
            "nominal": level, "observed": cr.observed,
            "wilson_low": cr.wilson_low, "wilson_high": cr.wilson_high,
        })
    return curve


# --- Garantia: a personalização nunca reduz a largura do intervalo (ADR-0012/0013) ---

def personalized_halfwidth(regional_halfwidth: float, point_regional: float, se_bias: float) -> float:
    """Meia-largura personalizada = √(reg² + (ponto·SE_bias)²) ≥ reg, por construção."""
    return math.sqrt(regional_halfwidth ** 2 + (point_regional * se_bias) ** 2)


def width_never_decreases(
    regional_halfwidth: float, point_regional: float, se_bias: float
) -> bool:
    """Verdadeiro sse a meia-largura personalizada ≥ a regional (incerteza não diminui)."""
    return personalized_halfwidth(regional_halfwidth, point_regional, se_bias) >= (
        regional_halfwidth - 1e-12
    )
