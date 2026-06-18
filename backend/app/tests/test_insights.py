"""Testes do domínio de insights (sumários, estatística e regras com gating)."""

from app.domain.insights import (
    FieldSeasonRecord,
    build_field_summary,
    detect_trend,
    generate_insights,
    yield_anomaly_zscore,
)
from app.domain.insights.engine import (
    cost_trends,
    performance_ranking,
    stability_ranking,
    yield_anomalies,
)


def _rec(fid, name, year, actual, fitted, cost=None, area=100.0):
    return FieldSeasonRecord(
        field_id=fid, field_name=name, harvest_year=year, area_ha=area,
        actual_sc_ha=actual, regional_fitted_sc_ha=fitted, cost_total=cost,
    )


def test_rel_residual_and_cost_per_ha():
    r = _rec(1, "A", 2024, 55.0, 50.0, cost=200000, area=100)
    assert abs(r.rel_residual - 0.1) < 1e-9
    assert r.cost_per_ha == 2000.0


def test_detect_trend_gating_and_direction():
    assert detect_trend([(2020, 10.0), (2021, 11.0)]) is None  # n<3
    up = detect_trend([(2020, 100.0), (2021, 120.0), (2022, 150.0)])
    assert up["direction"] == "rising" and up["monotonic"] is True
    flat = detect_trend([(2020, 100.0), (2021, 101.0), (2022, 99.0)])
    assert flat["direction"] == "stable"


def test_anomaly_zscore_gating():
    assert yield_anomaly_zscore([0.1, 0.1, 0.1]) is None  # n<4
    # variância nula no histórico -> z indefinido -> None (comportamento honesto)
    assert yield_anomaly_zscore([0.0, 0.0, 0.0, 1.0]) is None
    z = yield_anomaly_zscore([0.0, 0.05, -0.05, 1.0])  # prior com variância
    assert z is not None and z > 3


def test_build_summary_stability_none_for_single_season():
    s = build_field_summary([_rec(1, "A", 2024, 50.0, 50.0)])
    assert s.n_seasons == 1
    assert s.yield_stability_std is None


def test_performance_ranking_requires_two_seasons():
    # 1 safra por talhão -> não ranqueia (gating)
    summaries = [
        build_field_summary([_rec(1, "A", 2024, 55.0, 50.0)]),
        build_field_summary([_rec(2, "B", 2024, 45.0, 50.0)]),
    ]
    assert performance_ranking(summaries) == []


def test_performance_ranking_best_worst():
    a = build_field_summary([_rec(1, "A", y, 55.0, 50.0) for y in (2023, 2024)])
    b = build_field_summary([_rec(2, "B", y, 45.0, 50.0) for y in (2023, 2024)])
    out = performance_ranking([a, b])
    types = {i.type for i in out}
    assert "best_field_yield" in types and "worst_field_yield" in types
    best = next(i for i in out if i.type == "best_field_yield")
    assert best.field_id == 1


def test_stability_ranking_gap_required():
    # dois talhões igualmente estáveis -> sem insight (gap insuficiente)
    a = build_field_summary([_rec(1, "A", y, 50.0 + (y % 2), 50.0) for y in range(2019, 2025)])
    b = build_field_summary([_rec(2, "B", y, 50.0 + (y % 2), 50.0) for y in range(2019, 2025)])
    assert stability_ranking([a, b]) == []


def test_stability_ranking_detects_unstable():
    stable = build_field_summary([_rec(1, "Est", y, 50.0, 50.0) for y in range(2019, 2025)])
    unstable = build_field_summary(
        [_rec(2, "Insta", y, 50.0 * (1.2 if y % 2 else 0.8), 50.0) for y in range(2019, 2025)]
    )
    out = stability_ranking([stable, unstable])
    least = next(i for i in out if i.type == "least_stable_field")
    assert least.field_id == 2


def test_cost_trend_insight():
    recs = [_rec(1, "A", y, 50.0, 50.0, cost=(100000 + (y - 2020) * 30000))
            for y in range(2020, 2024)]
    s = build_field_summary(recs)
    out = cost_trends([s])
    assert out and out[0].type == "cost_trend"
    assert out[0].evidence["net_change_pct"] > 10


def test_yield_anomaly_insight():
    # histórico com pequena variância (residuos ~0 ±) e uma queda anômala em 2024
    actuals = [50.0, 51.0, 49.0, 50.5, 49.5]
    recs = [_rec(1, "A", 2019 + i, a, 50.0) for i, a in enumerate(actuals)]
    recs.append(_rec(1, "A", 2024, 20.0, 50.0))  # queda anômala
    out = yield_anomalies({1: recs})
    assert out and out[0].type == "yield_anomaly"
    assert out[0].evidence["zscore"] < -2


def test_generate_insights_sorted_by_confidence():
    a = build_field_summary([_rec(1, "A", y, 55.0, 50.0) for y in range(2019, 2025)])
    b = build_field_summary([_rec(2, "B", y, 45.0, 50.0) for y in range(2019, 2025)])
    items = generate_insights([a, b], {1: [], 2: []})
    confs = [i.confidence for i in items]
    order = {"alta": 0, "moderada": 1, "exploratória": 2}
    assert [order[c] for c in confs] == sorted(order[c] for c in confs)


def test_no_insights_from_empty():
    assert generate_insights([], {}) == []
