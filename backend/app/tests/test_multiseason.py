"""Projeção plurianual (ADR-0031)."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.finance import next_seasons, project_economics
from app.main import app

pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")

client = TestClient(app)


def test_next_seasons_labels():
    assert next_seasons("2026/27", 3) == ["2026/27", "2027/28", "2028/29"]


def test_project_economics_basic():
    scn = {"pessimista": 40.0, "normal": 60.0, "otimista": 72.0}
    p = project_economics(scn, base_price_per_bag=120, base_cost_per_ha=4800, season="2026/27", year_index=0)
    normal = next(s for s in p.scenarios if s.name == "normal")
    assert normal.revenue_per_ha == 7200.0       # 60 * 120
    assert normal.profit_per_ha == 2400.0         # 7200 - 4800
    assert p.expected_profit_per_ha == 2400.0


def test_price_trend_changes_future_seasons():
    scn = {"normal": 60.0}
    base = project_economics(scn, 100, 5000, "2026/27", 0, price_trend_pct=10)
    yr2 = project_economics(scn, 100, 5000, "2027/28", 1, price_trend_pct=10)
    assert yr2.price_per_bag > base.price_per_bag   # +10% no ano seguinte


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        project_economics({"normal": 60.0}, -1, 5000, "2026/27", 0)


def test_multi_season_endpoint():
    farm = client.post("/api/v1/farms", json={"name": "F", "municipality_code": 4309605}).json()
    fid = client.post(
        f"/api/v1/farms/{farm['id']}/fields", json={"name": "T1", "area_ha": 100}
    ).json()["id"]
    r = client.get(
        f"/api/v1/fields/{fid}/multi-season?n=3&price_per_bag=120&cost_per_ha=4800"
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["seasons"]) == 3
    assert body["productivity"]["point_sc_ha"] > 0
    assert body["seasons"][0]["scenarios"]          # cenários econômicos presentes
    assert "safra típica" in body["productivity"]["note"]
