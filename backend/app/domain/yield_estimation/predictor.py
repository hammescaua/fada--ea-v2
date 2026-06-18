"""Modelo regional de produtividade: inferência, intervalo e cenários.

A safra-alvo do MVP (2026/27) é futura: não há clima observado. Os cenários são
construídos a partir da **climatologia histórica** do município (percentis das
features de estresse), e a tendência tecnológica é projetada pelo termo de ano.
Honestidade-first (ADR-0003).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.domain.features import SOYBEAN_FEATURE_NAMES
from app.domain.units import kg_per_ha_to_bags_per_ha

# Para cada feature, qual percentil representa condição ADVERSA vs FAVORÁVEL.
# Déficit, veranico e dias quentes: mais alto = pior. Chuva total: mais alto = melhor.
_ADVERSE = {
    "water_deficit_reproductive_mm": "p90",
    "dry_spell_longest_reproductive_days": "p90",
    "hot_days_reproductive": "p90",
    "precip_total_season_mm": "p10",
}
_FAVORABLE = {
    "water_deficit_reproductive_mm": "p10",
    "dry_spell_longest_reproductive_days": "p10",
    "hot_days_reproductive": "p10",
    "precip_total_season_mm": "p90",
}
_NORMAL = {f: "p50" for f in SOYBEAN_FEATURE_NAMES}


@dataclass(frozen=True)
class Scenario:
    name: str
    yield_kg_ha: float
    yield_sc_ha: float


@dataclass(frozen=True)
class YieldEstimate:
    municipality_code: int
    municipality_name: str
    harvest_year: int
    point_sc_ha: float
    interval_sc_ha: tuple[float, float]
    scenarios: list[Scenario]
    drivers: dict[str, float]  # condições normais usadas (features)
    climatology: dict  # bloco do município (para riscos/explicação)


class RegionalYieldModel:
    """Wrapper de inferência sobre o artefato JSON (numpy puro)."""

    def __init__(self, artifact: dict) -> None:
        self._a = artifact
        self._names = artifact["feature_names"]
        self._mean = np.array(artifact["standardization"]["mean"])
        self._scale = np.array(artifact["standardization"]["scale"])
        self._coef = np.array(artifact["coefficients"])
        self._intercept = float(artifact["intercept"])

    @classmethod
    def load(cls, path: str | Path) -> RegionalYieldModel:
        return cls(json.loads(Path(path).read_text()))

    # -- inferência ---------------------------------------------------------
    def predict_kg_ha(self, feature_vector: dict[str, float]) -> float:
        x = np.array([feature_vector[n] for n in self._names], dtype=float)
        z = (x - self._mean) / self._scale
        return float(self._intercept + z @ self._coef)

    def municipalities(self) -> dict[str, dict]:
        return self._a["climatology"]["by_municipality"]

    def _muni_climatology(self, municipality_code: int) -> dict | None:
        return self.municipalities().get(str(municipality_code))

    def _features_at(self, climo: dict, selection: dict[str, str]) -> dict[str, float]:
        return {f: climo["features"][f][p] for f, p in selection.items()}

    def estimate(self, municipality_code: int, harvest_year: int) -> YieldEstimate:
        climo = self._muni_climatology(municipality_code)
        if climo is None:
            raise KeyError(municipality_code)

        def scenario(name: str, selection: dict[str, str]) -> Scenario:
            fv = self._features_at(climo, selection)
            fv["harvest_year"] = harvest_year
            kg = self.predict_kg_ha(fv)
            return Scenario(name, kg, kg_per_ha_to_bags_per_ha(kg))

        normal = scenario("normal", _NORMAL)
        pessimist = scenario("pessimista", {**_NORMAL, **_ADVERSE})
        optimist = scenario("otimista", {**_NORMAL, **_FAVORABLE})

        rq = self._a["residual_scha_quantiles"]
        interval = (
            round(normal.yield_sc_ha + rq["p10"], 1),
            round(normal.yield_sc_ha + rq["p90"], 1),
        )
        drivers = self._features_at(climo, _NORMAL)
        return YieldEstimate(
            municipality_code=municipality_code,
            municipality_name=climo["name"],
            harvest_year=harvest_year,
            point_sc_ha=round(normal.yield_sc_ha, 1),
            interval_sc_ha=interval,
            scenarios=[pessimist, normal, optimist],
            drivers=drivers,
            climatology=climo,
        )
