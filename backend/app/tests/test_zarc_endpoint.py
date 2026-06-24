"""Endpoint ZARC — usa o artefato real versionado em data/zarc/soja_rs.json."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

_ZARC_ARTIFACT = settings.data_dir / "zarc" / "soja_rs.json"
pytestmark = pytest.mark.skipif(
    not settings.model_path.exists() or not _ZARC_ARTIFACT.exists(),
    reason="modelo ou artefato ZARC ausente",
)


def test_zarc_window_endpoint():
    r = TestClient(app).get("/api/v1/zarc/planting-window?municipality=Horizontina")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "ZARC/MAPA"
    assert body["municipality_name"] == "Horizontina"
    assert "20" in body["windows_by_risk"] and len(body["windows_by_risk"]["20"]) >= 1


def test_zarc_window_with_date_inside():
    r = TestClient(app).get(
        "/api/v1/zarc/planting-window?municipality=Horizontina&planting_date=2026-11-01"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["within_zarc"] is True
    assert body["risk_level"] in (20, 30, 40)


def test_zarc_window_unknown_municipality():
    r = TestClient(app).get("/api/v1/zarc/planting-window?municipality=Inexistente")
    assert r.status_code == 404
