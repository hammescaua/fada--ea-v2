"""Serviço de benchmark: custo de referência regional (CONAB) e comparação honesta.

Lê o artefato destilado e devolve os três custos canônicos (COE/COT/CT) por ha,
componentes principais, e — quando dado o custo real do produtor — uma comparação
descritiva contra cada referência. A referência é de **safra inteira**; o serviço
comunica isso e nunca emite um juízo categórico dentro da banda de tolerância.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.data.connectors.cost_benchmark import CostBenchmarkStore
from app.domain.benchmark import CostBenchmark, compare_cost


class BenchmarkUnavailable(Exception):
    """Não há artefato de benchmark para a cultura/UF (fonte não coletada ainda)."""


_REFERENCES = (
    ("coe", "COE — custo operacional efetivo (caixa)", "coe_per_ha"),
    ("cot", "COT — custo operacional total (+ depreciações)", "cot_per_ha"),
    ("ct", "CT — custo total (+ renda dos fatores)", "ct_per_ha"),
)


@dataclass
class BenchmarkService:
    store: CostBenchmarkStore = field(default_factory=CostBenchmarkStore)

    def _benchmark(self, crop: str, uf: str) -> CostBenchmark:
        b = self.store.load(crop, uf)
        if b is None:
            raise BenchmarkUnavailable(f"{crop}/{uf}")
        return b

    def cost_benchmark(self, crop: str = "soja", uf: str = "RS") -> dict:
        b = self._benchmark(crop, uf)
        return {**_header(b), "components": list(b.components), "disclaimer": _disclaimer(b)}

    def compare_cost(
        self, actual_per_ha: float, crop: str = "soja", uf: str = "RS"
    ) -> dict:
        b = self._benchmark(crop, uf)
        references = {
            key: compare_cost(actual_per_ha, getattr(b, attr), label)
            for key, label, attr in _REFERENCES
        }
        return {
            **_header(b),
            "actual_cost_per_ha": round(actual_per_ha, 2),
            "references": references,
            "primary": "coe",  # caixa é o que o produtor costuma registrar
            "components": list(b.components),
            "disclaimer": _disclaimer(b),
        }


def _header(b: CostBenchmark) -> dict:
    return {
        "crop": b.crop,
        "uf": b.uf,
        "safra": b.safra,
        "technology": b.technology,
        "source": b.source,
        "fetched_at": b.fetched_at,
        "coe_per_ha": b.coe_per_ha,
        "cot_per_ha": b.cot_per_ha,
        "ct_per_ha": b.ct_per_ha,
    }


def _disclaimer(b: CostBenchmark) -> str:
    return (
        f"Referência {b.source} para soja/{b.uf}, safra {b.safra}, tecnologia "
        f"{b.technology} — custo de **safra inteira**. Compare com seu custo total; "
        "comparações no meio da safra refletem o quanto já foi desembolsado, "
        "não eficiência."
    )
