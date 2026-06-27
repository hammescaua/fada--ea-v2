"""Projeção plurianual de produtividade × rentabilidade (ADR-0031).

Honestidade: previsão de tempo real só existe para ~16 dias. Logo, a base
**climática** de cada safra futura é a *safra típica* da região (os 3 cenários
seco/normal/favorável), que **se repete** — não advinhamos o clima do ano X. O que
varia de safra para safra é o que o produtor assume: **preço** e **custo** (com
tendência anual opcional). A produtividade por cenário é a mesma; a rentabilidade
muda conforme essas suposições. Tudo determinístico.
"""

from __future__ import annotations

from dataclasses import dataclass


def next_seasons(base: str, n: int) -> list[str]:
    """Gera ``n`` rótulos de safra a partir de 'AAAA/AA' (ex.: '2026/27')."""
    start = int(base.split("/")[0])
    out: list[str] = []
    for i in range(n):
        y = start + i
        out.append(f"{y}/{str(y + 1)[-2:]}")
    return out


@dataclass(frozen=True)
class ScenarioEconomics:
    name: str
    yield_sc_ha: float
    price_per_bag: float
    revenue_per_ha: float
    profit_per_ha: float
    margin_pct: float


@dataclass(frozen=True)
class SeasonProjection:
    season: str
    year_index: int
    price_per_bag: float
    cost_per_ha: float
    scenarios: list[ScenarioEconomics]
    expected_profit_per_ha: float  # do cenário "normal" quando existir


def _trend(base_value: float, pct_per_year: float, year_index: int) -> float:
    return base_value * (1 + pct_per_year / 100) ** year_index


def project_economics(
    yield_scenarios: dict[str, float],
    base_price_per_bag: float,
    base_cost_per_ha: float,
    season: str,
    year_index: int,
    price_trend_pct: float = 0.0,
    cost_trend_pct: float = 0.0,
) -> SeasonProjection:
    """Rentabilidade de uma safra por cenário, com preço/custo (e tendência) do produtor."""
    if base_price_per_bag < 0 or base_cost_per_ha < 0:
        raise ValueError("preço e custo não podem ser negativos")
    price = _trend(base_price_per_bag, price_trend_pct, year_index)
    cost = _trend(base_cost_per_ha, cost_trend_pct, year_index)
    scns: list[ScenarioEconomics] = []
    for name, y in yield_scenarios.items():
        revenue = y * price
        profit = revenue - cost
        scns.append(
            ScenarioEconomics(
                name=name,
                yield_sc_ha=round(y, 1),
                price_per_bag=round(price, 2),
                revenue_per_ha=round(revenue, 2),
                profit_per_ha=round(profit, 2),
                margin_pct=round(100 * profit / revenue, 1) if revenue else 0.0,
            )
        )
    expected = next((s.profit_per_ha for s in scns if s.name == "normal"), scns[0].profit_per_ha)
    return SeasonProjection(
        season=season,
        year_index=year_index,
        price_per_bag=round(price, 2),
        cost_per_ha=round(cost, 2),
        scenarios=scns,
        expected_profit_per_ha=expected,
    )
