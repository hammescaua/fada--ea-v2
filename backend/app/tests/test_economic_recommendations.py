"""Testes das recomendações econômicas (ganho líquido R$/ha)."""

from __future__ import annotations

from app.domain.agronomy import economic_recommendations


def test_net_gain_subtracts_cost():
    # Fungicida nenhum->completo: ganho de produtividade alto, mas adiciona custo.
    recs = economic_recommendations(
        {"fungicida": "nenhum"}, personalized_point_sc_ha=50.0,
        price_per_bag=130.0, reference_cost_per_ha=5800.0,
    )
    assert len(recs) == 1
    r = recs[0]
    assert r.yield_gain_rs_ha > 0
    assert r.cost_change_rs_ha > 0          # adotar fungicida custa mais
    assert abs(r.net_gain_rs_ha - (r.yield_gain_rs_ha - r.cost_change_rs_ha)) < 0.02
    assert r.net_gain_rs_ha < r.yield_gain_rs_ha


def test_sorted_by_net_gain():
    recs = economic_recommendations(
        {"fungicida": "nenhum", "tratamento_semente": "nao", "inoculacao": "nao"},
        50.0, 130.0, 5800.0,
    )
    nets = [r.net_gain_rs_ha for r in recs]
    assert nets == sorted(nets, reverse=True)


def test_no_recs_when_optimal():
    recs = economic_recommendations({"fungicida": "completo"}, 50.0, 130.0, 5800.0)
    assert recs == []


def test_factor_without_cost_effect_has_zero_cost_change():
    # 'populacao' não está na matriz de custo -> só ganho de produtividade.
    recs = economic_recommendations({"populacao": "baixa"}, 50.0, 130.0, 5800.0)
    assert recs and recs[0].cost_change_rs_ha == 0.0
    assert recs[0].net_gain_rs_ha == recs[0].yield_gain_rs_ha
