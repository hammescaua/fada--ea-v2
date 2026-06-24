"""DTOs de previsão e alertas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class DailyForecastOut(BaseModel):
    day: date
    tmin: float
    tmax: float
    precipitation_mm: float
    precipitation_prob: float
    wind_max_kmh: float


class AlertOut(BaseModel):
    code: str
    severity: str
    title: str
    detail: str
    starts_on: date
    ends_on: date
    confidence: str
    evidence: dict


class ForecastResponse(BaseModel):
    latitude: float
    longitude: float
    n_days: int
    from_day: date | None
    to_day: date | None
    location_source: str | None = None
    alerts: list[AlertOut]
    forecast: list[DailyForecastOut]
    source: str
    disclaimer: str
