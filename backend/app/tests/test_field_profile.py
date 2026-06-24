"""Persistência do Perfil Agronômico por talhão + integração no brief de safra."""

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


def _field(client) -> int:
    farm = client.post("/api/v1/farms",
                       json={"name": "F", "municipality_code": 4309605}).json()
    return client.post(f"/api/v1/farms/{farm['id']}/fields",
                      json={"name": "T1", "area_ha": 100}).json()["id"]


def test_save_and_get_profile(client):
    fid = _field(client)
    # vazio inicialmente
    assert client.get(f"/api/v1/fields/{fid}/agronomic-profile").json()["profile"] == {}
    # salva
    prof = {"textura_solo": "argiloso", "cultivar": "moderna"}
    r = client.put(f"/api/v1/fields/{fid}/agronomic-profile", json={"profile": prof})
    assert r.status_code == 200 and r.json()["profile"] == prof
    # persiste (upsert)
    again = client.get(f"/api/v1/fields/{fid}/agronomic-profile").json()
    assert again["profile"] == prof


def test_save_profile_validates(client):
    fid = _field(client)
    r = client.put(f"/api/v1/fields/{fid}/agronomic-profile",
                   json={"profile": {"fungicida": "invalido"}})
    assert r.status_code == 422


def test_field_estimate_uses_stored_profile(client):
    fid = _field(client)
    client.put(f"/api/v1/fields/{fid}/agronomic-profile",
               json={"profile": {"textura_solo": "arenoso", "fungicida": "nenhum"}})
    est = client.get(f"/api/v1/fields/{fid}/estimate").json()
    assert est["personalized"]["point_sc_ha"] < est["regional"]["point_sc_ha"]
    assert est["adjustment"]["factors"]


def test_season_brief_personalized_by_field(client):
    fid = _field(client)
    # brief regional (sem perfil)
    base = client.get(f"/api/v1/planning/season-brief?field_id={fid}").json()
    assert base["yield"]["personalized"] is False
    # com perfil ruim → produtividade e margem caem vs regional
    client.put(f"/api/v1/fields/{fid}/agronomic-profile",
               json={"profile": {"fungicida": "nenhum", "nematoides": "alta"}})
    pers = client.get(f"/api/v1/planning/season-brief?field_id={fid}").json()
    assert pers["yield"]["personalized"] is True
    assert pers["yield"]["expected_sc_ha"] < base["yield"]["expected_sc_ha"]
    assert pers["yield"]["adjustment"]["factors"]


def test_season_brief_requires_municipality_or_field(client):
    assert client.get("/api/v1/planning/season-brief").status_code == 422
