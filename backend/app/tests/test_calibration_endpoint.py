"""Teste do endpoint /calibration (pula se o artefato não foi gerado)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.calibration import REPORT_PATH

pytestmark = pytest.mark.skipif(
    not REPORT_PATH.exists(), reason="relatório de calibração ausente"
)

client = TestClient(app)


def test_calibration_endpoint():
    r = client.get("/api/v1/calibration")
    assert r.status_code == 200
    body = r.json()
    for key in ("regional", "personalized"):
        rep = body[key]
        assert 0.0 <= rep["coverage_80"] <= 1.0
        assert rep["mean_width"] > 0
        assert len(rep["reliability_curve"]) >= 4
        assert "interpretation" in rep


def test_personalized_does_not_narrow():
    body = client.get("/api/v1/calibration").json()
    # a largura média do personalizado não é menor que a do regional (incerteza honesta)
    assert body["personalized"]["mean_width"] >= body["regional"]["mean_width"] - 1e-6


def test_personalized_not_worse_accuracy():
    body = client.get("/api/v1/calibration").json()
    assert body["personalized"]["mae"] <= body["regional"]["mae"] + 1e-6
