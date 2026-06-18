"""Pré-computa o grid de features por data de plantio (offline, pesado).

Para cada município × data-grid de plantio × ano histórico, recoloca a janela
reprodutiva pela fenologia GDD e calcula as 4 features. O runtime apenas lê esta
tabela e roda a inferência (leve). Saída versionada em data/features.

Uso:  python -m pipelines.build_planting_grid
"""

from __future__ import annotations

from datetime import date, timedelta

import mlflow
import pandas as pd

from app.core.config import settings
from app.data.connectors import IbgeConnector
from app.domain.features import build_soybean_features_for_windows
from app.domain.planting_date import SOYBEAN_PHENOLOGY_RS
from pipelines.build_dataset import _fetch_weather
from pipelines.region import (
    FIRST_HARVEST_YEAR,
    LAST_HARVEST_YEAR,
    MICROREGION_TRES_PASSOS,
)

# Datas-grid de plantio (mês, dia), passo de 5 dias cobrindo ZARC + buffer.
GRID_STEP_DAYS = 5
GRID_START = (10, 1)
GRID_END = (12, 20)


def _grid_dates(ref_prev_year: int) -> list[date]:
    start = date(ref_prev_year, *GRID_START)
    end = date(ref_prev_year, *GRID_END)
    out, d = [], start
    while d <= end:
        out.append(d)
        d += timedelta(days=GRID_STEP_DAYS)
    return out


def build() -> pd.DataFrame:
    from app.data.connectors import NasaPowerConnector, OpenMeteoConnector

    ibge = IbgeConnector()
    meteo, nasa = OpenMeteoConnector(), NasaPowerConnector()
    phen = SOYBEAN_PHENOLOGY_RS

    municipalities = ibge.microregion_municipalities(MICROREGION_TRES_PASSOS)
    w_start = date(FIRST_HARVEST_YEAR - 1, 9, 1)
    w_end = date(LAST_HARVEST_YEAR, 5, 31)

    rows: list[dict] = []
    for code, name in municipalities:
        try:
            lat, lon = ibge.municipality_centroid(code)
            series, _ = _fetch_weather(meteo, nasa, lat, lon, w_start, w_end)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {name} ignorado: {type(exc).__name__}")
            continue

        for harvest_year in range(FIRST_HARVEST_YEAR, LAST_HARVEST_YEAR + 1):
            for plant in _grid_dates(harvest_year - 1):
                stages = phen.stages(series, plant)
                r1, r6 = stages.reproductive_window
                season_window = (plant, min(r6 + timedelta(days=21), w_end))
                feats = build_soybean_features_for_windows(series, lat, season_window, (r1, r6))
                rows.append(
                    {
                        "municipality_code": code,
                        "municipality_name": name,
                        "harvest_year": harvest_year,
                        "planting_mmdd": plant.strftime("%m-%d"),
                        "r1_offset_days": (r1 - plant).days,
                        "r6_offset_days": (r6 - plant).days,
                        **feats,
                    }
                )
        print(f"  ✓ {name}")

    df = pd.DataFrame(rows)
    out = settings.data_dir / "features" / "soybean_planting_grid_tres_passos.csv"
    df.to_csv(out, index=False)

    mlflow.set_tracking_uri(f"sqlite:///{settings.data_dir.parent / 'mlflow.db'}")
    mlflow.set_experiment("planting_date_grid")
    with mlflow.start_run(run_name="build_grid"):
        mlflow.log_params({
            "grid_step_days": GRID_STEP_DAYS,
            "grid_start": f"{GRID_START[0]}-{GRID_START[1]}",
            "grid_end": f"{GRID_END[0]}-{GRID_END[1]}",
            "gdd_r1": phen.gdd_r1,
            "gdd_r6": phen.gdd_r6,
        })
        mlflow.log_metrics({
            "n_rows": len(df),
            "n_municipalities": df["municipality_code"].nunique(),
            "n_grid_dates": df["planting_mmdd"].nunique(),
        })

    print(f"\nGrid: {len(df)} linhas, {df['planting_mmdd'].nunique()} datas -> {out}")
    return df


if __name__ == "__main__":
    build()
