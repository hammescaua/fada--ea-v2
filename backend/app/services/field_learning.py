"""Aprendizado por talhão — unifica o Perfil Agronômico (a priori) com o histórico
de colheitas (a posteriori). É a "adaptação no tempo" do FADA (ADR-0025).

A previsão **parte do perfil agronômico** (conhecimento, dia 1) e, a cada colheita
registrada, **encolhe em direção ao dado real do talhão**. Sem colheita, é o perfil;
com muitas colheitas consistentes, é praticamente o dado real. O intervalo nunca
estreita artificialmente (a incerteza climática do ano é irredutível).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from app.domain.adaptive import ShrinkagePrior, personalize
from app.domain.agronomy import compute_adjustment
from app.domain.farm import Season
from app.domain.yield_estimation import RegionalYieldModel
from app.infra.repositories import AgronomicProfileRepository, FarmRepository
from app.services.regional_fitted import regional_fitted_sc_ha


class FieldNotFound(Exception):
    pass


@dataclass
class FieldLearningService:
    farms: FarmRepository
    profiles: AgronomicProfileRepository
    model: RegionalYieldModel
    prior: ShrinkagePrior = ShrinkagePrior()

    def _residuals(self, field_id: int, municipality_code: int) -> list[dict]:
        """Resíduos do talhão: real vs. fitted regional sob o clima REAL de cada ano."""
        history: list[dict] = []
        for c in self.farms.list_cycles_by_field(field_id):
            if c.actual_yield_sc_ha is None:
                continue
            fitted = regional_fitted_sc_ha(self.model, municipality_code, c.season.harvest_year)
            if fitted <= 0:
                continue
            res = c.actual_yield_sc_ha - fitted
            history.append({
                "harvest_year": c.season.harvest_year,
                "actual_sc_ha": round(c.actual_yield_sc_ha, 1),
                "regional_fitted_sc_ha": round(fitted, 1),
                "residual_pct": round(100 * res / fitted, 1),
            })
        return history

    def manejo_history(self, field_id: int) -> dict:
        """Histórico manejo×resultado por safra: o que foi feito × o que rendeu.

        Para cada safra do talhão: o manejo registrado (ou o perfil atual como proxy),
        a expectativa daquele manejo sob o clima real do ano e a produtividade real.
        É a base do aprendizado por variável e a visão que o produtor pede.
        """
        field = self.farms.get_field(field_id)
        if field is None:
            raise FieldNotFound(field_id)
        farm = self.farms.get_farm(field.farm_id)
        current = self.profiles.get(field_id) or {}
        rows: list[dict] = []
        for c in self.farms.list_cycles_by_field(field_id):
            snapshot = self.profiles.get_cycle(c.id)
            manejo = snapshot if snapshot else current
            source = "safra" if snapshot else ("perfil atual (proxy)" if current else "—")
            adj = compute_adjustment(manejo) if manejo else None
            fitted = regional_fitted_sc_ha(self.model, farm.municipality_code, c.season.harvest_year)
            predicted = round(fitted * adj.multiplier, 1) if (adj and fitted > 0) else None
            actual = round(c.actual_yield_sc_ha, 1) if c.actual_yield_sc_ha else None
            delta_pct = (
                round(100 * (actual - predicted) / predicted, 1)
                if (actual is not None and predicted) else None
            )
            rows.append({
                "crop_cycle_id": c.id,
                "season": c.season.label,
                "harvest_year": c.season.harvest_year,
                "manejo_source": source,
                "manejo_effect_pct": adj.total_effect_pct if adj else 0.0,
                "n_factors": adj.n_factors if adj else 0,
                "predicted_sc_ha": predicted,
                "actual_sc_ha": actual,
                "delta_vs_predicted_pct": delta_pct,
            })
        return {
            "field_id": field_id,
            "field_name": field.name,
            "n_seasons": len(rows),
            "history": rows,
            "note": "Manejo por safra (snapshot) × resultado. Onde não há snapshot, usa "
                    "o perfil atual do talhão como aproximação.",
        }

    def learned_estimate(self, field_id: int, season: str) -> dict:
        field = self.farms.get_field(field_id)
        if field is None:
            raise FieldNotFound(field_id)
        farm = self.farms.get_farm(field.farm_id)
        harvest_year = Season.parse(season).harvest_year
        est = self.model.estimate(farm.municipality_code, harvest_year)
        scenarios = {s.name: s.yield_sc_ha for s in est.scenarios}

        # a priori — perfil agronômico vira o prior do encolhimento
        profile = self.profiles.get(field_id) or {}
        prior_bias = compute_adjustment(profile).multiplier - 1.0 if profile else 0.0

        # a posteriori — resíduos das colheitas do talhão
        history = self._residuals(field_id, farm.municipality_code)
        rel = [h["residual_pct"] / 100.0 for h in history]
        n = len(rel)
        observed_bias = statistics.fmean(rel) if rel else 0.0
        variance = statistics.variance(rel) if n >= 2 else 0.0

        pred = personalize(
            est.point_sc_ha, est.interval_sc_ha, scenarios,
            n, observed_bias, variance, self.prior, prior_bias=prior_bias,
        )
        return {
            "field_id": field_id,
            "field_name": field.name,
            "municipality_code": farm.municipality_code,
            "season": season,
            "harvest_year": harvest_year,
            "regional": {
                "point_sc_ha": pred.regional_point_sc_ha,
                "interval_sc_ha": list(pred.regional_interval_sc_ha),
            },
            "a_priori_profile_pct": pred.prior_bias_pct,
            "observed_from_harvests_pct": pred.observed_bias_pct,
            "applied_pct": pred.farm_adjustment_pct,
            "n_harvests": n,
            "confidence_score": pred.confidence_score,
            "adaptation_level": pred.adaptation_level,
            "learned": {
                "point_sc_ha": pred.personalized_point_sc_ha,
                "interval_sc_ha": list(pred.personalized_interval_sc_ha),
                "scenarios": [
                    {"name": k, "yield_sc_ha": v} for k, v in pred.scenarios_sc_ha.items()
                ],
            },
            "residual_history": history,
            "explanation": _explain(pred, n),
        }


def _explain(pred, n: int) -> str:
    if n == 0:
        return (
            f"Previsão parte do Perfil Agronômico ({pred.prior_bias_pct:+.1f}% vs região). "
            "Registre colheitas e o FADA vai aprendendo do dado real do seu talhão, "
            "convergindo da estimativa agronômica para a sua realidade."
        )
    return (
        f"O FADA partiu do perfil ({pred.prior_bias_pct:+.1f}%) e, com {n} colheita(s) "
        f"registrada(s) (observado {pred.observed_bias_pct:+.1f}% vs região), aplicou "
        f"{pred.farm_adjustment_pct:+.1f}% (confiança {pred.confidence_score:.0%}). "
        f"Previsão do talhão: {pred.personalized_point_sc_ha} sc/ha "
        f"(adaptação {pred.adaptation_level}; o intervalo não estreita artificialmente)."
    )
