"""Testes do Perfil Agronômico: matriz, motor de ajuste e endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.agronomy import (
    FACTORS,
    UnknownFactor,
    apply_adjustment,
    compute_adjustment,
    planting_window_class,
    profile_completeness,
)
from app.main import app

pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")

_ZARC = settings.data_dir / "zarc" / "soja_rs.json"


def test_planting_window_class_mapping():
    assert planting_window_class(True, 20) == "otima"
    assert planting_window_class(True, 30) == "aceitavel"
    assert planting_window_class(True, 40) == "aceitavel"
    assert planting_window_class(False, None) == "fora"


@pytest.mark.skipif(not _ZARC.exists(), reason="artefato ZARC ausente")
def test_planting_window_class_endpoint():
    c = TestClient(app)
    inside = c.get(
        "/api/v1/agronomic/planting-window-class"
        "?municipality=Horizontina&planting_date=2026-11-15"
    ).json()
    assert inside["profile_fragment"]["janela_plantio"] in ("otima", "aceitavel")
    assert inside["within_zarc"] is True
    outside = c.get(
        "/api/v1/agronomic/planting-window-class"
        "?municipality=Horizontina&planting_date=2026-04-01"
    ).json()
    assert outside["profile_fragment"]["janela_plantio"] == "fora"


# -- matriz / motor (puro) --------------------------------------------------

def test_profile_completeness_empty():
    c = profile_completeness({})
    assert c["filled_count"] == 0
    assert c["pct"] == 0
    assert c["essential_total"] == len(c["missing"])


def test_profile_completeness_counts_only_essentials():
    # 2 essenciais + 1 não-essencial preenchidos → conta só os essenciais
    c = profile_completeness(
        {"cultivar": "alta", "fungicida": "duas", "compactacao": "ausente"}
    )
    assert c["filled_count"] == 2
    assert "cultivar" in c["filled"] and "fungicida" in c["filled"]
    assert "compactacao" not in c["filled"]
    assert c["pct"] == round(100 * 2 / c["essential_total"])


def test_profile_completeness_ignores_blank_values():
    c = profile_completeness({"cultivar": "", "fungicida": "duas"})
    assert c["filled"] == ["fungicida"]


def test_empty_profile_is_neutral():
    adj = compute_adjustment({})
    assert adj.multiplier == 1.0 and adj.n_factors == 0


def test_typical_levels_are_neutral():
    # Níveis "típicos/adequados" têm efeito 0 (referência = fazenda média).
    adj = compute_adjustment({"fungicida": "completo", "inoculacao": "sim"})
    assert adj.multiplier == 1.0 and adj.applied == []


def test_good_profile_raises_estimate():
    adj = compute_adjustment({"textura_solo": "argiloso", "cultivar": "moderna"})
    assert adj.multiplier > 1.0
    assert adj.applied[0].effect_pct != 0


def test_bad_profile_lowers_and_clamps():
    bad = {
        "fungicida": "nenhum", "nematoides": "alta", "janela_plantio": "fora",
        "acidez_corrigida": "nao", "inoculacao": "nao", "fertilidade_p": "baixo",
        "textura_solo": "arenoso", "manejo_pragas": "deficiente",
    }
    adj = compute_adjustment(bad)
    assert adj.multiplier == 0.50  # limitado (clamp)
    assert adj.clamped is True
    # Maior limitante primeiro (ordenado por efeito).
    assert adj.applied[0].effect_pct <= adj.applied[-1].effect_pct


def test_unknown_factor_or_option_rejected():
    with pytest.raises(UnknownFactor):
        compute_adjustment({"fator_inexistente": "x"})
    with pytest.raises(UnknownFactor):
        compute_adjustment({"fungicida": "opcao_invalida"})


def test_apply_widens_interval():
    adj = compute_adjustment({"cultivar": "moderna"})
    est = apply_adjustment(50.0, (40.0, 60.0), {"normal": 50.0}, adj)
    reg_width = 60.0 - 40.0
    pers_width = est.personalized_interval_sc_ha[1] - est.personalized_interval_sc_ha[0]
    assert est.personalized_point_sc_ha > 50.0   # ajuste positivo deslocou
    assert pers_width >= reg_width               # incerteza nunca estreita


def test_matrix_effects_are_fractions():
    for f in FACTORS.values():
        for opt in f.options.values():
            assert -1.0 < opt.effect < 1.0


# -- endpoint ---------------------------------------------------------------

def test_factors_catalog_endpoint():
    r = TestClient(app).get("/api/v1/agronomic/factors")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 15
    assert all("options" in f and f["options"] for f in body)


def test_neighboring_farms_diverge():
    c = TestClient(app)
    base = {"municipality": "Horizontina", "crop": "soja", "season": "2026/27"}
    good = c.post("/api/v1/agronomic/estimate", json={**base, "profile": {
        "textura_solo": "argiloso", "cultivar": "moderna", "fertilidade_p": "alto",
    }}).json()
    bad = c.post("/api/v1/agronomic/estimate", json={**base, "profile": {
        "textura_solo": "arenoso", "cultivar": "antiga", "fungicida": "nenhum",
    }}).json()
    assert good["regional"]["point_sc_ha"] == bad["regional"]["point_sc_ha"]
    assert good["personalized"]["point_sc_ha"] > bad["personalized"]["point_sc_ha"]
    assert bad["adjustment"]["factors"]  # fatores limitantes explicados


def test_estimate_rejects_bad_profile():
    r = TestClient(app).post("/api/v1/agronomic/estimate", json={
        "municipality": "Horizontina", "profile": {"fungicida": "xyz"},
    })
    assert r.status_code == 422
