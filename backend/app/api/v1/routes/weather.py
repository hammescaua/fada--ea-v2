"""Endpoints de previsão e alertas (Open-Meteo Forecast)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.infra.db import get_session
from app.infra.repositories import FarmRepository
from app.schemas.weather import AlertOut, DailyForecastOut, ForecastResponse
from app.services.weather import (
    ForecastUnavailable,
    LocationUnknown,
    WeatherService,
)

router = APIRouter()


def get_weather_service(session: Session = Depends(get_session)) -> WeatherService:
    return WeatherService(farms=FarmRepository(session))


def _response(data: dict) -> ForecastResponse:
    return ForecastResponse(
        latitude=data["latitude"],
        longitude=data["longitude"],
        n_days=data["n_days"],
        from_day=data["from_day"],
        to_day=data["to_day"],
        location_source=data.get("location_source"),
        alerts=[AlertOut(**vars(a)) for a in data["alerts"]],
        forecast=[DailyForecastOut(**vars(f)) for f in data["forecast"]],
        source=data["source"],
        disclaimer=data["disclaimer"],
    )


@router.get("/weather/forecast", response_model=ForecastResponse)
def weather_forecast_endpoint(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    days: int = Query(16, ge=1, le=16),
    svc: WeatherService = Depends(get_weather_service),
) -> ForecastResponse:
    try:
        return _response(svc.forecast_at(lat, lon, days))
    except ForecastUnavailable as exc:
        raise HTTPException(502, "Previsão indisponível no momento (fonte externa).") from exc


@router.get("/farms/{farm_id}/weather", response_model=ForecastResponse)
def farm_weather_endpoint(
    farm_id: int,
    days: int = Query(16, ge=1, le=16),
    svc: WeatherService = Depends(get_weather_service),
) -> ForecastResponse:
    try:
        return _response(svc.forecast_for_farm(farm_id, days))
    except LocationUnknown as exc:
        raise HTTPException(
            422,
            "Sem localização: georreferencie um talhão (lat/lon) ou use um município "
            "coberto pelo mapa de centroides.",
        ) from exc
    except ForecastUnavailable as exc:
        raise HTTPException(502, "Previsão indisponível no momento (fonte externa).") from exc
