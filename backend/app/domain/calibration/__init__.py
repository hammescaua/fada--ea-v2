"""Calibration — avalia se os intervalos do FADA são honestos (ADR-0013).

Mede (não altera) a calibração: cobertura com CI de Wilson, sharpness, curva de
confiabilidade, pinball loss e a garantia de que a personalização nunca reduz a
largura do intervalo. Funções puras e determinísticas, sem I/O, sem LLM.

CRPS foi deliberadamente descartado (redundante com pinball+cobertura — ADR-0013).
"""

from app.domain.calibration.metrics import (
    CoverageResult,
    coverage,
    personalized_halfwidth,
    pinball_loss,
    point_errors,
    reliability_curve,
    sharpness,
    width_never_decreases,
    wilson_interval,
)
from app.domain.calibration.report import CalibrationReport, build_report, interpret

__all__ = [
    "CoverageResult",
    "coverage",
    "wilson_interval",
    "sharpness",
    "point_errors",
    "pinball_loss",
    "reliability_curve",
    "personalized_halfwidth",
    "width_never_decreases",
    "CalibrationReport",
    "build_report",
    "interpret",
]
