from datetime import date, timedelta

from app.domain.climate import DailyWeather
from app.domain.planting_date import SOYBEAN_PHENOLOGY_RS
from app.domain.planting_date.phenology import PhenologyModel


def _constant_series(start: date, days: int, tmean: float) -> list[DailyWeather]:
    # tmin/tmax simétricos em torno da média desejada
    return [DailyWeather(start + timedelta(days=i), tmean - 5, tmean + 5, 0.0) for i in range(days)]


def test_stages_reached_by_gdd():
    # tmean=25, base 10 -> 15 GDD/dia (o dia do plantio já acumula).
    # R1=720 GDD -> 48 dias acumulando -> plantio+47; R6=1500 -> plantio+99.
    s = _constant_series(date(2026, 10, 1), 200, tmean=25.0)
    m = PhenologyModel()
    st = m.stages(s, date(2026, 10, 1))
    assert (st.r1_begin_flowering - st.planting).days == 47
    assert (st.r6_full_seed - st.planting).days == 99


def test_warmer_accumulates_faster():
    cold = _constant_series(date(2026, 10, 1), 250, tmean=18.0)  # 8 GDD/dia
    warm = _constant_series(date(2026, 10, 1), 250, tmean=28.0)  # 18 GDD/dia
    m = PhenologyModel()
    r1_cold = (m.stages(cold, date(2026, 10, 1)).r1_begin_flowering - date(2026, 10, 1)).days
    r1_warm = (m.stages(warm, date(2026, 10, 1)).r1_begin_flowering - date(2026, 10, 1)).days
    assert r1_warm < r1_cold


def test_later_planting_shifts_window_later():
    s = _constant_series(date(2026, 10, 1), 250, tmean=24.0)
    m = SOYBEAN_PHENOLOGY_RS
    early = m.stages(s, date(2026, 10, 5)).reproductive_window
    late = m.stages(s, date(2026, 10, 25)).reproductive_window
    assert late[0] > early[0] and late[1] > early[1]
