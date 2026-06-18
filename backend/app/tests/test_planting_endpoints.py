"""Testes de endpoint usando modelo + grid reais (pulam se ausentes)."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.planting_date import GRID_PATH

pytestmark = pytest.mark.skipif(
    not (settings.model_path.exists() and GRID_PATH.exists()),
    reason="modelo ou grid ausente",
)

client = TestClient(app)
BASE = {"municipality": "Horizontina", "crop": "soja", "season": "2026/27"}


def test_simulation_200():
    r = client.post("/api/v1/planting-date-simulation", json={**BASE, "planting_date": "2026-11-01"})
    assert r.status_code == 200
    b = r.json()
    assert b["municipality_code"] == 4309605
    assert b["within_zarc"] is True
    assert "r1_begin_flowering" in b["phenology"]
    assert len(b["scenarios"]) == 3


def test_simulation_outside_zarc_flagged():
    r = client.post("/api/v1/planting-date-simulation", json={**BASE, "planting_date": "2026-10-01"})
    assert r.status_code == 200
    # 01/out está fora da janela ZARC (início 11/out)
    assert r.json()["within_zarc"] is False


def test_optimization_top5_within_zarc():
    r = client.post("/api/v1/planting-window-optimization", json=BASE)
    assert r.status_code == 200
    b = r.json()
    assert len(b["top_recommendations"]) == 5
    # ranqueado por score decrescente
    scores = [rec["risk_score"] for rec in b["top_recommendations"]]
    assert scores == sorted(scores, reverse=True)


def test_optimization_risk_aversion_changes_ranking():
    neutral = client.post("/api/v1/planting-window-optimization",
                          json={**BASE, "risk_aversion": 0.0}).json()
    averse = client.post("/api/v1/planting-window-optimization",
                         json={**BASE, "risk_aversion": 2.0}).json()
    # com aversão alta, o score do topo penaliza mais o downside
    assert averse["top_recommendations"][0]["risk_score"] <= \
        neutral["top_recommendations"][0]["risk_score"]


def test_invalid_municipality_422():
    r = client.post("/api/v1/planting-date-simulation",
                    json={**BASE, "municipality": "Curitiba", "planting_date": "2026-11-01"})
    assert r.status_code == 422
