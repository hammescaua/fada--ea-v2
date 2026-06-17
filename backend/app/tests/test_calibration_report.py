"""Testes do CalibrationReport e da interpretação determinística."""

from app.domain.calibration import build_report

LEVELS = [0.5, 0.8, 0.9, 0.95]


def _intervals(points, half_by_level):
    return {lv: ([p - h for p in points], [p + h for p in points])
            for lv, h in half_by_level.items()}


def _quantiles(points):
    return {0.1: [p - 5 for p in points], 0.5: points, 0.9: [p + 5 for p in points]}


def test_calibrated_report():
    actuals = [50.0 + (i % 10 - 5) for i in range(200)]  # espalhados em ±5
    points = [50.0] * 200
    # intervalos largos o suficiente para cobrir ~80% no nível 80
    half = {0.5: 2.0, 0.8: 6.0, 0.9: 8.0, 0.95: 10.0}
    rep = build_report("R", actuals, points, _intervals(points, half), _quantiles(points))
    assert rep.n_predictions == 200
    assert 0.0 <= rep.coverage_80 <= 1.0
    assert "predições" in rep.interpretation
    assert rep.pinball["mean"] >= 0


def test_overconfident_detected():
    points = [float(i) for i in range(300)]
    # observados longe do ponto + intervalos minúsculos -> cobertura ~0 -> overconfident
    actuals = [p + (5 if i % 2 else -5) for i, p in enumerate(points)]
    half = {lv: 0.01 for lv in LEVELS}
    rep = build_report("R", actuals, points, _intervals(points, half), _quantiles(points))
    assert rep.coverage_80 < 0.8
    assert rep.overconfident is True
    assert "OVERCONFIDENT" in rep.interpretation


def test_underconfident_detected():
    actuals = [50.0] * 300
    points = [50.0] * 300
    half = {lv: 100.0 for lv in LEVELS}  # intervalos enormes -> cobre 100%
    rep = build_report("R", actuals, points, _intervals(points, half), _quantiles(points))
    assert rep.coverage_80 == 1.0
    assert rep.underconfident is True


def test_to_dict_roundtrip():
    actuals = [50.0] * 50
    points = [50.0] * 50
    half = {lv: 10.0 for lv in LEVELS}
    rep = build_report("R", actuals, points, _intervals(points, half), _quantiles(points))
    d = rep.to_dict()
    assert d["label"] == "R" and "coverage_detail" in d and "reliability_curve" in d
