"""Testes da convergência perfil (a priori) + colheitas (a posteriori) — ADR-0025."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domain.adaptive import personalize
from app.infra import models  # noqa: F401
from app.infra.db import Base, get_session
from app.main import app

pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")


# -- convergência (puro) ----------------------------------------------------

def test_no_harvest_uses_profile_prior():
    # n=0 -> w=0 -> aplica o prior do perfil (não o regional/0).
    pred = personalize(50.0, (40.0, 60.0), {"normal": 50.0},
                       n_cycles=0, observed_bias=0.0, variance_relative=0.0,
                       prior_bias=0.10)
    assert pred.farm_adjustment_pct == 10.0          # = prior do perfil
    assert pred.prior_bias_pct == 10.0
    assert pred.personalized_point_sc_ha == 55.0


def test_converges_toward_harvest_data():
    # Muitas colheitas consistentes -> aproxima do observado, longe do prior.
    few = personalize(50.0, (40.0, 60.0), {"normal": 50.0},
                      n_cycles=1, observed_bias=-0.20, variance_relative=0.01,
                      prior_bias=0.10)
    many = personalize(50.0, (40.0, 60.0), {"normal": 50.0},
                       n_cycles=8, observed_bias=-0.20, variance_relative=0.01,
                       prior_bias=0.10)
    # com mais colheitas, o ajuste se aproxima do observado (-20%)
    assert many.confidence_score > few.confidence_score
    assert many.farm_adjustment_pct < few.farm_adjustment_pct
    assert many.farm_adjustment_pct < 0  # já puxou para o real (negativo)


def test_prior_zero_is_backward_compatible():
    pred = personalize(50.0, (40.0, 60.0), {"normal": 50.0},
                       n_cycles=0, observed_bias=0.0, variance_relative=0.0)
    assert pred.farm_adjustment_pct == 0.0 and pred.personalized_point_sc_ha == 50.0


# -- endpoint (aprende com colheita real) -----------------------------------

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


def _field(client) -> tuple[int, int]:
    farm = client.post("/api/v1/farms",
                       json={"name": "F", "municipality_code": 4309605}).json()
    fid = client.post(f"/api/v1/farms/{farm['id']}/fields",
                     json={"name": "T1", "area_ha": 100}).json()["id"]
    return farm["id"], fid


def test_learned_estimate_starts_at_profile(client):
    _, fid = _field(client)
    client.put(f"/api/v1/fields/{fid}/agronomic-profile",
               json={"profile": {"cultivar": "moderna"}})  # prior positivo
    body = client.get(f"/api/v1/fields/{fid}/learned-estimate").json()
    assert body["n_harvests"] == 0
    assert body["a_priori_profile_pct"] != 0.0
    # sem colheita, aplicado == prior do perfil
    assert body["applied_pct"] == body["a_priori_profile_pct"]


def test_learned_estimate_adapts_with_harvest(client):
    _, fid = _field(client)
    # cria uma safra passada com produtividade real baixa
    cyc = client.post(f"/api/v1/fields/{fid}/crop-cycles",
                     json={"crop": "soja", "season": "2023/24"}).json()
    client.patch(f"/api/v1/crop-cycles/{cyc['id']}", json={"actual_yield_sc_ha": 20.0})
    body = client.get(f"/api/v1/fields/{fid}/learned-estimate").json()
    assert body["n_harvests"] == 1
    assert body["residual_history"]
    assert body["confidence_score"] > 0  # já começou a aprender
