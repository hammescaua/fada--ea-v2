from datetime import date, timedelta

from app.domain.climate import DailyWeather, hargreaves_et0
from app.domain.crop import SOYBEAN_RS
from app.domain.features import SOYBEAN_FEATURE_NAMES, build_soybean_features


def _season_series(harvest_year: int, daily_precip: float, tmin=20.0, tmax=30.0):
    start = date(harvest_year - 1, 10, 1)
    end = date(harvest_year, 3, 31)
    days = (end - start).days + 1
    return [
        DailyWeather(start + timedelta(days=i), tmin, tmax, daily_precip) for i in range(days)
    ]


def test_feature_names_order():
    assert SOYBEAN_FEATURE_NAMES[0] == "water_deficit_reproductive_mm"


def test_wet_season_has_no_deficit_and_no_dry_spell():
    series = _season_series(2027, daily_precip=10.0)  # chuva abundante todo dia
    f = build_soybean_features(series, latitude_deg=-27.6, harvest_year=2027, calendar=SOYBEAN_RS)
    assert f["water_deficit_reproductive_mm"] == 0.0
    assert f["dry_spell_longest_reproductive_days"] == 0.0
    assert f["precip_total_season_mm"] > 1000


def test_dry_season_has_deficit_and_long_dry_spell():
    series = _season_series(2027, daily_precip=0.0)  # nenhuma chuva
    f = build_soybean_features(series, latitude_deg=-27.6, harvest_year=2027, calendar=SOYBEAN_RS)
    assert f["water_deficit_reproductive_mm"] > 0.0
    # reprodutivo 21/dez a 28/fev = 70 dias todos secos
    assert f["dry_spell_longest_reproductive_days"] == 70.0
    assert f["precip_total_season_mm"] == 0.0


def test_hargreaves_et0_reasonable():
    # ET0 de verão em latitude subtropical deve ficar ~3-8 mm/dia
    et0 = hargreaves_et0(tmin=18.0, tmax=32.0, latitude_deg=-27.6, day=date(2027, 1, 15))
    assert 3.0 < et0 < 9.0
