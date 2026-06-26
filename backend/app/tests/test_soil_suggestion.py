"""Sugestão de solo por município (EMBRAPA Solos) — ADR-0028."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.data.connectors.soil_suggestion import SoilSuggestionStore
from app.infra import models  # noqa: F401
from app.infra.db import Base, get_session
from app.main import app

_ARTIFACT = settings.data_dir / "geo" / "soil_suggestions.json"
pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")


def test_store_reads_fixture(tmp_path):
    doc = {
        "source": "EMBRAPA", "fetched_at": "2026-06-26", "note": "aprox",
        "municipalities": {"4309605": {
            "name": "Horizontina", "ordem_dominante": "LATOSSOLOS",
            "confidence": "baixa",
            "suggestion": {"profundidade_solo": "profundo", "textura_solo": "argiloso"},
        }},
    }
    p = tmp_path / "soil_suggestions.json"
    p.write_text(json.dumps(doc))
    store = SoilSuggestionStore(path=p)
    sug = store.for_municipality(4309605)
    assert sug["suggestion"]["profundidade_solo"] == "profundo"
    assert sug["source"] == "EMBRAPA"
    assert store.for_municipality(9999999) is None


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


@pytest.mark.skipif(not _ARTIFACT.exists(), reason="artefato de solo ausente")
def test_field_soil_suggestion_endpoint(client):
    farm = client.post("/api/v1/farms",
                       json={"name": "F", "municipality_code": 4309605}).json()
    fid = client.post(f"/api/v1/farms/{farm['id']}/fields",
                     json={"name": "T1", "area_ha": 100}).json()["id"]
    r = client.get(f"/api/v1/fields/{fid}/soil-suggestion")
    assert r.status_code == 200
    body = r.json()
    assert body["profile_fragment"]          # sugere ao menos um fator
    assert "EMBRAPA" in body["source"]
    assert body["confidence"] in ("baixa", "média")
