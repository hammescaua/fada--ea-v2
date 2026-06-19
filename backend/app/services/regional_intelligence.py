"""Caso de uso: Inteligência Regional (Modo Básico).

Entrada: município + cultura + safra. Saída: produtividade estimada, intervalo,
cenários, riscos climáticos, janela de plantio e explicação em linguagem natural.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from app.domain.crop import SOYBEAN_RS
from app.domain.yield_estimation import RegionalYieldModel
from app.domain.yield_estimation.risk import assess_climatic_risks
from app.engine import Explainer

DATA_SOURCES = [
    "IBGE/PAM (rendimento municipal, tabela 1612)",
    "Open-Meteo / ERA5 (reanálise climática)",
    "NASA POWER (clima, fonte secundária)",
]
DISCLAIMER = (
    "Estimativa probabilística regional baseada em dados históricos e climatologia. "
    "Não considera ainda solo, manejo ou cultivar específicos da propriedade. "
    "Não é garantia de produtividade."
)


class CropNotSupported(Exception):
    pass


class MunicipalityNotInRegion(Exception):
    pass


class InvalidSeason(Exception):
    pass


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.strip().lower()


def parse_harvest_year(season: str) -> int:
    """'2026/27' -> 2027 (ano de colheita). Aceita também 'AAAA'."""
    try:
        first = season.split("/")[0].strip()
        year = int(first)
        return year + 1 if "/" in season else year
    except (ValueError, IndexError) as exc:
        raise InvalidSeason(season) from exc


@dataclass
class RegionalIntelligenceService:
    model: RegionalYieldModel
    explainer: Explainer

    def _resolve_municipality(self, name: str) -> tuple[int, str]:
        target = _normalize(name)
        for code, info in self.model.municipalities().items():
            if _normalize(info["name"]) == target:
                return int(code), info["name"]
        raise MunicipalityNotInRegion(name)

    def run(self, municipality: str, crop: str, season: str) -> dict:
        if _normalize(crop) != "soja":
            raise CropNotSupported(crop)

        harvest_year = parse_harvest_year(season)
        code, canonical = self._resolve_municipality(municipality)
        estimate = self.model.estimate(code, harvest_year)
        risks = assess_climatic_risks(estimate)

        pw_start, pw_end = SOYBEAN_RS.planting_window_for(harvest_year)
        opt_start, opt_end = SOYBEAN_RS.planting_optimal_for(harvest_year)
        planting_window = {
            "start": pw_start.strftime("%d/%m/%Y"),
            "end": pw_end.strftime("%d/%m/%Y"),
            "optimal_start": opt_start.strftime("%d/%m/%Y"),
            "optimal_end": opt_end.strftime("%d/%m/%Y"),
            "rationale": (
                "Janela do Zoneamento Agrícola de Risco Climático (ZARC) para soja no "
                "Noroeste do RS, que posiciona o período reprodutivo na fase de menor "
                "risco hídrico histórico."
            ),
        }

        risks_payload = [
            {"factor": r.factor, "severity": r.severity, "description": r.description,
             "metric": r.metric}
            for r in risks
        ]
        scenarios_payload = [
            {"name": s.name, "yield_sc_ha": round(s.yield_sc_ha, 1)} for s in estimate.scenarios
        ]

        explain_payload = {
            "municipality": canonical,
            "season": season,
            "point_sc_ha": estimate.point_sc_ha,
            "interval_sc_ha": list(estimate.interval_sc_ha),
            "scenarios": scenarios_payload,
            "risks": risks_payload,
            "planting_window": planting_window,
            "n_years": estimate.climatology["n_years"],
        }
        explanation = self.explainer.explain(explain_payload)

        n_years = estimate.climatology["n_years"]
        reasoning = {
            "n_years": n_years,
            "method": (
                "Estimativa regional (regressão sobre índices agroclimáticos) com a "
                "tendência tecnológica projetada para a safra; cenários a partir da "
                "climatologia histórica do município."
            ),
            "interval_basis": (
                "Intervalo de ~80% construído a partir dos quantis dos resíduos "
                "out-of-fold do modelo — reflete a incerteza climática do ano e não é "
                "estreitado artificialmente."
            ),
        }

        return {
            "municipality": canonical,
            "municipality_code": code,
            "crop": "soja",
            "season": season,
            "harvest_year": harvest_year,
            "estimated_yield_sc_ha": estimate.point_sc_ha,
            "confidence_interval_sc_ha": estimate.interval_sc_ha,
            "scenarios": scenarios_payload,
            "climatic_risks": risks_payload,
            "planting_window": planting_window,
            "explanation": explanation,
            "n_years": n_years,
            "reasoning": reasoning,
            "data_sources": DATA_SOURCES,
            "disclaimer": DISCLAIMER,
        }
