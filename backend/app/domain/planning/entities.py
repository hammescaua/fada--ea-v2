"""PlannedEvent — operação planejada (espelho do AgriculturalEvent)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.farm.events import EventType


@dataclass
class PlannedEvent:
    crop_cycle_id: int
    event_type: EventType
    planned_date: date
    product_name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    expected_cost: float | None = None    # custo total esperado (R$)
    notes: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.expected_cost is not None and self.expected_cost < 0:
            raise ValueError("expected_cost não pode ser negativo")

    @property
    def is_application(self) -> bool:
        from app.domain.farm.events import APPLICATION_EVENTS
        return self.event_type in APPLICATION_EVENTS
