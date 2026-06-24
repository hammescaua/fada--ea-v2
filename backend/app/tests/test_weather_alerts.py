"""Testes do motor de alertas (puro) e do endpoint (forecast mockado, sem rede)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.weather import DailyForecast, build_alerts
from app.infra import models  # noqa: F401
from app.infra.db import Base, get_session


def _day(i: int) -> date:
    return date(2026, 6, 23) + timedelta(days=i)


def _fc(i, tmin, tmax, precip, prob, wind) -> DailyForecast:
    return DailyForecast(_day(i), tmin, tmax, precip, prob, wind)


# -- motor de alertas (puro) ------------------------------------------------

def test_frost_alert_fires_and_grades_severity():
    fc = [_fc(0, 0.5, 12, 0, 0, 10), _fc(1, 8, 18, 0, 0, 10)]
    alerts = {a.code: a for a in build_alerts(fc)}
    assert "geada" in alerts
    assert alerts["geada"].severity == "alerta"  # tmin <= 1 °C
    assert alerts["geada"].evidence["min_tmin_c"] == 0.5


def test_dry_spell_detected():
    fc = [_fc(i, 12, 28, 0.0, 5, 10) for i in range(7)]  # 7 dias secos seguidos
    alerts = {a.code: a for a in build_alerts(fc)}
    assert "veranico" in alerts
    assert alerts["veranico"].severity == "alerta"  # >= 7 dias
    assert alerts["veranico"].evidence["dry_days"] == 7


def test_dry_spell_breaks_on_rain():
    fc = [_fc(i, 12, 28, 0.0, 5, 10) for i in range(4)]
    fc.append(_fc(4, 12, 28, 20.0, 80, 10))  # chuva quebra a sequência
    fc += [_fc(i, 12, 28, 0.0, 5, 10) for i in range(5, 8)]
    alerts = {a.code: a for a in build_alerts(fc)}
    assert "veranico" not in alerts  # nenhuma sequência atinge 5


def test_spray_window_and_heavy_rain():
    fc = [
        _fc(0, 12, 26, 0.0, 10, 8),     # boa janela de pulverização
        _fc(1, 14, 27, 35.0, 80, 20),   # chuva intensa
    ]
    codes = {a.code for a in build_alerts(fc)}
    assert "janela_pulverizacao" in codes
    assert "chuva_intensa" in codes


def test_no_alerts_when_calm():
    fc = [_fc(i, 15, 26, 5.0, 50, 25) for i in range(5)]  # chove um pouco, sem extremos
    assert build_alerts(fc) == []


# -- endpoint (mock do connector — não bate na rede) ------------------------

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

    from app.api.v1.routes import weather as weather_route
    from app.main import app

    class _FakeConnector:
        def daily_forecast(self, latitude, longitude, days=16):
            return [_fc(0, 0.5, 12, 0, 0, 8), _fc(1, 9, 20, 0, 0, 10)]

    def fake_service(session=None):
        from app.infra.repositories import FarmRepository
        from app.services.weather import WeatherService
        return WeatherService(farms=FarmRepository(TS()), connector=_FakeConnector())

    app.dependency_overrides[get_session] = override
    app.dependency_overrides[weather_route.get_weather_service] = fake_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_weather_forecast_endpoint(client):
    r = client.get("/api/v1/weather/forecast?lat=-27.6&lon=-54.3")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "Open-Meteo Forecast"
    assert any(a["code"] == "geada" for a in body["alerts"])
    assert body["n_days"] == 2
