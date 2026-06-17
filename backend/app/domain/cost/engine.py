"""Cost Engine — cálculos financeiros determinísticos sobre a timeline de eventos.

Convenções:
- ``cost`` de cada evento é o custo total daquela operação (R$).
- ``price_per_bag`` (R$/sc) é informado pelo produtor (preço spot), não previsto.
- Pré-colheita, custo/saca e cenários usam a produtividade *esperada* do modelo;
  pós-colheita, a produtividade real do CropCycle.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.domain.farm import AgriculturalEvent


@dataclass(frozen=True)
class CostBreakdown:
    total_cost: float
    area_ha: float
    cost_per_hectare: float
    cost_per_bag: float | None       # depende de uma produtividade (real ou esperada)
    yield_sc_ha: float | None
    n_applications: int
    cost_by_category: dict[str, float]


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    yield_sc_ha: float
    price_per_bag: float
    revenue: float
    total_cost: float
    profit: float
    margin_pct: float
    profit_per_hectare: float


def calculate_total_cost(events: list[AgriculturalEvent]) -> float:
    """Soma do custo de todos os eventos (R$). Eventos sem custo contam como 0."""
    return round(sum(e.cost or 0.0 for e in events), 2)


def calculate_cost_per_hectare(total_cost: float, area_ha: float) -> float:
    _require_positive(area_ha, "area_ha")
    return round(total_cost / area_ha, 2)


def calculate_cost_per_bag(total_cost: float, yield_sc_ha: float, area_ha: float) -> float:
    """Custo por saca = custo total / produção total (sc)."""
    _require_positive(area_ha, "area_ha")
    _require_positive(yield_sc_ha, "yield_sc_ha")
    total_production = yield_sc_ha * area_ha
    return round(total_cost / total_production, 2)


def calculate_break_even_yield(cost_per_hectare: float, price_per_bag: float) -> float:
    """Produtividade (sc/ha) necessária para empatar: custo/ha ÷ preço/saca."""
    _require_positive(price_per_bag, "price_per_bag")
    return round(cost_per_hectare / price_per_bag, 1)


def count_applications(events: list[AgriculturalEvent]) -> int:
    """Número de manejos (pulverizações/adubações)."""
    return sum(1 for e in events if e.is_application)


def _cost_by_category(events: list[AgriculturalEvent]) -> dict[str, float]:
    acc: Counter[str] = Counter()
    for e in events:
        acc[e.event_type.value] += e.cost or 0.0
    return {k: round(v, 2) for k, v in acc.items()}


def cost_breakdown(
    events: list[AgriculturalEvent], area_ha: float, yield_sc_ha: float | None
) -> CostBreakdown:
    """Consolida a timeline em um quadro de custos (estado derivado dos eventos)."""
    total = calculate_total_cost(events)
    return CostBreakdown(
        total_cost=total,
        area_ha=area_ha,
        cost_per_hectare=calculate_cost_per_hectare(total, area_ha),
        cost_per_bag=(
            calculate_cost_per_bag(total, yield_sc_ha, area_ha)
            if yield_sc_ha and yield_sc_ha > 0
            else None
        ),
        yield_sc_ha=yield_sc_ha,
        n_applications=count_applications(events),
        cost_by_category=_cost_by_category(events),
    )


def scenario_analysis(
    total_cost: float,
    area_ha: float,
    price_per_bag: float,
    yield_scenarios: dict[str, float],
) -> list[ScenarioResult]:
    """Lucro/margem por cenário de produtividade, a um preço informado.

    Args:
        yield_scenarios: {nome: produtividade sc/ha} (ex.: pessimista/normal/otimista).
    """
    _require_positive(area_ha, "area_ha")
    _require_positive(price_per_bag, "price_per_bag")
    results = []
    for name, y in yield_scenarios.items():
        revenue = round(y * area_ha * price_per_bag, 2)
        profit = round(revenue - total_cost, 2)
        results.append(
            ScenarioResult(
                name=name,
                yield_sc_ha=y,
                price_per_bag=price_per_bag,
                revenue=revenue,
                total_cost=total_cost,
                profit=profit,
                margin_pct=round(100 * profit / revenue, 1) if revenue else 0.0,
                profit_per_hectare=round(profit / area_ha, 2),
            )
        )
    return results


def _require_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} deve ser positivo (recebido: {value})")
