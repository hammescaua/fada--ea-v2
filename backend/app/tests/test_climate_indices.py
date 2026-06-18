from datetime import date, timedelta

from app.domain.climate import (
    DailyWeather,
    accumulated_rainfall,
    dry_spells,
    growing_degree_days,
    simple_water_deficit,
)


def _series(values):
    """values: lista de (tmin, tmax, precip, et0) começando em 2026-11-01."""
    start = date(2026, 11, 1)
    return [
        DailyWeather(start + timedelta(days=i), tmin, tmax, p, et0)
        for i, (tmin, tmax, p, et0) in enumerate(values)
    ]


def test_gdd_basic():
    # tmean = 25, base 10 -> 15 GDD/dia, 2 dias -> 30
    s = _series([(20, 30, 0, None), (20, 30, 0, None)])
    assert growing_degree_days(s, base_temp=10) == 30.0


def test_gdd_never_negative():
    # tmean = 5, base 10 -> 0
    s = _series([(0, 10, 0, None)])
    assert growing_degree_days(s, base_temp=10) == 0.0


def test_gdd_cap():
    # tmean = 35 capado em 30, base 10 -> 20
    s = _series([(30, 40, 0, None)])
    assert growing_degree_days(s, base_temp=10, cap_temp=30) == 20.0


def test_accumulated_rainfall_window():
    s = _series([(20, 30, 10, None), (20, 30, 5, None), (20, 30, 20, None)])
    assert accumulated_rainfall(s) == 35.0
    assert accumulated_rainfall(s, start=date(2026, 11, 2)) == 25.0


def test_dry_spell_detected():
    # 6 dias secos seguidos -> 1 veranico de 6 dias
    s = _series([(20, 30, 0, None)] * 6 + [(20, 30, 10, None)])
    summary = dry_spells(s, threshold_mm=1.0, min_length=5)
    assert summary.count == 1
    assert summary.longest_days == 6
    assert summary.total_dry_days == 6


def test_dry_spell_below_min_length_ignored():
    s = _series([(20, 30, 0, None)] * 3 + [(20, 30, 10, None)])
    summary = dry_spells(s, min_length=5)
    assert summary.count == 0


def test_water_deficit():
    # ETc(=et0*1) - P: (5-0)+(5-2) = 8
    s = _series([(20, 30, 0, 5.0), (20, 30, 2, 5.0)])
    assert simple_water_deficit(s) == 8.0


def test_water_deficit_floored_at_zero():
    # chuva supera demanda -> déficit 0
    s = _series([(20, 30, 50, 5.0)])
    assert simple_water_deficit(s) == 0.0
