"""Manejo por safra (snapshot) + histórico manejo×resultado (ADR-0026)."""

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


def _cycle(client) -> tuple[int, int]:
    farm = client.post("/api/v1/farms",
                       json={"name": "F", "municipality_code": 4309605}).json()
    fid = client.post(f"/api/v1/farms/{farm['id']}/fields",
                     json={"name": "T1", "area_ha": 100}).json()["id"]
    cid = client.post(f"/api/v1/fields/{fid}/crop-cycles",
                     json={"crop": "soja", "season": "2023/24"}).json()["id"]
    return fid, cid


def test_save_and_get_cycle_manejo(client):
    _, cid = _cycle(client)
    assert client.get(f"/api/v1/crop-cycles/{cid}/manejo").json()["profile"] == {}
    prof = {"fungicida": "nenhum", "cultivar": "antiga"}
    r = client.put(f"/api/v1/crop-cycles/{cid}/manejo", json={"profile": prof})
    assert r.status_code == 200 and r.json()["profile"] == prof
    assert client.get(f"/api/v1/crop-cycles/{cid}/manejo").json()["profile"] == prof


def test_cycle_manejo_validates(client):
    _, cid = _cycle(client)
    assert client.put(f"/api/v1/crop-cycles/{cid}/manejo",
                      json={"profile": {"fungicida": "x"}}).status_code == 422


def test_manejo_history_predicted_vs_actual(client):
    fid, cid = _cycle(client)
    client.put(f"/api/v1/crop-cycles/{cid}/manejo",
               json={"profile": {"fungicida": "nenhum"}})  # manejo ruim
    client.patch(f"/api/v1/crop-cycles/{cid}", json={"actual_yield_sc_ha": 35.0})
    hist = client.get(f"/api/v1/fields/{fid}/manejo-history").json()
    assert hist["n_seasons"] == 1
    row = hist["history"][0]
    assert row["manejo_source"] == "safra"
    assert row["manejo_effect_pct"] < 0          # fungicida nenhum reduz
    assert row["predicted_sc_ha"] is not None
    assert row["actual_sc_ha"] == 35.0
    assert row["delta_vs_predicted_pct"] is not None


def test_manejo_history_falls_back_to_field_profile(client):
    fid, cid = _cycle(client)
    # sem snapshot na safra, mas com perfil do talhão -> usa como proxy
    client.put(f"/api/v1/fields/{fid}/agronomic-profile",
               json={"profile": {"cultivar": "moderna"}})
    hist = client.get(f"/api/v1/fields/{fid}/manejo-history").json()
    assert hist["history"][0]["manejo_source"].startswith("perfil atual")
