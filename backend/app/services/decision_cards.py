"""Agregador do Cartão de Decisão — funde as inteligências num só hub (guia §4/Fatia 2).

Não recalcula nada: reaproveita clima (proativo), recomendações econômicas
(manejo→R$) e flags de atenção (histórico), mapeando cada fonte para o contrato
único ``DecisionCard``. Degrada graciosamente por fonte.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.decision import (
    DecisionCard,
    from_attention_flag,
    from_economic_recommendation,
    from_weather_alert,
    sort_cards,
)
from app.domain.yield_estimation import RegionalYieldModel
from app.infra.repositories import AgronomicProfileRepository, FarmRepository
from app.services.decisions import DecisionsService
from app.services.decisions import FarmNotFound as DecisionFarmNotFound
from app.services.season_planning import SeasonPlanningService
from app.services.weather import ForecastUnavailable, LocationUnknown, WeatherService


@dataclass
class DecisionCardService:
    farms: FarmRepository
    profiles: AgronomicProfileRepository
    model: RegionalYieldModel
    weather: WeatherService
    decisions: DecisionsService
    season: SeasonPlanningService

    def cards(
        self, farm_id: int, field_id: int | None = None, season: str = "2026/27"
    ) -> list[DecisionCard]:
        cards: list[DecisionCard] = []
        cards += self._weather_cards(farm_id)
        if field_id is not None:
            cards += self._management_cards(field_id, season)
        cards += self._history_cards(farm_id)
        return sort_cards(cards)

    def _weather_cards(self, farm_id: int) -> list[DecisionCard]:
        try:
            payload = self.weather.forecast_for_farm(farm_id)
        except (LocationUnknown, ForecastUnavailable):
            return []
        return [from_weather_alert(vars(a)) for a in payload["alerts"]]

    def _management_cards(self, field_id: int, season: str) -> list[DecisionCard]:
        field = self.farms.get_field(field_id)
        if field is None:
            return []
        farm = self.farms.get_farm(field.farm_id)
        info = self.model.municipalities().get(str(farm.municipality_code))
        profile = self.profiles.get(field_id)
        if info is None or not profile:
            return []
        try:
            brief = self.season.brief(info["name"], season=season, profile=profile)
        except Exception:  # noqa: BLE001 — fonte opcional; nunca derruba o hub
            return []
        recs = brief.get("recommendations") or []
        return [from_economic_recommendation(r) for r in recs]

    def _history_cards(self, farm_id: int) -> list[DecisionCard]:
        try:
            d = self.decisions.decisions(farm_id)
        except DecisionFarmNotFound:
            return []
        out: list[DecisionCard] = []
        for fld in d.get("fields", []):
            for flag in fld.get("flags", []):
                out.append(from_attention_flag(fld["field_name"], flag))
        return out
