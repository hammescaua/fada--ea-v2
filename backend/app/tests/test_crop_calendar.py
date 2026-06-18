from datetime import date

from app.domain.crop import SOYBEAN_RS


def test_windows_for_2027():
    w = SOYBEAN_RS.windows_for(2027)
    # safra 2026/27: começa em out/2026, reprodutivo cruza o ano-novo, termina em 2027
    assert w.season[0] == date(2026, 10, 1)
    assert w.season[1] == date(2027, 3, 31)
    assert w.reproductive[0] == date(2026, 12, 21)
    assert w.reproductive[1] == date(2027, 2, 28)
    assert w.vegetative[0] == date(2026, 10, 1)


def test_planting_window_is_previous_calendar_year():
    start, end = SOYBEAN_RS.planting_window_for(2027)
    assert start == date(2026, 10, 11)
    assert end == date(2026, 12, 10)
