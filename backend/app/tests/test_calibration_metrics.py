"""Testes das métricas de calibração (puras)."""

from app.domain.calibration import (
    coverage,
    pinball_loss,
    point_errors,
    reliability_curve,
    sharpness,
    wilson_interval,
)


def test_wilson_bounds():
    lo, hi = wilson_interval(80, 100)
    assert 0 <= lo < 0.8 < hi <= 1
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_wilson_narrows_with_n():
    _, hi_small = wilson_interval(8, 10)
    _, hi_big = wilson_interval(800, 1000)
    assert (hi_big - 0.8) < (hi_small - 0.8)  # mais dados -> CI mais apertado


def test_coverage_perfect():
    a = [float(i % 50) for i in range(100)]
    lo = [-1000.0] * 100
    hi = [1000.0] * 100
    cr = coverage(a, lo, hi, 0.8)
    assert cr.observed == 1.0
    assert cr.verdict == "underconfident"  # cobre demais (n grande -> CI conclui)


def test_coverage_overconfident():
    a = [float(i) for i in range(200)]
    lo = [x - 0.1 for x in a]
    hi = [x + 0.1 for x in a]
    # quase nada coberto além do próprio ponto; aqui actual==ponto então cobre tudo...
    # força miss: desloca os intervalos para longe
    lo = [x + 50 for x in a]
    hi = [x + 60 for x in a]
    cr = coverage(a, lo, hi, 0.8)
    assert cr.observed == 0.0
    assert cr.verdict == "overconfident"


def test_sharpness():
    s = sharpness([40.0, 45.0], [60.0, 55.0], [50.0, 50.0])
    assert s["mean_width"] == 15.0
    assert s["relative_width_pct"] == 30.0


def test_point_errors_signs():
    pe = point_errors([50.0, 50.0], [52.0, 54.0])  # super-previsão
    assert pe["bias"] == 3.0
    assert pe["mae"] == 3.0
    assert pe["rmse"] >= pe["mae"]


def test_pinball_nonnegative_and_p50_is_half_mae():
    a = [10.0, 20.0, 30.0]
    p50 = [12.0, 18.0, 33.0]
    loss = pinball_loss(a, p50, 0.5)
    assert loss >= 0
    mae = point_errors(a, p50)["mae"]
    assert abs(loss - mae / 2) < 0.01  # pinball(0.5) = MAE/2 (a menos de arredondamento)


def test_pinball_asymmetry():
    a = [10.0]
    # no quantil 0.9, subestimar (q<a) é penalizado por 0.9
    under = pinball_loss(a, [0.0], 0.9)
    over = pinball_loss(a, [20.0], 0.9)
    assert under > over


def test_reliability_curve_structure():
    a = [10.0, 20.0, 30.0]
    levels = {0.5: ([0, 0, 0], [100, 100, 100]), 0.9: ([0, 0, 0], [100, 100, 100])}
    curve = reliability_curve(a, levels)
    assert [p["nominal"] for p in curve] == [0.5, 0.9]
    assert all(p["observed"] == 1.0 for p in curve)
