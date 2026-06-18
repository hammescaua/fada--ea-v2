"""Sumários descritivos por talhão e estatísticas auxiliares (puras).

Estabilidade é medida sobre os resíduos AJUSTADOS AO CLIMA (desvio vs. expectativa
regional do ano), não sobre a produtividade bruta — um talhão não é "instável" só
porque o ano foi de seca para todos (ADR-0014).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSeasonRecord:
    """Uma safra de um talhão (dado real registrado)."""

    field_id: int
    field_name: str
    harvest_year: int
    area_ha: float
    actual_sc_ha: float
    regional_fitted_sc_ha: float
    cost_total: float | None = None
    n_applications: int = 0

    @property
    def rel_residual(self) -> float:
        """Desvio relativo vs. expectativa regional do ano (fração)."""
        return (self.actual_sc_ha - self.regional_fitted_sc_ha) / self.regional_fitted_sc_ha

    @property
    def cost_per_ha(self) -> float | None:
        if self.cost_total is None or self.area_ha <= 0:
            return None
        return self.cost_total / self.area_ha


@dataclass(frozen=True)
class FieldSummary:
    field_id: int
    field_name: str
    n_seasons: int
    mean_actual_sc_ha: float
    mean_rel_residual: float          # bias médio vs região (fração)
    yield_stability_std: float | None  # desvio dos resíduos relativos (None se n<2)
    mean_cost_per_ha: float | None
    n_seasons_with_cost: int
    latest_year: int
    latest_actual_sc_ha: float
    cost_trend: dict | None           # ver detect_trend

    @property
    def bias_percentage(self) -> float:
        return round(100 * self.mean_rel_residual, 1)


def detect_trend(series: list[tuple[int, float]], min_n: int = 3, threshold_pct: float = 10.0) -> dict | None:
    """Tendência determinística de uma série (ano, valor).

    Retorna None se n < min_n. Caso contrário: direção (rising/falling/stable),
    variação percentual líquida e se é estritamente monotônica (confiança maior).
    """
    if len(series) < min_n:
        return None
    s = sorted(series)
    values = [v for _, v in s]
    first, last = values[0], values[-1]
    if first == 0:
        return None
    net_pct = 100 * (last - first) / abs(first)
    ups = sum(1 for a, b in zip(values, values[1:]) if b > a)
    downs = sum(1 for a, b in zip(values, values[1:]) if b < a)
    monotonic = ups == len(values) - 1 or downs == len(values) - 1
    if net_pct > threshold_pct:
        direction = "rising"
    elif net_pct < -threshold_pct:
        direction = "falling"
    else:
        direction = "stable"
    return {
        "direction": direction, "net_change_pct": round(net_pct, 1),
        "monotonic": monotonic, "n": len(values),
        "first_year": s[0][0], "last_year": s[-1][0],
    }


def yield_anomaly_zscore(rel_residuals_history: list[float], min_n: int = 4) -> float | None:
    """Z-score do último resíduo relativo vs. a própria norma do talhão (None se n<min_n)."""
    if len(rel_residuals_history) < min_n:
        return None
    prior = rel_residuals_history[:-1]
    mu = statistics.fmean(prior)
    sd = statistics.stdev(prior)
    if sd == 0:
        return None
    return (rel_residuals_history[-1] - mu) / sd


def build_field_summary(records: list[FieldSeasonRecord]) -> FieldSummary:
    """Agrega as safras de UM talhão em um sumário descritivo."""
    recs = sorted(records, key=lambda r: r.harvest_year)
    rel = [r.rel_residual for r in recs]
    costs = [r.cost_per_ha for r in recs if r.cost_per_ha is not None]
    cost_series = [(r.harvest_year, r.cost_per_ha) for r in recs if r.cost_per_ha is not None]
    latest = recs[-1]
    return FieldSummary(
        field_id=latest.field_id,
        field_name=latest.field_name,
        n_seasons=len(recs),
        mean_actual_sc_ha=round(statistics.fmean(r.actual_sc_ha for r in recs), 1),
        mean_rel_residual=statistics.fmean(rel),
        yield_stability_std=round(statistics.stdev(rel), 4) if len(rel) >= 2 else None,
        mean_cost_per_ha=round(statistics.fmean(costs), 2) if costs else None,
        n_seasons_with_cost=len(costs),
        latest_year=latest.harvest_year,
        latest_actual_sc_ha=round(latest.actual_sc_ha, 1),
        cost_trend=detect_trend(cost_series) if len(cost_series) >= 3 else None,
    )
