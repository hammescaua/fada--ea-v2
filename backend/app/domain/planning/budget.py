"""Orçamento: planejado x realizado e agenda (determinístico, sem LLM).

Reusa o Cost Engine para o lado realizado. O planejado vem de PlannedEvent +
campos de plano do CropCycle (ADR-0015).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from app.domain.cost import calculate_total_cost, count_applications
from app.domain.farm import AgriculturalEvent
from app.domain.planning.entities import PlannedEvent


@dataclass(frozen=True)
class PlanVsActual:
    planned_total_cost: float
    actual_total_cost: float
    cost_variance: float            # realizado − planejado (>0 = acima do orçamento)
    cost_variance_pct: float | None
    pct_budget_spent: float | None  # realizado / planejado
    remaining_budget: float         # planejado − realizado ("quanto falta investir")
    over_budget: bool
    area_ha: float | None
    planned_cost_per_ha: float | None
    actual_cost_per_ha: float | None
    planned_applications: int
    actual_applications: int
    expected_revenue: float | None
    expected_profit: float | None


@dataclass(frozen=True)
class AgendaItem:
    planned_event_id: int | None
    event_type: str
    planned_date: str
    product_name: str | None
    expected_cost: float | None
    status: str  # "concluída" | "atrasada" | "próxima"


def compute_plan_vs_actual(
    planned_events: list[PlannedEvent],
    actual_events: list[AgriculturalEvent],
    area_ha: float | None,
    target_yield_sc_ha: float | None,
    expected_price_per_bag: float | None,
) -> PlanVsActual:
    planned_total = round(sum(p.expected_cost or 0.0 for p in planned_events), 2)
    actual_total = calculate_total_cost(actual_events)
    variance = round(actual_total - planned_total, 2)

    expected_revenue = expected_profit = None
    if area_ha and target_yield_sc_ha and expected_price_per_bag:
        expected_revenue = round(target_yield_sc_ha * area_ha * expected_price_per_bag, 2)
        expected_profit = round(expected_revenue - planned_total, 2)

    return PlanVsActual(
        planned_total_cost=planned_total,
        actual_total_cost=actual_total,
        cost_variance=variance,
        cost_variance_pct=round(100 * variance / planned_total, 1) if planned_total else None,
        pct_budget_spent=round(100 * actual_total / planned_total, 1) if planned_total else None,
        remaining_budget=round(planned_total - actual_total, 2),
        over_budget=actual_total > planned_total,
        area_ha=area_ha,
        planned_cost_per_ha=round(planned_total / area_ha, 2) if area_ha else None,
        actual_cost_per_ha=round(actual_total / area_ha, 2) if area_ha else None,
        planned_applications=sum(1 for p in planned_events if p.is_application),
        actual_applications=count_applications(actual_events),
        expected_revenue=expected_revenue,
        expected_profit=expected_profit,
    )


def build_agenda(
    planned_events: list[PlannedEvent],
    actual_events: list[AgriculturalEvent],
    today: date,
) -> list[AgendaItem]:
    """Agenda derivada do plano: reconciliação por contagem de tipo (sem matching frágil).

    Para cada tipo, os k primeiros planejados (por data) são "concluídos" se há ao
    menos k eventos reais daquele tipo; o restante é "atrasada" (data passada) ou
    "próxima".
    """
    actual_count: dict[str, int] = defaultdict(int)
    for e in actual_events:
        actual_count[e.event_type.value] += 1

    seen: dict[str, int] = defaultdict(int)
    items: list[AgendaItem] = []
    for p in sorted(planned_events, key=lambda x: x.planned_date):
        et = p.event_type.value
        rank = seen[et]
        seen[et] += 1
        if rank < actual_count[et]:
            status = "concluída"
        elif p.planned_date < today:
            status = "atrasada"
        else:
            status = "próxima"
        items.append(AgendaItem(
            planned_event_id=p.id, event_type=et,
            planned_date=p.planned_date.isoformat(), product_name=p.product_name,
            expected_cost=p.expected_cost, status=status,
        ))
    return items
