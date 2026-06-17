"""Testes de endpoint da timeline + Cost Engine (DB isolado, modelo real)."""

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


def _setup_cycle(client) -> int:
    farm = client.post("/api/v1/farms",
                       json={"name": "F", "municipality_code": 4309605}).json()
    field = client.post(f"/api/v1/farms/{farm['id']}/fields",
                       json={"name": "T1", "area_ha": 100}).json()
    return client.post(f"/api/v1/fields/{field['id']}/crop-cycles",
                      json={"crop": "soja", "season": "2026/27", "area_ha": 100}).json()["id"]


def test_timeline_and_cost_breakdown(client):
    cid = _setup_cycle(client)
    for e in [
        {"event_type": "BASE_FERTILIZATION", "event_date": "2026-11-01", "cost": 120000},
        {"event_type": "HERBICIDE", "event_date": "2026-11-20", "cost": 18000},
        {"event_type": "FUNGICIDE", "event_date": "2027-01-10", "cost": 22000},
    ]:
        assert client.post(f"/api/v1/crop-cycles/{cid}/events", json=e).status_code == 201

    assert len(client.get(f"/api/v1/crop-cycles/{cid}/events").json()) == 3
    b = client.get(f"/api/v1/crop-cycles/{cid}/cost").json()
    assert b["total_cost"] == 160000.0
    assert b["cost_per_hectare"] == 1600.0
    assert b["n_applications"] == 3
    assert b["cost_per_bag"] is not None  # usa produtividade esperada do modelo


def test_financials_scenarios(client):
    cid = _setup_cycle(client)
    client.post(f"/api/v1/crop-cycles/{cid}/events",
               json={"event_type": "BASE_FERTILIZATION", "event_date": "2026-11-01",
                     "cost": 200000})
    fin = client.post(f"/api/v1/crop-cycles/{cid}/financials",
                     json={"price_per_bag": 125}).json()
    assert fin["break_even_yield_sc_ha"] == 16.0  # 2000/125
    names = {s["name"] for s in fin["scenarios"]}
    assert {"pessimista", "normal", "otimista"} <= names


def test_cycle_patch_updates_yield(client):
    cid = _setup_cycle(client)
    r = client.patch(f"/api/v1/crop-cycles/{cid}", json={"actual_yield_sc_ha": 58})
    assert r.status_code == 200 and r.json()["actual_yield_sc_ha"] == 58
    # com produtividade real, financials usa cenário "real"
    fin = client.post(f"/api/v1/crop-cycles/{cid}/financials",
                     json={"price_per_bag": 125}).json()
    assert fin["yield_source"].startswith("produtividade real")


def test_patch_invalid_harvest_before_planting(client):
    cid = _setup_cycle(client)
    r = client.patch(f"/api/v1/crop-cycles/{cid}",
                    json={"actual_planting_date": "2026-11-01", "harvest_date": "2026-10-01"})
    assert r.status_code == 422
