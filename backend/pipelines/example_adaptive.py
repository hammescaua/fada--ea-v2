"""Gera um exemplo de Adaptive Farm Intelligence em examples/ (fazenda SINTÉTICA).

Demonstra a recuperação do bias da fazenda e a personalização com incerteza
preservada. Os rendimentos são sintéticos (fazenda +12% sobre o regional), apenas
para ilustração — não são dados reais.

Uso:  python -m pipelines.example_adaptive
"""

from __future__ import annotations

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domain.units import kg_per_ha_to_bags_per_ha
from app.domain.yield_estimation import RegionalYieldModel
from app.infra.db import Base
from app.infra.repositories import AdaptiveRepository, FarmRepository
from app.services.adaptive import AdaptiveService, _features_lookup
from app.domain.farm import CropCycle, Farm, Field, Season

TRUE_BIAS = 0.12  # fazenda 12% acima do regional (sintético)
HORIZONTINA = 4309605


def main() -> None:
    model = RegionalYieldModel.load(settings.model_path)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    farms = FarmRepository(session)
    svc = AdaptiveService(farms=farms, adaptive=AdaptiveRepository(session), model=model)

    farm = farms.add_farm(Farm(name="Fazenda Demo (+12%)", municipality_code=HORIZONTINA))
    field = farms.add_field(Field(farm_id=farm.id, name="Talhão 1", area_ha=100))

    lk = _features_lookup()
    for i, year in enumerate(range(2015, 2025)):
        feats = lk[(HORIZONTINA, year)]
        fitted = kg_per_ha_to_bags_per_ha(model.predict_kg_ha({**feats, "harvest_year": year}))
        actual = round(fitted * (1 + TRUE_BIAS) + (1 if i % 2 else -1) * 0.8, 1)
        farms.add_cycle(CropCycle(
            field_id=field.id, crop="soja", season=Season.parse(f"{year - 1}/{str(year)[2:]}"),
            area_ha=100, actual_yield_sc_ha=actual,
        ))

    profile = svc.recompute_profile(farm.id)
    personalized = svc.personalized_intelligence(farm.id, "2026/27")

    out = {
        "_note": "Rendimentos SINTÉTICOS (fazenda +12%) apenas para demonstração.",
        "profile": {
            "number_of_cycles": profile.number_of_cycles,
            "observed_bias_percentage": profile.bias_percentage,
            "variance_relative": round(profile.variance_relative, 4),
        },
        "residual_history": svc.residual_history(farm.id),
        "personalized_intelligence": personalized,
    }
    path = settings.data_dir.parent / "examples" / "adaptive_farm_demo.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Bias observado: {profile.bias_percentage}% (real +12%) | "
          f"n={profile.number_of_cycles}")
    print(f"Regional {personalized['regional_prediction']['point_sc_ha']} -> "
          f"Personalizado {personalized['personalized_prediction']['point_sc_ha']} sc/ha "
          f"(ajuste {personalized['farm_adjustment']['applied_pct']:+}%, "
          f"confiança {personalized['confidence_score']:.0%})")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
