"""Caso de uso de apoio à decisão: atenção por flags + ranking multi-critério.

Compõe Field Intelligence (histórico), Budget (plano x realizado) e o modelo
regional (expectativa). Determinístico, explicável — aponta ONDE olhar, não O QUE
fazer (ADR-0016).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.cost import calculate_total_cost
from app.domain.decisions import FieldDecisionInput, evaluate, rankings
from app.domain.planning import build_agenda
from app.domain.yield_estimation import RegionalYieldModel
from app.infra.repositories import EventRepository, FarmRepository, PlanningRepository
from app.services.insights import InsightsService


class FarmNotFound(Exception):
    pass


@dataclass
class DecisionsService:
    farms: FarmRepository
    events: EventRepository
    planning: PlanningRepository
    model: RegionalYieldModel
    insights: InsightsService

    def _expected_yield(self, municipality_code: int, harvest_year: int) -> float | None:
        try:
            return self.model.estimate(municipality_code, harvest_year).point_sc_ha
        except KeyError:
            return None

    def _gather(self, farm_id: int) -> tuple[list[FieldDecisionInput], str | None]:
        farm = self.farms.get_farm(farm_id)
        if farm is None:
            raise FarmNotFound(farm_id)
        cycles = self.farms.list_cycles_by_farm(farm_id)
        if not cycles:
            return [], None
        target_year = max(c.season.harvest_year for c in cycles)
        season_label = next(c.season.label for c in cycles if c.season.harvest_year == target_year)
        fields = {f.id: f for f in self.farms.list_fields(farm_id)}
        history = {s["field_id"]: s for s in self.insights.field_analytics(farm_id)["fields"]}
        expected = self._expected_yield(farm.municipality_code, target_year)

        out: list[FieldDecisionInput] = []
        for c in cycles:
            if c.season.harvest_year != target_year:
                continue
            fld = fields.get(c.field_id)
            area = c.area_ha or (fld.area_ha if fld else None)
            actual_events = self.events.list_by_cycle(c.id)
            planned_events = self.planning.list_by_cycle(c.id)
            actual_total = calculate_total_cost(actual_events) if actual_events else None
            planned_total = (round(sum(p.expected_cost or 0.0 for p in planned_events), 2)
                             if planned_events else None)
            pct = (round(100 * actual_total / planned_total, 1)
                   if actual_total is not None and planned_total else None)
            pending = sum(1 for i in build_agenda(planned_events, actual_events, date.today())
                          if i.status != "concluída")
            hist = history.get(c.field_id, {})
            out.append(FieldDecisionInput(
                field_id=c.field_id,
                field_name=fld.name if fld else f"Talhão {c.field_id}",
                area_ha=area,
                target_yield_sc_ha=c.target_yield_sc_ha,
                expected_yield_sc_ha=c.actual_yield_sc_ha or expected,
                actual_total_cost=actual_total,
                actual_cost_per_ha=(round(actual_total / area, 2)
                                    if actual_total is not None and area else None),
                planned_total_cost=planned_total,
                pct_budget_consumed=pct,
                over_budget=bool(actual_total and planned_total and actual_total > planned_total),
                has_pending_planned=pending > 0,
                n_seasons=hist.get("n_seasons", 0),
                bias_vs_region_pct=hist.get("bias_vs_region_pct"),
                stability_std_pct=hist.get("yield_stability_std_pct"),
            ))
        return out, season_label

    def decisions(self, farm_id: int) -> dict:
        fields, season = self._gather(farm_id)
        attentions = evaluate(fields)
        return {
            "farm_id": farm_id,
            "season": season,
            "n_fields": len(fields),
            "fields": [
                {
                    "field_id": a.field_id, "field_name": a.field_name,
                    "attention_level": a.attention_level,
                    "flags": [
                        {"code": fl.code, "severity": fl.severity, "title": fl.title,
                         "detail": fl.detail, "confidence": fl.confidence,
                         "evidence": fl.evidence}
                        for fl in a.flags
                    ],
                }
                for a in attentions
            ],
            "rankings": rankings(fields),
            "note": (
                "Atenção por alertas nomeados e auditáveis (sem score único). FADA aponta "
                "onde olhar; não prescreve manejo agronômico."
            ),
        }
