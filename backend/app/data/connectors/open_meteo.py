"""Open-Meteo Historical Weather API (reanálise ERA5).

Fonte primária de clima por cobrir 1940+ (alinha com a série do IBGE desde 1974) e
fornecer dados diários consistentes por ponto. Documentação: https://open-meteo.com.
"""

from __future__ import annotations

from datetime import date

from app.data.connectors.base import HttpDataSource
from app.domain.climate import DailyWeather

_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


class OpenMeteoConnector:
    def __init__(self, source: HttpDataSource | None = None) -> None:
        self._http = source or HttpDataSource()

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
