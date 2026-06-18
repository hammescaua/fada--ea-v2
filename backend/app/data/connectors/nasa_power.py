"""NASA POWER — séries climáticas diárias por ponto (community AG).

Fonte secundária / de validação cruzada do Open-Meteo. Cobre 1981+. Valores
ausentes são sinalizados como -999 e descartados. Doc: https://power.larc.nasa.gov.
"""

from __future__ import annotations

from datetime import date

from app.data.connectors.base import HttpDataSource
from app.domain.climate import DailyWeather

_POINT_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
_FILL = -999.0


class NasaPowerConnector:
    def __init__(self, source: HttpDataSource | None = None) -> None:
        self._http = source or HttpDataSource()

    def daily_weather(
        self, latitude: float, longitude: float, start: date, end: date
    ) -> list[DailyWeather]:
        data = self._http.get_json(
            _POINT_URL,
            params={
                "parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR",
                "community": "AG",
                "latitude": latitude,
                "longitude": longitude,
                "start": start.strftime("%Y%m%d"),
                "end": end.strftime("%Y%m%d"),
                "format": "JSON",
            },
        )
        params = data["properties"]["parameter"]
        tmax_s, tmin_s, prcp_s = params["T2M_MAX"], params["T2M_MIN"], params["PRECTOTCORR"]
        out: list[DailyWeather] = []
        for key in sorted(tmax_s):
            tmax, tmin, prcp = tmax_s[key], tmin_s[key], prcp_s.get(key, 0.0)
            if tmax == _FILL or tmin == _FILL:
                continue
            out.append(
                DailyWeather(
                    day=date(int(key[:4]), int(key[4:6]), int(key[6:8])),
                    tmin=float(tmin),
                    tmax=float(tmax),
                    precipitation_mm=max(0.0, float(prcp)) if prcp != _FILL else 0.0,
                )
            )
        return out
