"""Open-Meteo Historical Weather API (reanálise ERA5).

Fonte primária de clima por cobrir 1940+ (alinha com a série do IBGE desde 1974) e
fornecer dados diários consistentes por ponto. Documentação: https://open-meteo.com.
"""

from __future__ import annotations

from datetime import date

from app.data.connectors.base import HttpDataSource
from app.domain.climate import DailyWeather
from app.domain.weather import DailyForecast

_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


_FORECAST_DAILY = (
    "temperature_2m_max,temperature_2m_min,precipitation_sum,"
    "precipitation_probability_max,windspeed_10m_max"
)


class OpenMeteoConnector:
    def __init__(self, source: HttpDataSource | None = None) -> None:
        self._http = source or HttpDataSource()
        # Previsão deve ser sempre fresca: cache de disco desligado (ao vivo).
        self._forecast_http = HttpDataSource(use_cache=False, timeout=20.0)

    def daily_forecast(
        self, latitude: float, longitude: float, days: int = 16
    ) -> list[DailyForecast]:
        """Previsão diária (até 16 dias). Ao vivo — sem cache de disco."""
        data = self._forecast_http.get_json(
            _FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": _FORECAST_DAILY,
                "forecast_days": days,
                "timezone": "America/Sao_Paulo",
            },
        )
        daily = data["daily"]
        out: list[DailyForecast] = []
        for d, tmax, tmin, prcp, prob, wind in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_sum"],
            daily["precipitation_probability_max"],
            daily["windspeed_10m_max"],
            strict=True,
        ):
            if tmax is None or tmin is None:
                continue
            out.append(
                DailyForecast(
                    day=date.fromisoformat(d),
                    tmin=float(tmin),
                    tmax=float(tmax),
                    precipitation_mm=float(prcp or 0.0),
                    precipitation_prob=float(prob or 0.0),
                    wind_max_kmh=float(wind or 0.0),
                )
            )
        return out

    def daily_weather(
        self, latitude: float, longitude: float, start: date, end: date
    ) -> list[DailyWeather]:
        data = self._http.get_json(
            _ARCHIVE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "America/Sao_Paulo",
            },
        )
        daily = data["daily"]
        out: list[DailyWeather] = []
        for d, tmax, tmin, prcp in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_sum"],
            strict=True,
        ):
            if tmax is None or tmin is None:
                continue
            out.append(
                DailyWeather(
                    day=date.fromisoformat(d),
                    tmin=float(tmin),
                    tmax=float(tmax),
                    precipitation_mm=float(prcp or 0.0),
                )
            )
        return out
