"""Caso de uso financeiro: consolida a timeline em custos e cenários de lucro.

Integra o Cost Engine (determinístico) com a timeline de eventos e o modelo de
produtividade. Pré-colheita usa produtividade esperada do modelo; pós-colheita, a
real do CropCycle. Preço da saca é input do produtor (ADR-0011).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.cost import (
    CostBreakdown,
    ScenarioResult,
    calculate_break_even_yield,
    cost_breakdown,
    scenario_analysis,
)
from app.domain.yield_estimation import RegionalYieldModel
from app.infra.repositories import EventRepository, FarmRepository


class CycleNotFound(Exception):
    pass


class AreaUnknown(Exception):
    pass


@dataclass
class CostService:
    farms: FarmRepository
    events: EventRepository
    model: RegionalYieldModel

    def _cycle_or_raise(self, cycle_id: int):
        cycle = self.farms.get_cycle(cycle_id)
        if cycle is None:
            raise CycleNotFound(cycle_id)
        return cycle

    def _area(self, cycle) -> float:
        area = cycle.area_ha
        if area is None:
            field = self.farms.field_of_cycle(cycle.id)
            area = field.area_ha if field else None
        if not area or area <= 0:
            raise AreaUnknown(cycle.id)
        return area

    def _municipality_code(self, cycle) -> int | None:
        field = self.farms.field_of_cycle(cycle.id)
        if field is None:
            return None
        farm = self.farms.get_farm(field.farm_id)
        return farm.municipality_code if farm else None

    def _model_scenarios(self, cycle) -> dict[str, float] | None:
        code = self._municipality_code(cycle)
        if code is None:
            return None
        try:
            est = self.model.estimate(code, cycle.season.harvest_year)
        except KeyError:
            return None
        return {s.name: s.yield_sc_ha for s in est.scenarios}

    def _expected_yield(self, cycle) -> float | None:
        if cycle.actual_yield_sc_ha:
            return cycle.actual_yield_sc_ha
        scenarios = self._model_scenarios(cycle)
        return scenarios.get("normal") if scenarios else None

    def breakdown(self, cycle_id: int) -> CostBreakdown:
        cycle = self._cycle_or_raise(cycle_id)
        events = self.events.list_by_cycle(cycle_id)
        return cost_breakdown(events, self._area(cycle), self._expected_yield(cycle))

    def financials(self, cycle_id: int, price_per_bag: float) -> dict:
        cycle = self._cycle_or_raise(cycle_id)
        events = self.events.list_by_cycle(cycle_id)
        area = self._area(cycle)
        breakdown = cost_breakdown(events, area, self._expected_yield(cycle))
        break_even = calculate_break_even_yield(breakdown.cost_per_hectare, price_per_bag)

        if cycle.actual_yield_sc_ha:
            yields = {"real": cycle.actual_yield_sc_ha}
            yield_source = "produtividade real informada"
        else:
            yields = self._model_scenarios(cycle) or {}
            yield_source = "cenários do modelo regional (produtividade esperada)"

        scenarios: list[ScenarioResult] = (
            scenario_analysis(breakdown.total_cost, area, price_per_bag, yields)
            if yields else []
        )
        return {
            "breakdown": breakdown,
            "price_per_bag": price_per_bag,
            "break_even_yield_sc_ha": break_even,
            "yield_source": yield_source,
            "scenarios": scenarios,
        }
