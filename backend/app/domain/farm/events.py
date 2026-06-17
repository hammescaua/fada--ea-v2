"""Eventos agrícolas — a timeline operacional (parte do agregado CropCycle).

Modelagem orientada a eventos (não event sourcing): uma única entidade flexível
com ``event_type``, em vez de dezenas de tabelas rígidas. O estado derivado (custo
total, nº de aplicações) é calculado na leitura pelo Cost Engine (ADR-0011).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class EventType(str, Enum):
    PLANTING = "PLANTING"
    BASE_FERTILIZATION = "BASE_FERTILIZATION"
    TOP_DRESSING = "TOP_DRESSING"
    HERBICIDE = "HERBICIDE"
    FUNGICIDE = "FUNGICIDE"
    INSECTICIDE = "INSECTICIDE"
    FOLIAR = "FOLIAR"
    IRRIGATION = "IRRIGATION"
    HARVEST = "HARVEST"
    OTHER = "OTHER"


# Eventos considerados "aplicações" (pulverizações/adubações) para contagem de manejos.
APPLICATION_EVENTS = frozenset({
    EventType.BASE_FERTILIZATION,
    EventType.TOP_DRESSING,
    EventType.HERBICIDE,
    EventType.FUNGICIDE,
    EventType.INSECTICIDE,
    EventType.FOLIAR,
})


@dataclass
class AgriculturalEvent:
    """Um evento na timeline da safra.

    ``cost`` é o custo total da operação (R$); ``quantity``/``unit`` são descritivos
    do insumo aplicado. ``product_id`` referencia o catálogo opcionalmente, sem
    obrigar — baixo atrito de captura preserva o flywheel.
    """

    crop_cycle_id: int
    event_type: EventType
    event_date: date
    product_name: str | None = None
    product_id: int | None = None
    quantity: float | None = None
    unit: str | None = None
    cost: float | None = None
    notes: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.cost is not None and self.cost < 0:
            raise ValueError("cost não pode ser negativo")
        if self.quantity is not None and self.quantity < 0:
            raise ValueError("quantity não pode ser negativa")

    @property
    def is_application(self) -> bool:
        return self.event_type in APPLICATION_EVENTS
