"""Testes do ajuste de custo pelo perfil (rentabilidade personalizada)."""

from __future__ import annotations

from app.domain.agronomy import compute_cost_adjustment


def test_irrigation_raises_cost():
    adj = compute_cost_adjustment({"irrigacao": "irrigado"})
    assert adj.multiplier > 1.0
    assert adj.applied[-1].effect_pct > 0


def test_cutting_fungicide_lowers_cost():
    adj = compute_cost_adjustment({"fungicida": "nenhum"})
    assert adj.multiplier < 1.0
    assert adj.applied[0].effect_pct == -8.0


def test_typical_profile_is_neutral():
    adj = compute_cost_adjustment({"fungicida": "completo", "irrigacao": "sequeiro"})
    assert adj.multiplier == 1.0 and adj.applied == []


def test_ignores_non_cost_factors_and_bad_options():
    # 'textura_solo' não tem efeito de custo; opção inválida é ignorada (sem erro).
    adj = compute_cost_adjustment({"textura_solo": "argiloso", "fungicida": "xyz"})
    assert adj.multiplier == 1.0


def test_cost_multiplier_is_clamped():
    extreme = {
        "irrigacao": "irrigado", "cultivar": "moderna", "acidez_corrigida": "recente",
        "plantio_direto": "convencional",
    }
    adj = compute_cost_adjustment(extreme)
    assert 0.80 <= adj.multiplier <= 1.25
