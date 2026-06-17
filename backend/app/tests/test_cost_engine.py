"""Testa o Cost Engine (funções puras, determinísticas)."""

from datetime import date

import pytest

from app.domain.farm import AgriculturalEvent, EventType
from app.domain.cost import (
    calculate_break_even_yield,
    calculate_cost_per_bag,
    calculate_cost_per_hectare,
    calculate_total_cost,
    cost_breakdown,
    count_applications,
    scenario_analysis,
)


def _ev(t: EventType, cost: float | None) -> AgriculturalEvent:
    return AgriculturalEvent(crop_cycle_id=1, event_type=t, event_date=date(2026, 11, 1),
                             cost=cost)


EVENTS = [
    _ev(EventType.PLANTING, 85000),
    _ev(EventType.BASE_FERTILIZATION, 120000),
    _ev(EventType.HERBICIDE, 18000),
    _ev(EventType.FUNGICIDE, 22000),
    _ev(EventType.INSECTICIDE, 15000),
    _ev(EventType.IRRIGATION, None),  # sem custo conta como 0
]


def test_total_cost_ignores_none():
    assert calculate_total_cost(EVENTS) == 260000.0


def test_count_applications_excludes_planting_and_irrigation():
    # aplicações = adubação de base + herbicida + fungicida + inseticida = 4
    assert count_applications(EVENTS) == 4


def test_cost_per_hectare_and_bag():
    assert calculate_cost_per_hectare(260000, 100) == 2600.0
    # 100 ha x 52 sc/ha = 5200 sc -> 260000/5200 = 50.0
    assert calculate_cost_per_bag(260000, 52, 100) == 50.0


def test_break_even_yield():
    # custo/ha 2600 a R$130/sc -> 20 sc/ha
    assert calculate_break_even_yield(2600, 130) == 20.0


def test_scenario_analysis_profit_and_margin():
    res = scenario_analysis(260000, 100, 125, {"pessimista": 36.8, "normal": 51.2})
    by = {r.name: r for r in res}
    # normal: receita 51.2*100*125 = 640000; lucro 380000
    assert by["normal"].revenue == 640000.0
    assert by["normal"].profit == 380000.0
    assert by["pessimista"].profit < by["normal"].profit


def test_cost_breakdown_without_yield_has_no_cost_per_bag():
    b = cost_breakdown(EVENTS, area_ha=100, yield_sc_ha=None)
    assert b.cost_per_bag is None
    assert b.n_applications == 4
    assert b.cost_by_category["BASE_FERTILIZATION"] == 120000.0


def test_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_cost_per_hectare(100, 0)
    with pytest.raises(ValueError):
        calculate_break_even_yield(2600, 0)


def test_event_invariants():
    with pytest.raises(ValueError):
        AgriculturalEvent(crop_cycle_id=1, event_type=EventType.HERBICIDE,
                          event_date=date(2026, 11, 1), cost=-5)
