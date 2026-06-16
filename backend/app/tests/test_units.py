import pytest

from app.domain.units import (
    BAG_KG,
    bags_per_ha_to_kg_per_ha,
    bags_to_kg,
    kg_per_ha_to_bags_per_ha,
    kg_to_bags,
)


def test_bag_is_60kg():
    assert BAG_KG == 60.0


def test_bags_kg_roundtrip():
    assert bags_to_kg(50) == 3000.0
    assert kg_to_bags(3000) == 50.0


def test_yield_conversion():
    # 3600 kg/ha = 60 sc/ha (produtividade típica de soja)
    assert kg_per_ha_to_bags_per_ha(3600) == 60.0
    assert bags_per_ha_to_kg_per_ha(60) == 3600.0


def test_negative_rejected():
    with pytest.raises(ValueError):
        bags_to_kg(-1)
