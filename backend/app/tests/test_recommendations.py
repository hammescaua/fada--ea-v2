"""Testes do motor de recomendações acionáveis."""

from __future__ import annotations

from app.domain.agronomy import recommendations
from app.domain.agronomy.recommendations import MANAGEABLE_FACTORS


def test_recommends_fixing_fungicide_first():
    profile = {"fungicida": "nenhum", "inoculacao": "nao"}
    recs = recommendations(profile, personalized_point_sc_ha=50.0)
    assert recs[0].key == "fungicida"             # maior ganho primeiro
    assert recs[0].target_label == "Completo"
    assert recs[0].gain_sc_ha > 0
    keys = {r.key for r in recs}
    assert "inoculacao" in keys


def test_no_recommendation_when_optimal():
    recs = recommendations({"fungicida": "completo", "inoculacao": "sim"}, 50.0)
    assert recs == []


def test_structural_factors_excluded():
    # Solo arenoso é estrutural — não vira recomendação acionável.
    recs = recommendations({"textura_solo": "arenoso"}, 50.0)
    assert recs == []
    assert "textura_solo" not in MANAGEABLE_FACTORS


def test_gain_is_marginal_and_positive():
    recs = recommendations({"manejo_pragas": "deficiente"}, 40.0)
    assert len(recs) == 1
    r = recs[0]
    # deficiente (-15%) -> adequado (0): ganho ~ 1/0.85 - 1 ≈ +17.6%
    assert 15 < r.gain_pct < 20
    assert r.gain_sc_ha > 0
