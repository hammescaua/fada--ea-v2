"""Gera exemplos reais de What-If de data de plantio e registra no MLflow.

- Exemplos em examples/ (simulação + otimização para Horizontina 2026/27).
- Validação no MLflow: reconciliação com o endpoint regional + sensibilidade por
  data (esperado, downside, score).

Uso:  python -m pipelines.example_planting
"""

from __future__ import annotations

import json

import mlflow

from app.core.config import settings
from app.domain.yield_estimation import RegionalYieldModel
from app.services.planting_date import PlantingDateService, load_grid
from app.services.regional_intelligence import parse_harvest_year

HORIZONTINA = "Horizontina"
SEASON = "2026/27"


def main() -> None:
    model = RegionalYieldModel.load(settings.model_path)
    grid = load_grid()
    service = PlantingDateService(model=model, grid=grid)
    out_dir = settings.data_dir.parent / "examples"
    out_dir.mkdir(exist_ok=True)

    sim = service.simulate(HORIZONTINA, "soja", SEASON, "2026-11-01")
    opt = service.optimize(HORIZONTINA, "soja", SEASON)
    (out_dir / "horizontina_planting_simulation_2026_27.json").write_text(
        json.dumps(sim, ensure_ascii=False, indent=2)
    )
    (out_dir / "horizontina_planting_optimization_2026_27.json").write_text(
        json.dumps(opt, ensure_ascii=False, indent=2)
    )

    # Validação: reconciliação com o endpoint regional (mesma safra, mesmo município).
    harvest_year = parse_harvest_year(SEASON)
    code = sim["municipality_code"]
    regional = model.estimate(code, harvest_year).point_sc_ha
    baseline = opt["baseline_expected_sc_ha"]

    mlflow.set_tracking_uri(f"sqlite:///{settings.data_dir.parent / 'mlflow.db'}")
    mlflow.set_experiment("planting_date_optimization")
    with mlflow.start_run(run_name="horizontina_2026_27"):
        mlflow.log_params({"municipality": HORIZONTINA, "season": SEASON, "harvest_year": harvest_year})
        mlflow.log_metrics({
            "regional_point_sc_ha": regional,
            "planting_baseline_sc_ha": baseline,
            "reconciliation_delta_sc_ha": round(baseline - regional, 2),
        })
        # Sensibilidade: varre todas as datas-grid (passo de aversão neutro).
        full = service.optimize(HORIZONTINA, "soja", SEASON, risk_aversion=0.5, top_n=99)
        for rank, rec in enumerate(full["top_recommendations"], 1):
            tag = rec["planting_date"].replace("/", "")
            mlflow.log_metrics({
                f"score_{tag}": rec["risk_score"],
                f"expected_{tag}": rec["expected_yield_sc_ha"],
                f"downside_{tag}": rec["downside_sc_ha"],
            }, step=rank)

    print(f"Reconciliação: regional={regional:.1f} | planting-base={baseline:.1f} "
          f"(Δ={baseline - regional:+.1f} sc/ha)")
    print("Top 3 datas robustas:")
    for rec in opt["top_recommendations"][:3]:
        print(f"  {rec['planting_date']}: esperado {rec['expected_yield_sc_ha']} "
              f"piso {rec['downside_sc_ha']} score {rec['risk_score']}")


if __name__ == "__main__":
    main()
