"""Índices agroclimáticos.

Todas as funções operam sobre uma sequência de :class:`DailyWeather` e são puras
(sem I/O, sem estado global), portanto trivialmente testáveis e reprodutíveis.

Referências de método:
- GDD: soma térmica = média diária − temperatura base, truncada em zero, com teto
  opcional na temperatura média (método "horizontal cutoff").
- Veranico (dry spell): sequência de dias consecutivos com precipitação abaixo de
  um limiar.
- Déficit hídrico simplificado: balanço P − ETc acumulado, truncado em zero
  (proxy de estresse; um balanço completo entra na V2 com armazenamento de solo).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DailyWeather:
    """Registro climático diário.

    Args:
        day: data do registro.
        tmin: temperatura mínima (°C).
        tmax: temperatura máxima (°C).
        precipitation_mm: precipitação (mm).
        et0_mm: evapotranspiração de referência (mm), opcional.
    """

    day: date
    tmin: float
    tmax: float
    precipitation_mm: float
    et0_mm: float | None = None

    @property
    def tmean(self) -> float:
        return (self.tmin + self.tmax) / 2.0


@dataclass(frozen=True)
class DrySpellSummary:
    """Resumo de veranicos em um período."""

    count: int
    longest_days: int
    total_dry_days: int


def growing_degree_days(
    series: list[DailyWeather],
    base_temp: float,
    cap_temp: float | None = None,
) -> float:
    """Soma térmica acumulada (Growing Degree Days) no período.

    Args:
        series: série diária.
        base_temp: temperatura base da cultura (°C). Ex.: soja ≈ 10, milho ≈ 10.
        cap_temp: teto opcional para a temperatura média antes de subtrair a base.

    Returns:
        GDD acumulado (°C·dia), nunca negativo.
    """
    total = 0.0
    for d in series:
        tmean = d.tmean
        if cap_temp is not None and tmean > cap_temp:
            tmean = cap_temp
        total += max(0.0, tmean - base_temp)
    return total


def accumulated_rainfall(
    series: list[DailyWeather],
    start: date | None = None,
    end: date | None = None,
) -> float:
    """Precipitação acumulada (mm), opcionalmente restrita a [start, end].

    Útil para chuva na janela crítica (ex.: soja em R1–R5).
    """
    return sum(
        d.precipitation_mm
        for d in series
        if (start is None or d.day >= start) and (end is None or d.day <= end)
    )


def dry_spells(
    series: list[DailyWeather],
    threshold_mm: float = 1.0,
    min_length: int = 5,
) -> DrySpellSummary:
    """Identifica veranicos (sequências secas).

    Args:
        series: série diária (assume-se ordenada por data).
        threshold_mm: chuva abaixo da qual o dia é considerado "seco".
        min_length: duração mínima (dias) para a sequência contar como veranico.

    Returns:
        Resumo com contagem, maior duração e total de dias secos.
    """
    count = 0
    longest = 0
    total_dry = 0
    current = 0
    for d in series:
        if d.precipitation_mm < threshold_mm:
            current += 1
            total_dry += 1
        else:
            if current >= min_length:
                count += 1
                longest = max(longest, current)
            current = 0
    if current >= min_length:  # veranico aberto no fim da série
        count += 1
        longest = max(longest, current)
    return DrySpellSummary(count=count, longest_days=longest, total_dry_days=total_dry)


def simple_water_deficit(
    series: list[DailyWeather],
    crop_coefficient: float = 1.0,
) -> float:
    """Déficit hídrico simplificado: máx(0, Σ(ETc − P)).

    ETc = et0 × crop_coefficient. Requer ``et0_mm`` presente nos registros; dias sem
    et0 são ignorados. É um *proxy* de estresse hídrico para o MVP — o balanço
    completo com capacidade de água disponível no solo entra na V2.

    Returns:
        Déficit acumulado (mm), nunca negativo.
    """
    deficit = 0.0
    for d in series:
        if d.et0_mm is None:
            continue
        etc = d.et0_mm * crop_coefficient
        deficit += etc - d.precipitation_mm
    return max(0.0, deficit)
