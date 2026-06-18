"""Conversões de massa e produtividade.

A "saca" (bag) é a unidade comercial padrão no Brasil. Para soja e milho a saca
equivale a **60 kg** (cf. uso de mercado e B3). Outras culturas podem ter outra
referência e devem ser tratadas explicitamente.
"""

from __future__ import annotations

# Saca de soja/milho. Mantida nomeada para evitar "número mágico" no código.
BAG_KG: float = 60.0


def bags_to_kg(bags: float, bag_kg: float = BAG_KG) -> float:
    """Converte sacas para quilogramas."""
    _require_non_negative(bags, "bags")
    return bags * bag_kg


def kg_to_bags(kg: float, bag_kg: float = BAG_KG) -> float:
    """Converte quilogramas para sacas."""
    _require_non_negative(kg, "kg")
    return kg / bag_kg


def kg_per_ha_to_bags_per_ha(kg_per_ha: float, bag_kg: float = BAG_KG) -> float:
    """Converte produtividade de kg/ha para sc/ha."""
    _require_non_negative(kg_per_ha, "kg_per_ha")
    return kg_per_ha / bag_kg


def bags_per_ha_to_kg_per_ha(bags_per_ha: float, bag_kg: float = BAG_KG) -> float:
    """Converte produtividade de sc/ha para kg/ha."""
    _require_non_negative(bags_per_ha, "bags_per_ha")
    return bags_per_ha * bag_kg


def _require_non_negative(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} não pode ser negativo (recebido: {value})")
