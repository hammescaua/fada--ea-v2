"""Testa o encolhimento hierárquico (núcleo científico do adaptive)."""

from app.domain.adaptive import ShrinkagePrior, personalize, shrinkage_weight
from app.domain.adaptive.shrinkage import compute_profile_stats

PRIOR = ShrinkagePrior()


def test_weight_increases_with_n():
    ws = [shrinkage_weight(n, 0.01, PRIOR)[0] for n in [1, 5, 10, 20]]
    assert ws == sorted(ws)  # monotônico crescente
    assert ws[0] < 0.2 and ws[-1] > 0.7


def test_consistent_farm_trusted_more_than_noisy():
    w_consistent = shrinkage_weight(10, 0.005, PRIOR)[0]
    w_noisy = shrinkage_weight(10, 0.05, PRIOR)[0]
    assert w_consistent > w_noisy


def test_zero_cycles_returns_regional_unchanged():
    pred = personalize(50.0, (40.0, 60.0), {"normal": 50.0}, 0, 0.0, 0.0, PRIOR)
    assert pred.personalized_point_sc_ha == 50.0
    assert pred.personalized_interval_sc_ha == (40.0, 60.0)
    assert pred.confidence_score == 0.0
    assert pred.adaptation_level == "nenhuma"


def test_interval_never_narrower_than_regional():
    # incerteza honesta: a largura personalizada >= largura regional
    for n in [1, 5, 10, 20]:
        pred = personalize(50.0, (40.0, 60.0), {"normal": 50.0}, n, 0.12, 0.01, PRIOR)
        reg_w = pred.regional_interval_sc_ha[1] - pred.regional_interval_sc_ha[0]
        per_w = pred.personalized_interval_sc_ha[1] - pred.personalized_interval_sc_ha[0]
        assert per_w >= reg_w - 1e-6


def test_shrinkage_pulls_toward_regional_at_low_n():
    # bias observado +20%, mas com 1 safra a correção aplicada é muito menor
    pred = personalize(50.0, (40.0, 60.0), {"normal": 50.0}, 1, 0.20, 0.01, PRIOR)
    assert abs(pred.farm_adjustment_pct) < abs(pred.observed_bias_pct) / 2


def test_converges_to_bias_with_many_cycles():
    pred = personalize(50.0, (40.0, 60.0), {"normal": 50.0}, 30, 0.12, 0.005, PRIOR)
    assert pred.farm_adjustment_pct > 9.5  # encolhimento leve, aproxima do +12%


def test_compute_profile_stats():
    stats = compute_profile_stats([0.1, 0.12, 0.08], [5.0, 6.0, 4.0])
    assert stats.n == 3
    assert abs(stats.mean_relative_residual - 0.1) < 1e-9
    assert stats.median_residual_sc_ha == 5.0
