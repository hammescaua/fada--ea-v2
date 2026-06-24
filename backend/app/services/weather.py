"""Serviço de previsão e alertas — resolve coordenadas e roda o motor de alertas.

Resolução de lat/lon (em ordem): talhão com coordenadas → centroide do município
da fazenda. A previsão é ao vivo; se a fonte falhar, o serviço sinaliza
indisponibilidade em vez de inventar (ADR-0003).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.data.connectors.municipality_geo import MunicipalityCentroidStore
from app.data.connectors.open_meteo import OpenMeteoConnector
from app.domain.weather import Alert, DailyForecast, build_alerts
from app.infra.repositories import FarmRepository


class LocationUnknown(Exception):
    """Sem coordenadas: nem talhão georreferenciado, nem centroide do município."""


class ForecastUnavailable(Exception):
    """A fonte de previsão (Open-Meteo) não respondeu — não inventamos clima."""


@dataclass
class WeatherService:
    farms: FarmRepository
    connector: OpenMeteoConnector = field(default_factory=OpenMeteoConnector)
    centroids: MunicipalityCentroidStore = field(default_factory=MunicipalityCentroidStore)

    def forecast_at(self, latitude: float, longitude: float, days: int = 16) -> dict:
        try:
            fc = self.connector.daily_forecast(latitude, longitude, days)
        except Exception as exc:  # noqa: BLE001 — rede instável: degrada graciosamente
            raise ForecastUnavailable(str(exc)) from exc
        return _payload(latitude, longitude, fc)

    def forecast_for_farm(self, farm_id: int, days: int = 16) -> dict:
        lat, lon, origin = self._resolve_farm_location(farm_id)
        out = self.forecast_at(lat, lon, days)
        out["location_source"] = origin
        return out

    def _resolve_farm_location(self, farm_id: int) -> tuple[float, float, str]:
        farm = self.farms.get_farm(farm_id)
        if farm is None:
            raise LocationUnknown(f"farm {farm_id}")
        for fld in self.farms.list_fields(farm_id):
            if fld.latitude is not None and fld.longitude is not None:
                return float(fld.latitude), float(fld.longitude), f"talhão {fld.name}"
        latlon = self.centroids.latlon(farm.municipality_code)
        if latlon is None:
            raise LocationUnknown(f"município {farm.municipality_code}")
        return latlon[0], latlon[1], "centroide do município"


def _payload(latitude: float, longitude: float, fc: list[DailyForecast]) -> dict:
    alerts = build_alerts(fc)
    return {
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "n_days": len(fc),
        "from_day": fc[0].day if fc else None,
        "to_day": fc[-1].day if fc else None,
        "alerts": alerts,
        "forecast": fc,
        "source": "Open-Meteo Forecast",
        "disclaimer": _disclaimer(alerts),
    }


def _disclaimer(alerts: list[Alert]) -> str:
    base = (
        "Previsão do Open-Meteo (modelos numéricos). Previsão erra — a confiança "
        "cai com o horizonte e alertas de chuva trazem a probabilidade, nunca certeza."
    )
    if not alerts:
        base = "Sem alertas no horizonte previsto. " + base
    return base
