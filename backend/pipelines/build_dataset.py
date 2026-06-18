"""Constrói o dataset de features (raw -> intermediate -> features).

Para cada município da microrregião Três Passos:
  1. obtém o ground truth de rendimento (IBGE/PAM);
  2. obtém o centroide (IBGE malhas);
  3. baixa a série climática diária (Open-Meteo/ERA5) cobrindo todas as safras;
  4. calcula as features agroclimáticas por safra (domínio puro).

Saída: ``data/features/soybean_tres_passos.csv`` (versionado).

Uso:  python -m pipelines.build_dataset
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from app.core.config import settings
from app.data.connectors import IbgeConnector, NasaPowerConnector, OpenMeteoConnector
from app.domain.climate import DailyWeather
from app.domain.crop import SOYBEAN_RS
from app.domain.features import SOYBEAN_FEATURE_NAMES, build_soybean_features
from pipelines.region import (
    FIRST_HARVEST_YEAR,
    LAST_HARVEST_YEAR,
    MICROREGION_TRES_PASSOS,
)


def _fetch_weather(
    primary: OpenMeteoConnector,
    fallback: NasaPowerConnector,
    lat: float,
    lon: float,
    start: date,
    end: date,
) -> tuple[list[DailyWeather], str]:
    """Open-Meteo (1940+) como primária; NASA POWER (1981+) como fallback."""
    try:
        return primary.daily_weather(lat, lon, start, end), "open-meteo"
    except Exception:  # noqa: BLE001 — fonte interchangeável; tenta a secundária
        nasa_start = max(start, date(1981, 1, 1))
        return fallback.daily_weather(lat, lon, nasa_start, end), "nasa-power"


def build() -> pd.DataFrame:
    ibge = IbgeConnector()
    meteo = OpenMeteoConnector()
    nasa = NasaPowerConnector()

    municipalities = ibge.microregion_municipalities(MICROREGION_TRES_PASSOS)
    print(f"Municípios na microrregião: {len(municipalities)}")

    # Janela climática que cobre todas as safras (out do ano anterior -> mar).
    weather_start = date(FIRST_HARVEST_YEAR - 1, 9, 1)
    weather_end = date(LAST_HARVEST_YEAR, 4, 30)

    rows: list[dict] = []
    for code, name in municipalities:
        try:
            lat, lon = ibge.municipality_centroid(code)
            yields = ibge.soybean_yield_kg_ha(code)
            series, src = _fetch_weather(meteo, nasa, lat, lon, weather_start, weather_end)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {name} ({code}) ignorado: {type(exc).__name__}")
            continue

        n_added = 0
        for year in range(FIRST_HARVEST_YEAR, LAST_HARVEST_YEAR + 1):
            if year not in yields:
                continue
            feats = build_soybean_features(series, lat, year, SOYBEAN_RS)
            rows.append(
                {
                    "municipality_code": code,
                    "municipality_name": name,
                    "harvest_year": year,
                    "latitude": lat,
                    "longitude": lon,
                    **feats,
                    "yield_kg_ha": yields[year],
                }
            )
            n_added += 1
        print(f"  ✓ {name}: {n_added} safras [{src}]")

    df = pd.DataFrame(rows)
    out = settings.data_dir / "features" / "soybean_tres_passos.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nDataset: {len(df)} linhas -> {out}")
    print(df[["harvest_year", *SOYBEAN_FEATURE_NAMES, "yield_kg_ha"]].describe().round(1))
    return df


if __name__ == "__main__":
    build()
