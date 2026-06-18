"""Testes de endpoint da camada de decisão + projeção (DB isolado, modelo real)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.infra import models  # noqa: F401
from app.infra.db import Base, get_session
from app.main import app

pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    TS = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        s = TS()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _farm_two_fields(client):
    farm = client.post("/api/v1/farms", json={"name": "F", "municipality_code": 4309605}).json()
    fa = client.post(f"/api/v1/farms/{farm['id']}/fields",
                    json={"name": "Norte", "area_ha": 100}).json()
    fb = client.post(f"/api/v1/farms/{farm['id']}/fields",
                    json={"name": "Sul", "area_ha": 80}).json()
    ca = client.post(f"/api/v1/fields/{fa['id']}/crop-cycles", json={
        "crop": "soja", "season": "2026/27", "area_ha": 100, "target_yield_sc_ha": 75}).json()["id"]
    client.post(f"/api/v1/fields/{fb['id']}/crop-cycles", json={
        "crop": "soja", "season": "2026/27", "area_ha": 80, "target_yield_sc_ha": 52})
    # Norte estoura o orçamento; Sul dentro
    client.post(f"/api/v1/crop-cycles/{ca}/planned-events",
               json={"event_type": "BASE_FERTILIZATION", "planned_date": "2026-11-01",
                     "expected_cost": 130000})
    client.post(f"/api/v1/crop-cycles/{ca}/events",
               json={"event_type": "BASE_FERTILIZATION", "event_date": "2026-11-01",
                     "cost": 160000})
    return farm["id"], ca


def test_decisions_attention_and_rankings(client):
    farm_id, _ = _farm_two_fields(client)
    d = client.get(f"/api/v1/farms/{farm_id}/decisions").json()
    assert d["n_fields"] == 2
    norte = next(f for f in d["fields"] if f["field_name"] == "Norte")
    assert norte["attention_level"] == "alta"
    codes = {fl["code"] for fl in norte["flags"]}
    assert "orcamento_estourado" in codes
    # toda flag traz evidência e confiança
    assert all("confidence" in fl and fl["evidence"] for fl in norte["flags"])
    assert d["rankings"]["custo_por_hectare"][0]["field_name"] == "Norte"


def test_no_single_score_field(client):
    farm_id, _ = _farm_two_fields(client)
    d = client.get(f"/api/v1/farms/{farm_id}/decisions").json()
    # honestidade: nenhum "priority_score" — só flags nomeadas
    for f in d["fields"]:
        assert "score" not in f


def test_cost_projection_plan_based(client):
    _, ca = _farm_two_fields(client)
    client.post(f"/api/v1/crop-cycles/{ca}/planned-events",
               json={"event_type": "FUNGICIDE", "planned_date": "2027-01-10",
                     "expected_cost": 25000})
    proj = client.get(f"/api/v1/crop-cycles/{ca}/cost-projection").json()
    # real 160000 + pendente 25000 = 185000 (a base já foi cumprida -> não conta)
    assert proj["actual_total_cost"] == 160000.0
    assert proj["remaining_planned_cost"] == 25000.0
    assert proj["projected_total_cost"] == 185000.0
    assert "plano" in proj["basis"]


def test_cost_projection_without_plan(client):
    farm = client.post("/api/v1/farms", json={"name": "X", "municipality_code": 4309605}).json()
    fld = client.post(f"/api/v1/farms/{farm['id']}/fields",
                     json={"name": "T", "area_ha": 50}).json()
    ca = client.post(f"/api/v1/fields/{fld['id']}/crop-cycles",
                    json={"crop": "soja", "season": "2026/27", "area_ha": 50}).json()["id"]
    proj = client.get(f"/api/v1/crop-cycles/{ca}/cost-projection").json()
    assert proj["projected_total_cost"] is None  # sem plano, sem projeção honesta


def test_assistant_attention_question(client):
    farm_id, _ = _farm_two_fields(client)
    r = client.post("/api/v1/assistant",
                   json={"message": "Qual talhão merece mais atenção?", "farm_id": farm_id}).json()
    assert r["intent"] == "field_attention"
    assert "Norte" in r["answer"]


def test_decisions_404(client):
    assert client.get("/api/v1/farms/999/decisions").status_code == 404
