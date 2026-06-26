"""Testes do Cartão de Decisão (contrato §4): construtores puros + endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domain.decision import (
    from_attention_flag,
    from_economic_recommendation,
    from_weather_alert,
    sort_cards,
)
from app.infra import models  # noqa: F401
from app.infra.db import Base, get_session
from app.main import app

pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")


# -- construtores (puros) ---------------------------------------------------

def test_weather_alert_card_has_no_numeric_effect_and_maps_confidence():
    alert = {
        "code": "geada", "severity": "alerta", "title": "Risco de geada",
        "detail": "Mínima de 2°C", "starts_on": "2026-06-25", "ends_on": "2026-06-26",
        "confidence": "alta", "evidence": {"min_tmin_c": 2.0},
    }
    card = from_weather_alert(alert)
    assert card.source == "clima" and card.effect is None
    assert card.confidence == "alta" and card.severity == "alerta"
    assert card.why and card.why[0].label == "min_tmin_c"


def test_economic_recommendation_card_effect_always_has_interval():
    rec = {
        "key": "fungicida", "question": "Programa de fungicida (ferrugem)",
        "current_label": "Nenhum", "target_label": "Completo",
        "gain_sc_ha": 11.0, "yield_gain_rs_ha": 1430.0, "cost_change_rs_ha": 470.0,
        "net_gain_rs_ha": 960.0, "rationale": "Ferrugem corta produtividade.",
        "confidence": "alta",
    }
    card = from_economic_recommendation(rec)
    assert card.source == "manejo"
    low, point, high = card.effect.profit_brl_ha
    assert low < point < high and point == 960.0    # sempre intervalo, nunca seco
    ylow, ypoint, yhigh = card.effect.yield_sc_ha
    assert ylow < ypoint < yhigh


def test_attention_flag_card():
    card = from_attention_flag("Talhão Sede", {
        "code": "custo_ha_alto", "severity": "atenção", "title": "Custo alto",
        "detail": "R$ 1.800/ha", "confidence": "média", "evidence": {},
    })
    assert card.source == "historico" and card.confidence == "moderada"


def test_sort_orders_climate_first():
    clima = from_weather_alert({
        "code": "geada", "severity": "alerta", "title": "x", "detail": "y",
        "starts_on": "a", "ends_on": "b", "confidence": "alta", "evidence": {},
    })
    hist = from_attention_flag("T", {"code": "instavel", "severity": "alerta",
                                     "title": "x", "detail": "y", "confidence": "baixa",
                                     "evidence": {}})
    ordered = sort_cards([hist, clima])
    assert ordered[0].source == "clima"


# -- endpoint ---------------------------------------------------------------

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


def test_decision_cards_endpoint_with_management(client):
    farm = client.post("/api/v1/farms",
                       json={"name": "F", "municipality_code": 4309605}).json()
    fid = client.post(f"/api/v1/farms/{farm['id']}/fields",
                     json={"name": "T1", "area_ha": 100}).json()["id"]
    client.put(f"/api/v1/fields/{fid}/agronomic-profile",
               json={"profile": {"fungicida": "nenhum", "inoculacao": "nao"}})
    r = client.get(f"/api/v1/farms/{farm['id']}/decision-cards?field_id={fid}")
    assert r.status_code == 200
    body = r.json()
    manejo = [c for c in body["cards"] if c["source"] == "manejo"]
    assert manejo, "deve haver cartões de manejo a partir do perfil"
    assert manejo[0]["effect"]["profit_brl_ha"] is not None


def test_decision_cards_farm_not_found(client):
    assert client.get("/api/v1/farms/999/decision-cards").status_code == 404
