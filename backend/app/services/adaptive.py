"""Caso de uso de Adaptive Farm Intelligence.

Coleta os resíduos da fazenda (produtividade real vs. expectativa regional sob o
clima REAL de cada ano — ADR-0012), materializa o FarmPerformanceProfile e aplica
o encolhimento para personalizar uma predição regional, preservando a incerteza.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.adaptive import (
    FarmPerformanceProfile,
    ShrinkagePrior,
    compute_profile_stats,
    personalize,
)
from app.domain.farm import Season
from app.domain.yield_estimation import RegionalYieldModel
from app.infra.repositories import AdaptiveRepository, FarmRepository
from app.services.regional_fitted import features_lookup, regional_fitted_sc_ha

# Alias retrocompatível (usado por pipelines/example_adaptive).
_features_lookup = features_lookup


class FarmNotFound(Exception):
    pass


@dataclass
class AdaptiveService:
    farms: FarmRepository
    adaptive: AdaptiveRepository
    model: RegionalYieldModel
    prior: ShrinkagePrior = ShrinkagePrior()

    def _fitted_sc_ha(self, municipality_code: int, harvest_year: int) -> float:
        """Expectativa regional sob o clima REAL do ano (compartilhada — ver regional_fitted)."""
        return regional_fitted_sc_ha(self.model, municipality_code, harvest_year)

    def residual_history(self, farm_id: int) -> list[dict]:
        farm = self.farms.get_farm(farm_id)
        if farm is None:
            raise FarmNotFound(farm_id)
        history = []
        for c in self.farms.list_cycles_by_farm(farm_id):
            if c.actual_yield_sc_ha is None:
                continue
            fitted = self._fitted_sc_ha(farm.municipality_code, c.season.harvest_year)
            if fitted <= 0:
                continue
            residual = c.actual_yield_sc_ha - fitted
            history.append({
                "harvest_year": c.season.harvest_year,
                "actual_sc_ha": round(c.actual_yield_sc_ha, 1),
                "regional_fitted_sc_ha": round(fitted, 1),
                "residual_sc_ha": round(residual, 1),
                "residual_pct": round(100 * residual / fitted, 1),
            })
        return history

    def recompute_profile(self, farm_id: int) -> FarmPerformanceProfile:
        history = self.residual_history(farm_id)
        rel = [h["residual_pct"] / 100.0 for h in history]
        absr = [h["residual_sc_ha"] for h in history]
        stats = compute_profile_stats(rel, absr)
        profile = FarmPerformanceProfile(
            farm_id=farm_id,
            number_of_cycles=stats.n,
            mean_relative_residual=stats.mean_relative_residual,
            mean_residual_sc_ha=stats.mean_residual_sc_ha,
            median_residual_sc_ha=stats.median_residual_sc_ha,
            variance_relative=stats.variance_relative,
        )
        return self.adaptive.upsert_profile(profile)

    def personalized_intelligence(self, farm_id: int, season: str) -> dict:
        farm = self.farms.get_farm(farm_id)
        if farm is None:
            raise FarmNotFound(farm_id)
        harvest_year = Season.parse(season).harvest_year
        est = self.model.estimate(farm.municipality_code, harvest_year)
        scenarios = {s.name: s.yield_sc_ha for s in est.scenarios}

        profile = self.adaptive.get_profile(farm_id)
        n = profile.number_of_cycles if profile else 0
        observed_bias = profile.mean_relative_residual if profile else 0.0
        variance = profile.variance_relative if profile else 0.0

        pred = personalize(
            est.point_sc_ha, est.interval_sc_ha, scenarios,
            n, observed_bias, variance, self.prior,
        )
        return {
            "farm_id": farm_id,
            "municipality_code": farm.municipality_code,
            "season": season,
            "harvest_year": harvest_year,
            "regional_prediction": {
                "point_sc_ha": pred.regional_point_sc_ha,
                "interval_sc_ha": list(pred.regional_interval_sc_ha),
            },
            "farm_adjustment": {
                "applied_pct": pred.farm_adjustment_pct,
                "observed_bias_pct": pred.observed_bias_pct,
                "n_cycles": pred.n_cycles,
            },
            "personalized_prediction": {
                "point_sc_ha": pred.personalized_point_sc_ha,
                "interval_sc_ha": list(pred.personalized_interval_sc_ha),
                "scenarios": [
                    {"name": k, "yield_sc_ha": v} for k, v in pred.scenarios_sc_ha.items()
                ],
            },
            "confidence_score": pred.confidence_score,
            "adaptation_level": pred.adaptation_level,
            "explanation": _explain(pred),
        }


def _explain(pred) -> str:
    if pred.n_cycles == 0:
        return (
            "Ainda não há safras reais registradas nesta fazenda — a previsão é "
            "puramente regional. Registre colheitas para o FADA aprender o perfil da área."
        )
    direction = "acima" if pred.farm_adjustment_pct >= 0 else "abaixo"
    return (
        f"Com {pred.n_cycles} safra(s) registrada(s), o FADA estima que esta fazenda "
        f"produz cerca de {abs(pred.observed_bias_pct):.1f}% {direction} da média regional. "
        f"Aplicando confiança de {pred.confidence_score:.0%} (encolhimento), a correção "
        f"efetiva é {pred.farm_adjustment_pct:+.1f}%, levando a previsão de "
        f"{pred.regional_point_sc_ha} para {pred.personalized_point_sc_ha} sc/ha. O "
        f"intervalo não estreita artificialmente: a incerteza climática do ano é "
        f"irredutível (adaptação: {pred.adaptation_level})."
    )
