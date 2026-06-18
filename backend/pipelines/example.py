"""Gera exemplos reais do endpoint e salva em ``examples/`` (versionado).

Uso:  python -m pipelines.example
"""

from __future__ import annotations

import json

from app.core.config import settings
from app.domain.yield_estimation import RegionalYieldModel
from app.engine.explainer import TemplateExplainer
from app.services.regional_intelligence import RegionalIntelligenceService

EXAMPLES = [
    ("Horizontina", "soja", "2026/27"),
    ("Três Passos", "soja", "2026/27"),
    ("Crissiumal", "soja", "2026/27"),
]


def main() -> None:
    model = RegionalYieldModel.load(settings.model_path)
    service = RegionalIntelligenceService(model=model, explainer=TemplateExplainer())
    out_dir = settings.data_dir.parent / "examples"
    out_dir.mkdir(exist_ok=True)

    for municipality, crop, season in EXAMPLES:
        result = service.run(municipality=municipality, crop=crop, season=season)
        slug = municipality.lower().replace(" ", "_").replace("ê", "e").replace("ã", "a")
        path = out_dir / f"{slug}_{crop}_{season.replace('/', '_')}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(
            f"{municipality:14s} normal={result['estimated_yield_sc_ha']:.1f} sc/ha "
            f"IC={result['confidence_interval_sc_ha']} -> {path.name}"
        )


if __name__ == "__main__":
    main()
