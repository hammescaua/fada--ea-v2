"""Domínio de benchmark — referência regional de custo (CONAB)."""

from __future__ import annotations

from app.domain.benchmark.cost import (
    COST_BAND_PCT,
    CostBenchmark,
    CostComparison,
    CostComponent,
    compare_cost,
)

__all__ = [
    "COST_BAND_PCT",
    "CostBenchmark",
    "CostComparison",
    "CostComponent",
    "compare_cost",
]
