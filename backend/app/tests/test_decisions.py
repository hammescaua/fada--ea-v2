"""Testes do domínio de decisão (flags gated, atenção, ranking) — sem score único."""

from app.domain.decisions import FieldDecisionInput, attention_level, evaluate, rankings
from app.domain.decisions.engine import _field_flags


def _f(**kw):
    base = dict(field_id=1, field_name="A", area_ha=100.0)
    base.update(kw)
    return FieldDecisionInput(**base)


def test_cost_per_ha_flag_relative_to_median():
    f = _f(actual_cost_per_ha=2000.0)
    flags = _field_flags(f, farm_cost_median=1500.0)  # ratio 1.33 -> média
    assert any(fl.code == "custo_ha_alto" and fl.severity == "média" for fl in flags)
    flags_high = _field_flags(_f(actual_cost_per_ha=2500.0), 1500.0)  # 1.67 -> alta
    assert any(fl.code == "custo_ha_alto" and fl.severity == "alta" for fl in flags_high)


def test_below_target_flag():
    flags = _field_flags(_f(target_yield_sc_ha=75.0, expected_yield_sc_ha=51.0), None)
    fl = next(fl for fl in flags if fl.code == "abaixo_da_meta")
    assert fl.severity == "alta"  # 32% abaixo
    assert fl.confidence == "moderada"
    assert fl.evidence["gap_pct"] == 32.0


def test_over_budget_flag():
    flags = _field_flags(_f(actual_total_cost=160000, planned_total_cost=130000), None)
    fl = next(fl for fl in flags if fl.code == "orcamento_estourado")
    assert fl.severity == "alta"  # 1.23 >= 1.15


def test_below_region_gated_by_n():
    assert not any(fl.code == "abaixo_da_regiao"
                   for fl in _field_flags(_f(bias_vs_region_pct=-25, n_seasons=1), None))
    flags = _field_flags(_f(bias_vs_region_pct=-25, n_seasons=3), None)
    fl = next(fl for fl in flags if fl.code == "abaixo_da_regiao")
    assert fl.severity == "alta" and fl.confidence == "moderada"


def test_unstable_gated_by_n():
    assert not any(fl.code == "instavel"
                   for fl in _field_flags(_f(stability_std_pct=20, n_seasons=2), None))
    assert any(fl.code == "instavel"
               for fl in _field_flags(_f(stability_std_pct=20, n_seasons=4), None))


def test_attention_level():
    from app.domain.decisions.model import AttentionFlag
    alta = [AttentionFlag("x", "alta", "t", "d", "alta")]
    media = [AttentionFlag("x", "média", "t", "d", "alta")]
    assert attention_level(alta) == "alta"
    assert attention_level(media) == "média"
    assert attention_level([]) == "saudável"


def test_evaluate_sorts_and_levels():
    fields = [
        _f(field_id=1, field_name="Norte", actual_total_cost=160000,
           planned_total_cost=130000, target_yield_sc_ha=75, expected_yield_sc_ha=51),
        _f(field_id=2, field_name="Sul", actual_cost_per_ha=750.0),
    ]
    out = evaluate(fields)
    assert out[0].field_name == "Norte" and out[0].attention_level == "alta"
    assert out[1].attention_level == "saudável"


def test_rankings_no_blending():
    fields = [
        _f(field_id=1, field_name="A", actual_cost_per_ha=1600.0,
           target_yield_sc_ha=75, expected_yield_sc_ha=51),
        _f(field_id=2, field_name="B", actual_cost_per_ha=750.0,
           target_yield_sc_ha=52, expected_yield_sc_ha=51),
    ]
    rk = rankings(fields)
    assert rk["custo_por_hectare"][0]["field_name"] == "A"
    assert rk["distancia_da_meta_pct"][0]["field_name"] == "A"
