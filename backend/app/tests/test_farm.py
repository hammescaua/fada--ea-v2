"""Testa o flywheel de ground truth com banco isolado (SQLite temporário)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.farm import Season, YieldObservation
from app.infra import models  # noqa: F401 — registra as tabelas
from app.infra.db import Base, get_session
from app.main import app


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_full_capture_flow(client):
    farm = client.post("/api/v1/farms",
                       json={"name": "Faz. Teste", "municipality_code": 4309605}).json()
    field = client.post(f"/api/v1/farms/{farm['id']}/fields",
                        json={"name": "T1", "area_ha": 85}).json()
    cycle = client.post(f"/api/v1/fields/{field['id']}/crop-cycles",
                       json={"crop": "soja", "season": "2026/27"}).json()
    assert cycle["harvest_year"] == 2027
    obs = client.post("/api/v1/yield-observations", json={
        "crop_cycle_id": cycle["id"], "actual_yield_sc_ha": 58, "area_ha": 85,
        "cultivar": "BMX Ícone",
    })
    assert obs.status_code == 201
    assert len(client.get("/api/v1/yield-observations").json()) == 1


def test_field_on_missing_farm_404(client):
    r = client.post("/api/v1/farms/999/fields", json={"name": "T", "area_ha": 10})
    assert r.status_code == 404


def test_observation_invariants():
    # colheita anterior ao plantio
    with pytest.raises(ValueError):
        YieldObservation(crop_cycle_id=1, actual_yield_sc_ha=10, area_ha=1,
                         actual_planting_date=__import__("datetime").date(2027, 1, 1),
                         actual_harvest_date=__import__("datetime").date(2026, 12, 1))
    # rendimento negativo
    with pytest.raises(ValueError):
        YieldObservation(crop_cycle_id=1, actual_yield_sc_ha=-1, area_ha=1)


def test_season_value_object():
    assert Season.parse("2026/27").harvest_year == 2027
    assert Season.parse("2027").harvest_year == 2027
