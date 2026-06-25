"""Testes da personalização sensível ao cenário climático (ADR-0023)."""

from __future__ import annotations

from app.domain.agronomy import (
    apply_adjustment,
    compute_adjustment,
    scenario_multipliers,
    water_sensitivity_note,
)


def test_normal_scenario_equals_flat_multiplier():
    profile = {"textura_solo": "arenoso", "fungicida": "nenhum"}
    flat = compute_adjustment(profile).multiplier
    assert scenario_multipliers(profile)["normal"] == flat


def test_sandy_soil_worse_in_dry_year():
    m = scenario_multipliers({"textura_solo": "arenoso"})
    # arenoso (-7%) amplificado no seco, atenuado no úmido
    assert m["pessimista"] < m["normal"] < m["otimista"]


def test_poor_drainage_worse_in_wet_year():
    m = scenario_multipliers({"drenagem": "ma"})
    assert m["otimista"] < m["normal"] < m["pessimista"]


def test_non_water_factor_is_scenario_neutral():
    m = scenario_multipliers({"fungicida": "nenhum"})
    assert m["pessimista"] == m["normal"] == m["otimista"]


def test_apply_adjustment_diverges_scenarios():
    profile = {"textura_solo": "arenoso"}
    adj = compute_adjustment(profile)
    scen = {"pessimista": 40.0, "normal": 50.0, "otimista": 60.0}
    flat = apply_adjustment(50.0, (40.0, 60.0), scen, adj)
    aware = apply_adjustment(50.0, (40.0, 60.0), scen, adj,
                             scenario_multipliers=scenario_multipliers(profile))
    # ponto igual; pessimista do sensível é mais baixo que o flat
    assert aware.personalized_point_sc_ha == flat.personalized_point_sc_ha
    assert aware.scenarios_sc_ha["pessimista"] < flat.scenarios_sc_ha["pessimista"]


def test_water_sensitivity_note():
    assert water_sensitivity_note({"textura_solo": "arenoso", "profundidade_solo": "raso"})
    assert water_sensitivity_note({"drenagem": "ma"})
    assert water_sensitivity_note({"fungicida": "nenhum"}) is None
