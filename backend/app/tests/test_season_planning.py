"""Testes da síntese de margem (puro) e do brief de safra (endpoint real)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.planning.season import season_margin
from app.main import app

pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")


# -- domínio puro -----------------------------------------------------------

def test_season_margin_breakeven_and_profit():
    out = season_margin(
        yield_scenarios={"pessimista": 40.0, "normal": 60.0, "otimista": 75.0},
        expected_yield_sc_ha=60.0,
        price_per_bag=130.0,
        costs_per_ha={"coe": 4668.0, "cot": 5830.0, "ct": 6656.0},
    )
    # break-even = custo/ha ÷ preço
    assert out["break_even_yield_sc_ha"]["cot"] == round(5830.0 / 130.0, 1)
    assert out["break_even_yield_sc_ha"]["coe"] < out["break_even_yield_sc_ha"]["ct"]
    # margem esperada sobre COT: 60*130 - 5830
    assert out["expected"]["profit_per_ha"] == round(60.0 * 130.0 - 5830.0, 2)
    names = {s.name for s in out["scenarios"]}
    assert {"pessimista", "normal", "otimista"} <= names


def test_season_margin_scenarios_use_cot():
    out = season_margin(
        {"normal": 50.0}, 50.0, 100.0, {"coe": 4000.0, "cot": 5000.0, "ct": 6000.0}
    )
    s = out["scenarios"][0]
    assert s.revenue == 5000.0 and s.total_cost == 5000.0 and s.profit == 0.0


# -- endpoint (composição real, dados versionados) --------------------------

def test_season_brief_endpoint():
    r = TestClient(app).get(
        "/api/v1/planning/season-brief?municipality=Horizontina&season=2026/27"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["municipality"] == "Horizontina"
    assert body["yield"]["expected_sc_ha"] > 0
    # ZARC e preço/custo estão versionados → margem deve sintetizar
    assert body["planting"]["zarc"] is not None
    assert body["price"] is not None and body["cost"] is not None
    assert body["margin"] is not None
    assert "break_even_yield_sc_ha" in body["margin"]
    assert isinstance(body["verdict"], str) and len(body["verdict"]) > 0


def test_season_brief_unknown_municipality():
    r = TestClient(app).get("/api/v1/planning/season-brief?municipality=Inexistente")
    assert r.status_code == 404
