"""Endpoint de mercado + integração do preço ao vivo no Financeiro.

Usa o artefato real versionado em data/market/soja_price.json (CEPEA/ESALQ).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.infra import models  # noqa: F401
from app.infra.db import Base, get_session
from app.main import app

_PRICE_ARTIFACT = settings.data_dir / "market" / "soja_price.json"
pytestmark = pytest.mark.skipif(
    not settings.model_path.exists() or not _PRICE_ARTIFACT.exists(),
    reason="modelo ou artefato de preço ausente",
)


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


def test_market_price_endpoint():
    r = TestClient(app).get("/api/v1/market/price?crop=soja")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "CEPEA/ESALQ"
    assert body["unit"].startswith("BRL")
    assert body["summary"]["latest_value"] > 0
    assert len(body["series"]) >= 1
    assert "não prevê preço" in body["disclaimer"]


def test_market_price_unknown_crop_404():
    r = TestClient(app).get("/api/v1/market/price?crop=cevada")
    assert r.status_code == 404


def test_financials_defaults_to_live_price(client):
    cid = _setup_cycle(client)
    client.post(f"/api/v1/crop-cycles/{cid}/events",
               json={"event_type": "BASE_FERTILIZATION", "event_date": "2026-11-01",
                     "cost": 200000})
    # Sem price_per_bag: deve resolver pela cotação CEPEA do artefato.
    fin = client.post(f"/api/v1/crop-cycles/{cid}/financials", json={}).json()
    assert "CEPEA" in fin["price_source"]
    assert fin["price_per_bag"] > 0


def test_financials_explicit_price_wins(client):
    cid = _setup_cycle(client)
    client.post(f"/api/v1/crop-cycles/{cid}/events",
               json={"event_type": "BASE_FERTILIZATION", "event_date": "2026-11-01",
                     "cost": 200000})
    fin = client.post(f"/api/v1/crop-cycles/{cid}/financials",
                     json={"price_per_bag": 125}).json()
    assert fin["price_per_bag"] == 125
    assert fin["price_source"] == "informado pelo produtor"
