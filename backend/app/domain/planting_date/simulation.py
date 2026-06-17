"""Backtest climatológico de data de plantio e otimização robusta.

Para uma data de plantio, rejogamos essa data contra cada ano histórico do
município (features já recolocadas pela fenologia GDD) e obtemos uma *distribuição*
de produtividade. Dela extraímos esperado, cenários, intervalo e risco. A otimização
ranqueia por um equivalente-certeza com aversão a risco (ADR-0008), não por máxima
produtividade.

Funções puras: recebem features pré-computadas e o modelo; não fazem I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.domain.features import SOYBEAN_FEATURE_NAMES
from app.domain.units import kg_per_ha_to_bags_per_ha

# Aversão a risco default no equivalente-certeza (0 = neutro, ~1 = conservador).
DEFAULT_RISK_AVERSION = 0.5


@dataclass(frozen=True)
class PlantingDateOutcome:
    planting_date: str
    within_zarc: bool
    n_years: int
    expected_sc_ha: float           # mediana da distribuição climatológica
    interval_sc_ha: tuple[float, float]
    pessimista_sc_ha: float         # P10 entre anos
    normal_sc_ha: float             # P50
    otimista_sc_ha: float           # P90
    downside_sc_ha: float           # P10 (robustez)
    stability_sc_ha: float          # IQR (menor = mais estável)
    risk_score: float               # equivalente-certeza (maior = melhor)
    risk_drivers: dict[str, float] = field(default_factory=dict)


def _predict_distribution(
    model, per_year_features: list[dict[str, float]], harvest_year: int
) -> np.ndarray:
    """Produtividade prevista (sc/ha) para cada ano histórico, na data dada."""
    out = []
    for f in per_year_features:
        fv = {name: f[name] for name in SOYBEAN_FEATURE_NAMES}
        fv["harvest_year"] = harvest_year
        out.append(kg_per_ha_to_bags_per_ha(model.predict_kg_ha(fv)))
    return np.array(out, dtype=float)


def simulate_planting_date(
    model,
    per_year_features: list[dict[str, float]],
    harvest_year: int,
    planting_date: str,
    within_zarc: bool,
    risk_aversion: float = DEFAULT_RISK_AVERSION,
) -> PlantingDateOutcome:
    preds = _predict_distribution(model, per_year_features, harvest_year)
    p10, p50, p90 = (float(np.percentile(preds, p)) for p in (10, 50, 90))
    p25, p75 = float(np.percentile(preds, 25)), float(np.percentile(preds, 75))

    rq = model._a["residual_scha_quantiles"]
    interval = (round(p50 + rq["p10"], 1), round(p50 + rq["p90"], 1))

    # Equivalente-certeza: penaliza o downside (mediana − P10).
    risk_score = round(p50 - risk_aversion * (p50 - p10), 2)

    deficit = np.array([f["water_deficit_reproductive_mm"] for f in per_year_features])
    dry = np.array([f["dry_spell_longest_reproductive_days"] for f in per_year_features])
    hot = np.array([f["hot_days_reproductive"] for f in per_year_features])

    return PlantingDateOutcome(
        planting_date=planting_date,
        within_zarc=within_zarc,
        n_years=len(preds),
        expected_sc_ha=round(p50, 1),
        interval_sc_ha=interval,
        pessimista_sc_ha=round(p10, 1),
        normal_sc_ha=round(p50, 1),
        otimista_sc_ha=round(p90, 1),
        downside_sc_ha=round(p10, 1),
        stability_sc_ha=round(p75 - p25, 1),
        risk_score=risk_score,
        risk_drivers={
            "deficit_reprodutivo_mediano_mm": round(float(np.median(deficit)), 1),
            "deficit_reprodutivo_adverso_mm": round(float(np.percentile(deficit, 90)), 1),
            "veranico_adverso_dias": round(float(np.percentile(dry, 90)), 1),
            "dias_quentes_adversos": round(float(np.percentile(hot, 90)), 1),
        },
    )


def optimize_planting_window(
    model,
    grid: dict[str, list[dict[str, float]]],
    harvest_year: int,
    zarc: dict[str, bool],
    risk_aversion: float = DEFAULT_RISK_AVERSION,
    top_n: int = 5,
) -> list[PlantingDateOutcome]:
    """Avalia todas as datas-grid dentro do ZARC e ranqueia por equivalente-certeza.

    Args:
        grid: {data_iso: features_por_ano}.
        zarc: {data_iso: dentro_do_zarc}.
    """
    outcomes = [
        simulate_planting_date(
            model, feats, harvest_year, d, zarc.get(d, False), risk_aversion
        )
        for d, feats in grid.items()
        if zarc.get(d, False)  # restrição dura do ZARC
    ]
    outcomes.sort(key=lambda o: o.risk_score, reverse=True)
    return outcomes[:top_n]
