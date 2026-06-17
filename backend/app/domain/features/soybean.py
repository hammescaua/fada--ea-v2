"""Features agroclimáticas para soja.

As features são calculadas em janelas fenológicas (ver :mod:`app.domain.crop`). A
escolha é justificada no ADR-0004; em resumo, priorizamos estresse hídrico e
térmico no período reprodutivo — o principal driver de variância de produtividade
de soja de sequeiro no RS.
"""

from __future__ import annotations

from app.domain.climate import (
    DailyWeather,
    accumulated_rainfall,
    days_above,
    dry_spells,
    simple_water_deficit,
    with_hargreaves_et0,
)
from app.domain.crop import CropCalendar

# Coeficiente de cultura (Kc) médio da soja no período reprodutivo (FAO-56 mid-season).
SOYBEAN_KC_REPRODUCTIVE = 1.15

# Ordem canônica das features do modelo (sem o termo de tendência 'harvest_year',
# que é adicionado no nível do dataset).
SOYBEAN_FEATURE_NAMES = [
    "water_deficit_reproductive_mm",
    "dry_spell_longest_reproductive_days",
    "hot_days_reproductive",
    "precip_total_season_mm",
]


def _slice(series: list[DailyWeather], window: tuple) -> list[DailyWeather]:
    start, end = window
    return [d for d in series if start <= d.day <= end]


def build_soybean_features_for_windows(
    series: list[DailyWeather],
    latitude_deg: float,
    season_window: tuple,
    reproductive_window: tuple,
) -> dict[str, float]:
    """Constrói as features dadas janelas explícitas (season e reprodutiva).

    Usado tanto pelo calendário fixo quanto pela fenologia dirigida por data de
    plantio (GDD), garantindo que as duas vias calculem features de forma idêntica.
    """
    season = _slice(series, season_window)
    season = with_hargreaves_et0(season, latitude_deg)
    reproductive = _slice(season, reproductive_window)

    longest_dry = dry_spells(reproductive, threshold_mm=1.0, min_length=1).longest_days

    return {
        "water_deficit_reproductive_mm": simple_water_deficit(
            reproductive, crop_coefficient=SOYBEAN_KC_REPRODUCTIVE
        ),
        "dry_spell_longest_reproductive_days": float(longest_dry),
        "hot_days_reproductive": float(days_above(reproductive, tmax_threshold=35.0)),
        "precip_total_season_mm": accumulated_rainfall(season),
    }


def build_soybean_features(
    series: list[DailyWeather],
    latitude_deg: float,
    harvest_year: int,
    calendar: CropCalendar,
) -> dict[str, float]:
    """Constrói o vetor de features para um município/safra (janela do calendário).

    Args:
        series: série diária cobrindo ao menos a janela da safra.
        latitude_deg: latitude do município (para ET0 de Hargreaves).
        harvest_year: ano de colheita (ex.: 2027 para a safra 2026/27).
        calendar: calendário fenológico da cultura.

    Returns:
        Dicionário {feature: valor} na ordem de :data:`SOYBEAN_FEATURE_NAMES`.
    """
    windows = calendar.windows_for(harvest_year)
    return build_soybean_features_for_windows(
        series, latitude_deg, windows.season, windows.reproductive
    )
