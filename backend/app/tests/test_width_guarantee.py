"""Garantia fundamental: a personalização NUNCA reduz a largura do intervalo.

Prova por construção: meia-largura_pers = √(reg² + (ponto·SE_bias)²) ≥ reg.
Aqui validamos com property-based testing (milhares de entradas aleatórias) tanto a
função pura quanto a integração com adaptive.personalize (ADR-0012/0013).
"""

import random

from app.domain.adaptive import ShrinkagePrior, personalize, shrinkage_weight
from app.domain.calibration import personalized_halfwidth, width_never_decreases

PRIOR = ShrinkagePrior()


def test_personalized_halfwidth_formula():
    # √(10² + (50·0.06)²) = √(100+9) ≈ 10.44
    assert abs(personalized_halfwidth(10.0, 50.0, 0.06) - (109 ** 0.5)) < 1e-9


def test_width_never_decreases_property_random():
    rng = random.Random(42)
    for _ in range(20000):
        h_reg = rng.uniform(0.0, 40.0)
        point = rng.uniform(1.0, 90.0)
        se_bias = rng.uniform(0.0, 1.0)
        assert width_never_decreases(h_reg, point, se_bias)
        assert personalized_halfwidth(h_reg, point, se_bias) >= h_reg - 1e-12


def test_personalize_interval_width_dominates_regional():
    """Integração: largura(personalizado) >= largura(regional) para qualquer n."""
    rng = random.Random(7)
    for _ in range(5000):
        point = rng.uniform(20.0, 70.0)
        half = rng.uniform(2.0, 25.0)
        lo, hi = point - half, point + half
        n = rng.randint(0, 60)
        bias = rng.uniform(-0.4, 0.4)
        var = rng.uniform(0.0, 0.2)
        pred = personalize(point, (lo, hi), {"normal": point}, n, bias, var, PRIOR)
        reg_w = pred.regional_interval_sc_ha[1] - pred.regional_interval_sc_ha[0]
        per_w = pred.personalized_interval_sc_ha[1] - pred.personalized_interval_sc_ha[0]
        # tolerância para o arredondamento a 1 casa nos extremos do intervalo
        assert per_w >= reg_w - 0.21


def test_zero_cycles_equality():
    # n=0 -> SE_bias=0 -> largura idêntica à regional
    assert width_never_decreases(10.0, 50.0, 0.0)
    assert personalized_halfwidth(10.0, 50.0, 0.0) == 10.0
    w, se = shrinkage_weight(0, 0.0, PRIOR)
    assert w == 0.0 and se == 0.0
