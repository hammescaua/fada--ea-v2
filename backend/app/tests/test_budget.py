"""Testes do orçamento (plano x realizado), agenda e presets (puros)."""

from datetime import date

from app.domain.farm import AgriculturalEvent, EventPreset, EventType
from app.domain.planning import PlannedEvent, build_agenda, compute_plan_vs_actual


def _planned(et, d, cost):
    return PlannedEvent(crop_cycle_id=1, event_type=EventType(et), planned_date=d,
                        expected_cost=cost)


def _actual(et, d, cost):
    return AgriculturalEvent(crop_cycle_id=1, event_type=EventType(et), event_date=d, cost=cost)


def test_preset_cost_per_hectare():
    p = EventPreset(name="Fung", event_type=EventType.FUNGICIDE, default_cost=220,
                    cost_is_per_hectare=True)
    assert p.cost_for_area(100) == 22000.0
    flat = EventPreset(name="X", event_type=EventType.OTHER, default_cost=5000)
    assert flat.cost_for_area(100) == 5000.0  # custo total fixo
    assert EventPreset(name="Y", event_type=EventType.OTHER).cost_for_area(100) is None


def test_plan_vs_actual_within_budget():
    planned = [_planned("BASE_FERTILIZATION", date(2026, 11, 1), 120000),
               _planned("FUNGICIDE", date(2027, 1, 10), 40000)]
    actual = [_actual("BASE_FERTILIZATION", date(2026, 11, 1), 130000)]
    pva = compute_plan_vs_actual(planned, actual, 100.0, 58.0, 125.0)
    assert pva.planned_total_cost == 160000.0
    assert pva.actual_total_cost == 130000.0
    assert pva.remaining_budget == 30000.0
    assert pva.over_budget is False
    assert pva.planned_applications == 2 and pva.actual_applications == 1
    # receita esperada = 58*100*125 = 725000; lucro = 725000-160000
    assert pva.expected_revenue == 725000.0
    assert pva.expected_profit == 565000.0


def test_plan_vs_actual_over_budget():
    planned = [_planned("HERBICIDE", date(2026, 11, 1), 10000)]
    actual = [_actual("HERBICIDE", date(2026, 11, 2), 15000)]
    pva = compute_plan_vs_actual(planned, actual, 50.0, None, None)
    assert pva.over_budget is True
    assert pva.cost_variance == 5000.0
    assert pva.remaining_budget == -5000.0
    assert pva.expected_profit is None  # sem alvo/preço


def test_plan_vs_actual_no_plan():
    pva = compute_plan_vs_actual([], [_actual("HERBICIDE", date(2026, 11, 1), 9000)], 50.0,
                                 None, None)
    assert pva.planned_total_cost == 0.0
    assert pva.pct_budget_spent is None


def test_agenda_status_by_count_and_date():
    planned = [
        _planned("BASE_FERTILIZATION", date(2026, 11, 1), 100),
        _planned("FUNGICIDE", date(2027, 1, 10), 200),
        _planned("FUNGICIDE", date(2027, 2, 10), 200),
    ]
    actual = [_actual("BASE_FERTILIZATION", date(2026, 11, 1), 100),
              _actual("FUNGICIDE", date(2027, 1, 12), 200)]
    items = build_agenda(planned, actual, today=date(2027, 1, 20))
    status = {(i.event_type, i.planned_date): i.status for i in items}
    assert status[("BASE_FERTILIZATION", "2026-11-01")] == "concluída"
    assert status[("FUNGICIDE", "2027-01-10")] == "concluída"   # 1ª fungicida feita
    assert status[("FUNGICIDE", "2027-02-10")] == "próxima"     # 2ª ainda não, data futura


def test_agenda_overdue():
    planned = [_planned("HERBICIDE", date(2026, 11, 1), 100)]
    items = build_agenda(planned, [], today=date(2027, 1, 1))
    assert items[0].status == "atrasada"  # planejada, data passada, não executada
