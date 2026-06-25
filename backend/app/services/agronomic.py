"""Serviço agronômico: estimativa personalizada por perfil (a priori, dia 1).

Compõe a estimativa regional com o ajuste do Perfil Agronômico FADA. Resultado:
duas fazendas vizinhas com solos/manejos diferentes passam a receber **previsões
diferentes**, antes de qualquer histórico — com cada fator do ajuste explicado.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.agronomy import (
    FACTORS,
    apply_adjustment,
    compute_adjustment,
    for_factor,
    guide,
    recommendations,
    scenario_multipliers,
    water_sensitivity_note,
)
from app.services.regional_intelligence import RegionalIntelligenceService

_DISCLAIMER = (
    "Estimativa ajustada pelo Perfil Agronômico (base técnica Embrapa/CQFS-RS-SC), "
    "que desloca a expectativa regional pelos fatores do seu talhão. É um ajuste "
    "agronômico a priori — ainda não validado pela sua colheita; por isso o intervalo "
    "alarga. Conforme você registrar safras, a personalização passa a aprender do seu "
    "dado real."
)


@dataclass
class AgronomicService:
    regional: RegionalIntelligenceService

    def factors_catalog(self) -> list[dict]:
        """Catálogo do questionário padronizado (para a UI montar o formulário).

        Cada fator vem enriquecido com a explicação **com fonte** do guia agronômico
        (ADR-0027), quando disponível.
        """
        out = []
        for f in FACTORS.values():
            entry = for_factor(f.key)
            out.append({
                "key": f.key,
                "question": f.question,
                "rationale": f.rationale,
                "confidence": f.confidence,
                "explanation": entry.explanation if entry else None,
                "sources": list(entry.sources) if entry else [],
                "options": [
                    {"value": v, "label": o.label, "effect_pct": round(o.effect * 100, 1)}
                    for v, o in f.options.items()
                ],
            })
        return out

    def knowledge_guide(self) -> list[dict]:
        """Guia agronômico citável (fatores + temas) — o 'por quê' com fonte."""
        return [
            {
                "key": e.key, "title": e.title, "explanation": e.explanation,
                "practical": e.practical, "sources": list(e.sources),
            }
            for e in guide()
        ]

    def personalized_estimate(
        self, municipality: str, crop: str, season: str, profile: dict[str, str]
    ) -> dict:
        reg = self.regional.run(municipality, crop, season)
        scenarios = {s["name"]: s["yield_sc_ha"] for s in reg["scenarios"]}
        adjustment = compute_adjustment(profile)
        est = apply_adjustment(
            regional_point_sc_ha=reg["estimated_yield_sc_ha"],
            regional_interval_sc_ha=tuple(reg["confidence_interval_sc_ha"]),
            scenarios_sc_ha=scenarios,
            adjustment=adjustment,
            scenario_multipliers=scenario_multipliers(profile),
        )
        recs = recommendations(profile, est.personalized_point_sc_ha)
        return {
            "municipality": reg["municipality"],
            "municipality_code": reg["municipality_code"],
            "crop": crop,
            "season": season,
            "harvest_year": reg["harvest_year"],
            "regional": {
                "point_sc_ha": est.regional_point_sc_ha,
                "interval_sc_ha": list(est.regional_interval_sc_ha),
            },
            "personalized": {
                "point_sc_ha": est.personalized_point_sc_ha,
                "interval_sc_ha": list(est.personalized_interval_sc_ha),
                "scenarios": [
                    {"name": n, "yield_sc_ha": y} for n, y in est.scenarios_sc_ha.items()
                ],
            },
            "adjustment": {
                "multiplier": est.multiplier,
                "total_effect_pct": est.total_effect_pct,
                "clamped": adjustment.clamped,
                "n_factors": adjustment.n_factors,
                "factors": [vars(a) for a in adjustment.applied],
            },
            "recommendations": [vars(r) for r in recs],
            "water_sensitivity_note": water_sensitivity_note(profile),
            "climatic_risks": reg["climatic_risks"],
            "data_sources": reg["data_sources"] + ["Perfil Agronômico FADA (ajuste a priori)"],
            "disclaimer": _DISCLAIMER,
        }
