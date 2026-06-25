"""Domínio de previsão e alertas agronômicos (Open-Meteo Forecast)."""

from __future__ import annotations

from app.domain.weather.forecast import (
    Alert,
    DailyForecast,
    build_alerts,
)

__all__ = ["Alert", "DailyForecast", "build_alerts"]
