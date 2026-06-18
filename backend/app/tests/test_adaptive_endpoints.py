"""Testes de endpoint do Adaptive Intelligence (DB isolado, modelo real)."""

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


def _seed_farm(client, yields_by_year: dict[int, float]) -> int:
    farm = client.post("/api/v1/farms",
                       json={"name": "F", "municipality_code": 4309605}).json()
    field = client.post(f"/api/v1/farms/{farm['id']}/fields",
                       json={"name": "T1", "area_ha": 100}).json()
    for year, y in yields_by_year.items():
        client.post(f"/api/v1/fields/{field['id']}/crop-cycles", json={
            "crop": "soja", "season": f"{year - 1}/{str(year)[2:]}",
            "area_ha": 100, "actual_yield_sc_ha": y,
        })
    return farm["id"]


def test_recompute_profile_and_history(client):
    farm_id = _seed_farm(client, {y: 55.0 for y in range(2018, 2024)})
    prof = client.post(f"/api/v1/farms/{farm_id}/performance-profile/recompute").json()
    assert prof["number_of_cycles"] == 6
    assert len(prof["residual_history"]) == 6
    assert "bias_percentage" in prof


def test_personalized_interval_not_narrower(client):
    farm_id = _seed_farm(client, {y: 58.0 for y in range(2015, 2025)})
    client.post(f"/api/v1/farms/{farm_id}/performance-profile/recompute")
    pi = client.post("/api/v1/personalized-intelligence",
                    json={"farm_id": farm_id, "season": "2026/27"}).json()
    reg = pi["regional_prediction"]["interval_sc_ha"]
    per = pi["personalized_prediction"]["interval_sc_ha"]
    assert (per[1] - per[0]) >= (reg[1] - reg[0]) - 1e-6
    assert 0.0 <= pi["confidence_score"] <= 1.0
    assert pi["adaptation_level"] in {"nenhuma", "baixa", "moderada", "alta"}


def test_personalized_without_profile_is_regional(client):
    farm = client.post("/api/v1/farms",
                      json={"name": "Nova", "municipality_code": 4309605}).json()
    pi = client.post("/api/v1/personalized-intelligence",
                    json={"farm_id": farm["id"], "season": "2026/27"}).json()
    assert pi["confidence_score"] == 0.0
    assert pi["farm_adjustment"]["n_cycles"] == 0
    assert pi["personalized_prediction"]["point_sc_ha"] == \
        pi["regional_prediction"]["point_sc_ha"]


def test_profile_404_before_recompute(client):
    farm = client.post("/api/v1/farms",
                      json={"name": "X", "municipality_code": 4309605}).json()
    assert client.get(f"/api/v1/farms/{farm['id']}/performance-profile").status_code == 404


def test_assistant_adaptive_question(client):
    farm_id = _seed_farm(client, {y: 58.0 for y in range(2016, 2024)})
    client.post(f"/api/v1/farms/{farm_id}/performance-profile/recompute")
    r = client.post("/api/v1/assistant", json={
        "message": "Minha fazenda costuma produzir acima da média?", "farm_id": farm_id,
    }).json()
    assert r["intent"] == "above_average"
    assert "média regional" in r["answer"]
