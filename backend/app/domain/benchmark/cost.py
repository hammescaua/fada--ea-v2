"""Domínio de benchmark de custo — referência regional CONAB (sem juízo de valor).

Representa o custo de produção *de referência* (R$/ha) publicado pela CONAB para
uma cultura/UF/safra, nos três conceitos canônicos:

- **COE** (Custo Operacional Efetivo): desembolso de caixa (insumos, operações…).
- **COT** (Custo Operacional Total): COE + depreciações.
- **CT**  (Custo Total): COT + renda dos fatores (terra, remuneração do capital).

A comparação contra o custo real do produtor é **descritiva e honesta**: a
referência é de safra inteira; o sinal só vira "acima/abaixo" fora de uma banda de
tolerância. Funções puras e determinísticas — sem I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

# Dentro de ±10% da referência tratamos como "na média" — evita falsa precisão.
COST_BAND_PCT = 10.0


@dataclass(frozen=True)
class CostComponent:
    item: str
    value_per_ha: float
    share_pct: float


@dataclass(frozen=True)
class CostBenchmark:
    crop: str
    uf: str
    safra: str
    technology: str
    source: str          # "CONAB"
    fetched_at: str      # ISO date (proveniência)
    coe_per_ha: float
    cot_per_ha: float
    ct_per_ha: float
    components: tuple[CostComponent, ...]


@dataclass(frozen=True)
class CostComparison:
    actual_per_ha: float
    reference_label: str       # ex.: "COE (custo de caixa)"
    reference_per_ha: float
    delta_per_ha: float        # actual - reference
    ratio_pct: float           # actual / reference * 100
    descriptor: str            # "abaixo" | "na média" | "acima"


def compare_cost(
    actual_per_ha: float, reference_per_ha: float, reference_label: str
) -> CostComparison:
    """Compara o custo real do produtor com uma referência regional. Puro."""
    ratio = 0.0 if reference_per_ha == 0 else actual_per_ha / reference_per_ha * 100.0
    delta = actual_per_ha - reference_per_ha
    if ratio > 100 + COST_BAND_PCT:
        descriptor = "acima"
    elif ratio < 100 - COST_BAND_PCT:
        descriptor = "abaixo"
    else:
        descriptor = "na média"
    return CostComparison(
        actual_per_ha=round(actual_per_ha, 2),
        reference_label=reference_label,
        reference_per_ha=round(reference_per_ha, 2),
        delta_per_ha=round(delta, 2),
        ratio_pct=round(ratio, 1),
        descriptor=descriptor,
    )
