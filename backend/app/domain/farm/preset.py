"""EventPreset — template de operação para captura rápida (reduz atrito).

Um preset pré-preenche um AgriculturalEvent (tipo, produto, dose, custo padrão).
"Operações favoritas" são presets. Ver ADR-0015.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.farm.events import EventType


@dataclass
class EventPreset:
    name: str
    event_type: EventType
    product_name: str | None = None
    product_id: int | None = None
    default_quantity: float | None = None
    unit: str | None = None
    default_cost: float | None = None     # custo total padrão (R$) ou por ha (ver basis)
    cost_is_per_hectare: bool = False      # se True, default_cost é R$/ha
    notes: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("EventPreset.name não pode ser vazio")
        if self.default_cost is not None and self.default_cost < 0:
            raise ValueError("default_cost não pode ser negativo")

    def cost_for_area(self, area_ha: float | None) -> float | None:
        """Resolve o custo total do evento para uma área (se custo for por ha)."""
        if self.default_cost is None:
            return None
        if self.cost_is_per_hectare and area_ha:
            return round(self.default_cost * area_ha, 2)
        return self.default_cost
