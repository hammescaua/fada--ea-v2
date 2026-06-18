"""CalibrationReport — artefato determinístico de calibração (sem LLM)."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass

from app.domain.calibration.metrics import (
    coverage,
    pinball_loss,
    point_errors,
    reliability_curve,
    sharpness,
)

# Níveis reportados como resumo legível (80% é o IC efetivamente comunicado).
CANONICAL_LEVELS = (0.5, 0.8, 0.9, 0.95)
HEADLINE_LEVEL = 0.8


@dataclass
class CalibrationReport:
    label: str
    n_predictions: int
    coverage_50: float
    coverage_80: float
    coverage_90: float
    coverage_95: float
    coverage_detail: list[dict]
    mean_width: float
    median_width: float
    relative_width_pct: float
    mae: float
    rmse: float
    bias: float
    pinball: dict
    reliability_curve: list[dict]
    overconfident: bool
    underconfident: bool
    interpretation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def build_report(
    label: str,
    actuals: list[float],
    points: list[float],
    intervals_by_level: dict[float, tuple[list[float], list[float]]],
    quantiles: dict[float, list[float]],
) -> CalibrationReport:
    """Monta o relatório a partir do backtest.

    Args:
        intervals_by_level: {nivel: (lowers, uppers)} — deve conter os níveis canônicos
            e os da curva de confiabilidade.
        quantiles: {tau: predicoes_no_quantil} para pinball (ex.: 0.1, 0.5, 0.9).
    """
    cov = {lvl: coverage(actuals, *intervals_by_level[lvl], lvl) for lvl in CANONICAL_LEVELS}
    headline = cov[HEADLINE_LEVEL]

    lo80, hi80 = intervals_by_level[HEADLINE_LEVEL]
    sharp = sharpness(lo80, hi80, actuals)
    pe = point_errors(actuals, points)
    pinball = {f"p{int(t * 100)}": pinball_loss(actuals, q, t) for t, q in quantiles.items()}
    pinball["mean"] = round(statistics.fmean(pinball.values()), 3)

    report = CalibrationReport(
        label=label,
        n_predictions=len(actuals),
        coverage_50=cov[0.5].observed,
        coverage_80=cov[0.8].observed,
        coverage_90=cov[0.9].observed,
        coverage_95=cov[0.95].observed,
        coverage_detail=[
            {
                "nominal": c.nominal, "observed": c.observed,
                "wilson_low": c.wilson_low, "wilson_high": c.wilson_high, "verdict": c.verdict,
            }
            for c in cov.values()
        ],
        mean_width=sharp["mean_width"],
        median_width=sharp["median_width"],
        relative_width_pct=sharp["relative_width_pct"],
        mae=pe["mae"], rmse=pe["rmse"], bias=pe["bias"],
        pinball=pinball,
        reliability_curve=reliability_curve(actuals, intervals_by_level),
        overconfident=headline.verdict == "overconfident",
        underconfident=headline.verdict == "underconfident",
    )
    report.interpretation = interpret(report)
    return report


def interpret(r: CalibrationReport) -> str:
    """Interpretação determinística (sem LLM)."""
    h = next(c for c in r.coverage_detail if c["nominal"] == HEADLINE_LEVEL)
    if r.overconfident:
        verdict = (f"OVERCONFIDENT: o IC80 cobriu apenas {h['observed']:.0%} (Wilson "
                   f"[{h['wilson_low']:.0%}, {h['wilson_high']:.0%}]), abaixo de 80% — "
                   f"os intervalos são estreitos demais.")
    elif r.underconfident:
        verdict = (f"UNDERCONFIDENT: o IC80 cobriu {h['observed']:.0%} (Wilson "
                   f"[{h['wilson_low']:.0%}, {h['wilson_high']:.0%}]), acima de 80% — "
                   f"os intervalos são largos demais (pouco úteis).")
    else:
        verdict = (f"CALIBRADO: o IC80 cobriu {h['observed']:.0%} (Wilson "
                   f"[{h['wilson_low']:.0%}, {h['wilson_high']:.0%}]), consistente com 80% "
                   f"dentro do erro amostral.")
    bias_dir = ("tende a super-prever" if r.bias > 0 else
                "tende a sub-prever" if r.bias < 0 else "sem viés sistemático")
    return (
        f"[{r.label}] {r.n_predictions} predições (backtest leave-one-year-out). {verdict} "
        f"Largura média do IC80: {r.mean_width} sc/ha (~{r.relative_width_pct}% da "
        f"produtividade). MAE {r.mae} · RMSE {r.rmse} sc/ha · bias {r.bias:+} sc/ha "
        f"({bias_dir})."
    )
