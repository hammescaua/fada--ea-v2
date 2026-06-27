"""Comparação de margem entre opções de 2ª safra / inverno (ADR-0030).

No Noroeste RS a soja de verão é seguida por uma decisão de inverno/2ª safra
(trigo, milho 2ª safra, aveia/cobertura...). Aqui só comparamos **margem por ha**
de forma determinística a partir de produtividade, preço e custo — números que o
produtor informa (ou referências citadas que ele confirma). Sem previsão mágica.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CropOption:
    name: str
    yield_sc_ha: float
    price_per_bag: float
    cost_per_ha: float


@dataclass(frozen=True)
class CropMargin:
    name: str
    revenue_per_ha: float
    cost_per_ha: float
    margin_per_ha: float
    break_even_sc_ha: float | None
    rank: int


def compare_options(options: list[CropOption]) -> list[CropMargin]:
    """Margem por ha de cada opção, ordenada da melhor para a pior."""
    if not options:
        return []
    computed: list[CropMargin] = []
    for o in options:
        if o.yield_sc_ha < 0 or o.price_per_bag < 0 or o.cost_per_ha < 0:
            raise ValueError("valores não podem ser negativos")
        revenue = o.yield_sc_ha * o.price_per_bag
        margin = revenue - o.cost_per_ha
        break_even = (
            round(o.cost_per_ha / o.price_per_bag, 1) if o.price_per_bag > 0 else None
        )
        computed.append(
            CropMargin(
                name=o.name,
                revenue_per_ha=round(revenue, 2),
                cost_per_ha=round(o.cost_per_ha, 2),
                margin_per_ha=round(margin, 2),
                break_even_sc_ha=break_even,
                rank=0,
            )
        )
    ordered = sorted(computed, key=lambda c: c.margin_per_ha, reverse=True)
    return [
        CropMargin(
            name=c.name,
            revenue_per_ha=c.revenue_per_ha,
            cost_per_ha=c.cost_per_ha,
            margin_per_ha=c.margin_per_ha,
            break_even_sc_ha=c.break_even_sc_ha,
            rank=idx + 1,
        )
        for idx, c in enumerate(ordered)
    ]
