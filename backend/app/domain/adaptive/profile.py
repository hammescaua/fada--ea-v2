"""Memória de desempenho da fazenda (estatísticas suficientes dos resíduos).

Materializa o que o FADA "aprendeu" sobre a fazenda. A política de encolhimento
(peso, intervalo) é aplicada na leitura a partir destes números — não embutida aqui
(reprodutível e com hiperparâmetros ajustáveis). Ver ADR-0012.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class FarmPerformanceProfile:
    """Resíduos acumulados da fazenda vs. expectativa regional (clima-condicionada).

    - ``mean_relative_residual``: bias multiplicativo observado (fração; ex.: 0.12 = +12%).
    - ``mean_residual_sc_ha`` / ``median_residual_sc_ha``: diagnóstico descritivo (sc/ha).
    - ``variance_relative``: variância dos resíduos relativos (consistência da fazenda).
    """

    farm_id: int
    number_of_cycles: int
    mean_relative_residual: float
    mean_residual_sc_ha: float
    median_residual_sc_ha: float
    variance_relative: float
    last_updated: datetime | None = None
    id: int | None = None

    @property
    def bias_percentage(self) -> float:
        return round(100 * self.mean_relative_residual, 1)
