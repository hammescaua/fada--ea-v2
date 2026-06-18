"""Insights — análise descritiva por talhão + Insight Engine determinístico.

Sem cultivar (confundimento), sem shrinkage por talhão (fome de dados), sem LLM
gerando números (ADR-0014). Tudo determinístico, com *evidence gating*: nenhum
insight é emitido sem N suficiente e tamanho de efeito explícito.
"""

from app.domain.insights.summary import (
    FieldSeasonRecord,
    FieldSummary,
    build_field_summary,
    detect_trend,
    yield_anomaly_zscore,
)
from app.domain.insights.engine import Insight, generate_insights

__all__ = [
    "FieldSeasonRecord",
    "FieldSummary",
    "build_field_summary",
    "detect_trend",
    "yield_anomaly_zscore",
    "Insight",
    "generate_insights",
]
