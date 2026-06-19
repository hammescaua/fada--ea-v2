"""Testes de endpoint de planejamento + captura rápida (DB isolado)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infra import models  # noqa: F401
from app.infra.db import Base, get_session
from app.main import app


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


def _two_cycles(client):
    farm = client.post("/api/v1/farms", json={"name": "F", "municipality_code": 4309605}).json()
    fa = client.post(f"/api/v1/farms/{farm['id']}/fields",
                    json={"name": "Norte", "area_ha": 100}).json()
    fb = client.post(f"/api/v1/farms/{farm['id']}/fields",
                    json={"name": "Sul", "area_ha": 80}).json()
    ca = client.post(f"/api/v1/fields/{fa['id']}/crop-cycles", json={
        "crop": "soja", "season": "2026/27", "area_ha": 100,
        "target_yield_sc_ha": 58, "expected_price_per_bag": 125}).json()["id"]
    cb = client.post(f"/api/v1/fields/{fb['id']}/crop-cycles", json={
        "crop": "soja", "season": "2026/27", "area_ha": 80}).json()["id"]
    return ca, cb


def test_quick_log_multiple_cycles_with_preset(client):
    ca, cb = _two_cycles(client)
    preset = client.post("/api/v1/event-presets", json={
        "name": "Fungicida", "event_type": "FUNGICIDE", "default_cost": 220,
        "cost_is_per_hectare": True}).json()
    r = client.post("/api/v1/quick-log", json={
        "crop_cycle_ids": [ca, cb], "event_date": "2027-01-12", "preset_id": preset["id"]})
    assert r.status_code == 201
    created = r.json()["created"]
    assert len(created) == 2
    assert created[0]["cost"] == 22000.0  # 100 ha
    assert created[1]["cost"] == 17600.0  # 80 ha


def test_quick_log_requires_type_or_preset(client):
    ca, _ = _two_cycles(client)
    r = client.post("/api/v1/quick-log",
                   json={"crop_cycle_ids": [ca], "event_date": "2027-01-12"})
    assert r.status_code == 422


def test_plan_vs_actual_endpoint(client):
    ca, _ = _two_cycles(client)
    for et, d, cost in [("BASE_FERTILIZATION", "2026-11-01", 120000),
                        ("FUNGICIDE", "2027-01-10", 40000)]:
        client.post(f"/api/v1/crop-cycles/{ca}/planned-events",
                   json={"event_type": et, "planned_date": d, "expected_cost": cost})
    client.post(f"/api/v1/crop-cycles/{ca}/events",
               json={"event_type": "BASE_FERTILIZATION", "event_date": "2026-11-01",
                     "cost": 130000})
    pva = client.get(f"/api/v1/crop-cycles/{ca}/plan-vs-actual").json()
    assert pva["planned_total_cost"] == 160000.0
    assert pva["over_budget"] is False
    assert pva["remaining_budget"] == 30000.0
    assert pva["expected_profit"] == 565000.0
    assert "interpretation" in pva


def test_agenda_endpoint(client):
    ca, _ = _two_cycles(client)
    client.post(f"/api/v1/crop-cycles/{ca}/planned-events",
               json={"event_type": "HERBICIDE", "planned_date": "2026-11-20",
                     "expected_cost": 18000})
    ag = client.get(f"/api/v1/crop-cycles/{ca}/agenda").json()
    assert ag["crop_cycle_id"] == ca
    assert len(ag["items"]) == 1
    assert "summary" in ag


def test_plan_vs_actual_404(client):
    assert client.get("/api/v1/crop-cycles/999/plan-vs-actual").status_code == 404


def test_assistant_cost_total_with_context(client):
    # Aceite 1.2: pergunta de custo com crop_cycle_id retorna o valor (não "selecione")
    ca, _ = _two_cycles(client)
    client.post(f"/api/v1/crop-cycles/{ca}/events",
               json={"event_type": "BASE_FERTILIZATION", "event_date": "2026-11-01",
                     "cost": 120000})
    r = client.post("/api/v1/assistant", json={
        "message": "Quanto já gastei nesta safra?", "crop_cycle_id": ca}).json()
    assert r["intent"] == "cost_total"
    assert "120000" in r["answer"]
    assert "selecione" not in r["answer"].lower()


def test_assistant_budget_questions(client):
    ca, _ = _two_cycles(client)
    client.post(f"/api/v1/crop-cycles/{ca}/planned-events",
               json={"event_type": "BASE_FERTILIZATION", "planned_date": "2026-11-01",
                     "expected_cost": 100000})
    client.post(f"/api/v1/crop-cycles/{ca}/events",
               json={"event_type": "BASE_FERTILIZATION", "event_date": "2026-11-01",
                     "cost": 60000})
    r = client.post("/api/v1/assistant", json={
        "message": "Quanto ainda falta investir?", "crop_cycle_id": ca}).json()
    assert r["intent"] == "remaining_budget"
    assert "40000" in r["answer"]
