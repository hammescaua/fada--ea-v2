"""Testes de endpoint de Field Intelligence + Insights (DB isolado, modelo real)."""

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


def _seed_two_fields(client) -> int:
    farm = client.post("/api/v1/farms",
                      json={"name": "F", "municipality_code": 4309605}).json()
    fa = client.post(f"/api/v1/farms/{farm['id']}/fields",
                    json={"name": "Norte", "area_ha": 100}).json()
    fb = client.post(f"/api/v1/farms/{farm['id']}/fields",
                    json={"name": "Sul", "area_ha": 80}).json()
    for year in range(2019, 2025):
        s = f"{year - 1}/{str(year)[2:]}"
        client.post(f"/api/v1/fields/{fa['id']}/crop-cycles",
                   json={"crop": "soja", "season": s, "area_ha": 100, "actual_yield_sc_ha": 60})
        client.post(f"/api/v1/fields/{fb['id']}/crop-cycles",
                   json={"crop": "soja", "season": s, "area_ha": 80, "actual_yield_sc_ha": 42})
    return farm["id"]


def test_field_analytics(client):
    farm_id = _seed_two_fields(client)
    r = client.get(f"/api/v1/farms/{farm_id}/field-analytics")
    assert r.status_code == 200
    body = r.json()
    assert body["n_fields"] == 2
    assert body["n_records"] == 12
    assert all("bias_vs_region_pct" in f for f in body["fields"])


def test_insights_best_worst(client):
    farm_id = _seed_two_fields(client)
    r = client.get(f"/api/v1/farms/{farm_id}/insights")
    assert r.status_code == 200
    items = r.json()["insights"]
    types = {i["type"] for i in items}
    assert "best_field_yield" in types and "worst_field_yield" in types
    assert all(i["evidence"] for i in items)  # todo insight traz evidência


def test_insights_empty_farm(client):
    farm = client.post("/api/v1/farms",
                      json={"name": "Vazia", "municipality_code": 4309605}).json()
    r = client.get(f"/api/v1/farms/{farm['id']}/insights")
    assert r.status_code == 200
    assert r.json()["n_insights"] == 0


def test_field_analytics_404(client):
    assert client.get("/api/v1/farms/999/field-analytics").status_code == 404
