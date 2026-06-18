"""Gera um exemplo de Field Intelligence + Insights (fazenda SINTÉTICA).

Demonstra rankings, estabilidade ajustada ao clima, tendência de custo e anomalia.
Dados sintéticos (clima real, produtividades fabricadas) — apenas ilustração.

Uso:  python -m pipelines.example_insights
"""

from __future__ import annotations

import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domain.farm import AgriculturalEvent, CropCycle, EventType, Farm, Field, Season
from app.domain.yield_estimation import RegionalYieldModel
from app.infra.db import Base
from app.infra.repositories import EventRepository, FarmRepository
from app.services.insights import InsightsService
from app.services.regional_fitted import regional_fitted_sc_ha

HORIZONTINA = 4309605
YEARS = range(2018, 2025)


def main() -> None:
    model = RegionalYieldModel.load(settings.model_path)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    farms, events = FarmRepository(session), EventRepository(session)

    farm = farms.add_farm(Farm(name="Fazenda Demo Talhões", municipality_code=HORIZONTINA))
    norte = farms.add_field(Field(farm_id=farm.id, name="Talhão Norte", area_ha=100))
    sul = farms.add_field(Field(farm_id=farm.id, name="Talhão Sul", area_ha=80))
    leste = farms.add_field(Field(farm_id=farm.id, name="Talhão Leste", area_ha=90))

    def fitted(y: int) -> float:
        return regional_fitted_sc_ha(model, HORIZONTINA, y)

    for i, year in enumerate(YEARS):
        f = fitted(year)
        # Norte: +10% estável; anomalia em 2024 (queda); custo/ha crescente.
        norte_y = round(f * 1.10 + (0.5 if i % 2 else -0.5), 1)
        if year == 2024:
            norte_y = round(f * 0.80, 1)  # anomalia
        _cycle(farms, events, norte.id, year, 100, norte_y,
               cost=90000 + i * 12000)  # custo crescente
        # Sul: -8% (pior), custo estável.
        _cycle(farms, events, sul.id, year, 80, round(f * 0.92, 1), cost=120000)
        # Leste: média, porém instável (alterna ±15%).
        leste_y = round(f * (1.15 if i % 2 else 0.85), 1)
        _cycle(farms, events, leste.id, year, 90, leste_y, cost=110000)

    svc = InsightsService(farms=farms, events=events, model=model)
    analytics = svc.field_analytics(farm.id)
    insights = svc.insights(farm.id)

    out = {
        "_note": "Fazenda SINTÉTICA (clima real, produtividades fabricadas) p/ demonstração.",
        "field_analytics": analytics,
        "insights": insights,
    }
    path = settings.data_dir.parent / "examples" / "insights_demo.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Talhões: {analytics['n_fields']} | registros: {analytics['n_records']}")
    for s in analytics["fields"]:
        print(f"  {s['field_name']:14s} bias {s['bias_vs_region_pct']:+5.1f}% "
              f"estab {s['yield_stability_std_pct']}% custo/ha {s['mean_cost_per_ha']}")
    print(f"\nInsights ({insights['n_insights']}):")
    for i in insights["insights"]:
        print(f"  [{i['confidence']}] {i['detail']}")
    print(f"-> {path}")


def _cycle(farms, events, field_id, year, area, actual, cost):
    c = farms.add_cycle(CropCycle(
        field_id=field_id, crop="soja", season=Season.parse(f"{year - 1}/{str(year)[2:]}"),
        area_ha=area, actual_yield_sc_ha=actual,
    ))
    events.add_event(AgriculturalEvent(
        crop_cycle_id=c.id, event_type=EventType.BASE_FERTILIZATION,
        event_date=date(year - 1, 11, 1), cost=cost,
    ))
    events.add_event(AgriculturalEvent(
        crop_cycle_id=c.id, event_type=EventType.HERBICIDE,
        event_date=date(year - 1, 11, 20), cost=cost * 0.15,
    ))


if __name__ == "__main__":
    main()
