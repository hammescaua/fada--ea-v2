"""Testes do caso de uso e do endpoint usando o artefato real treinado.

Pulam se o modelo ainda não foi treinado (data/models/...json ausente).
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.yield_estimation import RegionalYieldModel
from app.engine.explainer import TemplateExplainer
from app.main import app
from app.services.regional_intelligence import (
    CropNotSupported,
    InvalidSeason,
    MunicipalityNotInRegion,
    RegionalIntelligenceService,
    parse_harvest_year,
)

pytestmark = pytest.mark.skipif(
    not settings.model_path.exists(), reason="modelo não treinado"
)


@pytest.fixture
def service() -> RegionalIntelligenceService:
    model = RegionalYieldModel.load(settings.model_path)
    return RegionalIntelligenceService(model=model, explainer=TemplateExplainer())


def test_parse_harvest_year():
    assert parse_harvest_year("2026/27") == 2027
    assert parse_harvest_year("2027") == 2027
    with pytest.raises(InvalidSeason):
        parse_harvest_year("safra-x")


def test_horizontina_runs(service):
    out = service.run(municipality="Horizontina", crop="soja", season="2026/27")
    assert out["municipality_code"] == 4309605
    assert out["harvest_year"] == 2027
    assert out["estimated_yield_sc_ha"] > 0
    by = {s["name"]: s["yield_sc_ha"] for s in out["scenarios"]}
    assert by["pessimista"] < by["normal"] < by["otimista"]
    assert out["climatic_risks"][0]["factor"] == "deficit_hidrico_reprodutivo"
    assert "Horizontina" in out["explanation"]


def test_accent_insensitive_resolution(service):
    # "Doutor Mauricio Cardoso" sem acento deve resolver
    out = service.run(municipality="doutor mauricio cardoso", crop="soja", season="2026/27")
    assert out["municipality_code"] == 4306734


def test_unknown_municipality(service):
    with pytest.raises(MunicipalityNotInRegion):
        service.run(municipality="São Paulo", crop="soja", season="2026/27")


def test_unsupported_crop(service):
    with pytest.raises(CropNotSupported):
        service.run(municipality="Horizontina", crop="milho", season="2026/27")


def test_endpoint_200():
    client = TestClient(app)
    r = client.post(
        "/api/v1/regional-intelligence",
        json={"municipality": "Horizontina", "uf": "RS", "crop": "soja", "season": "2026/27"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["municipality_code"] == 4309605
    assert len(body["scenarios"]) == 3
    assert body["confidence_interval_sc_ha"][0] < body["confidence_interval_sc_ha"][1]
    # Transparência (Fase 3.2): raciocínio estruturado exposto
    assert body["n_years"] > 0
    assert body["reasoning"]["n_years"] == body["n_years"]
    assert "interval_basis" in body["reasoning"]


def test_endpoint_422_unknown_municipality():
    client = TestClient(app)
    r = client.post(
        "/api/v1/regional-intelligence",
        json={"municipality": "Curitiba", "crop": "soja", "season": "2026/27"},
    )
    assert r.status_code == 422
