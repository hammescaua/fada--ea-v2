"""Casos de uso de Field Intelligence (descritivo) e do Insight Engine.

Coleta apenas DADO REAL registrado (talhões, safras com produtividade, eventos de
custo), computa a expectativa regional ajustada ao clima e deriva sumários e
insights determinísticos. Sem cultivar, sem shrinkage por talhão (ADR-0014).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.cost import calculate_total_cost, count_applications
from app.domain.insights import (
    FieldSeasonRecord,
    FieldSummary,
    build_field_summary,
    generate_insights,
)
from app.domain.yield_estimation import RegionalYieldModel
from app.infra.repositories import EventRepository, FarmRepository
from app.services.regional_fitted import regional_fitted_sc_ha


class FarmNotFound(Exception):
    pass


@dataclass
class InsightsService:
    farms: FarmRepository
    events: EventRepository
    model: RegionalYieldModel

    def _gather(self, farm_id: int) -> tuple[list[FieldSummary], dict[int, list[FieldSeasonRecord]]]:
        farm = self.farms.get_farm(farm_id)
        if farm is None:
            raise FarmNotFound(farm_id)
        fields = {f.id: f for f in self.farms.list_fields(farm_id)}
        records_by_field: dict[int, list[FieldSeasonRecord]] = {}

        for cycle in self.farms.list_cycles_by_farm(farm_id):
            if cycle.actual_yield_sc_ha is None:
                continue
            fld = fields.get(cycle.field_id)
            area = cycle.area_ha or (fld.area_ha if fld else None)
            if not area or area <= 0:
                continue
            year = cycle.season.harvest_year
            fitted = regional_fitted_sc_ha(self.model, farm.municipality_code, year)
            if fitted <= 0:
                continue
            cycle_events = self.events.list_by_cycle(cycle.id)
            cost_total = calculate_total_cost(cycle_events) if cycle_events else None
            record = FieldSeasonRecord(
                field_id=cycle.field_id,
                field_name=fld.name if fld else f"Talhão {cycle.field_id}",
                harvest_year=year, area_ha=area,
                actual_sc_ha=cycle.actual_yield_sc_ha, regional_fitted_sc_ha=fitted,
                cost_total=cost_total, n_applications=count_applications(cycle_events),
            )
            records_by_field.setdefault(cycle.field_id, []).append(record)

        summaries = [build_field_summary(recs) for recs in records_by_field.values()]
        summaries.sort(key=lambda s: s.mean_rel_residual, reverse=True)
        return summaries, records_by_field

    def field_analytics(self, farm_id: int) -> dict:
        summaries, records = self._gather(farm_id)
        return {
            "farm_id": farm_id,
            "n_fields": len(summaries),
            "n_records": sum(len(r) for r in records.values()),
            "fields": [_summary_dict(s) for s in summaries],
        }

    def insights(self, farm_id: int) -> dict:
        summaries, records = self._gather(farm_id)
        items = generate_insights(summaries, records)
        return {
            "farm_id": farm_id,
            "n_insights": len(items),
            "insights": [
                {
                    "type": i.type, "scope": i.scope, "field_id": i.field_id,
                    "title": i.title, "detail": i.detail, "evidence": i.evidence,
                    "confidence": i.confidence,
                }
                for i in items
            ],
            "note": (
                "Insights determinísticos a partir de dado real registrado, com N e "
                "tamanho de efeito. Sem cultivar (confundimento) e sem personalização "
                "por talhão (dados insuficientes) nesta fase."
            ),
        }


def _summary_dict(s: FieldSummary) -> dict:
    return {
        "field_id": s.field_id, "field_name": s.field_name, "n_seasons": s.n_seasons,
        "mean_actual_sc_ha": s.mean_actual_sc_ha, "bias_vs_region_pct": s.bias_percentage,
        "yield_stability_std_pct": (
            round(100 * s.yield_stability_std, 1) if s.yield_stability_std is not None else None
        ),
        "mean_cost_per_ha": s.mean_cost_per_ha, "n_seasons_with_cost": s.n_seasons_with_cost,
        "latest_year": s.latest_year, "latest_actual_sc_ha": s.latest_actual_sc_ha,
        "cost_trend": s.cost_trend,
    }
