"""DTOs de captura rápida (presets e quick-log)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.domain.farm import EventType
from app.schemas.operations import AgriculturalEventOut


class EventPresetCreate(BaseModel):
    name: str
    event_type: EventType
    product_name: str | None = None
    product_id: int | None = None
    default_quantity: float | None = Field(None, ge=0)
    unit: str | None = None
    default_cost: float | None = Field(None, ge=0)
    cost_is_per_hectare: bool = False
    notes: str | None = None


class EventPresetOut(BaseModel):
    id: int
    name: str
    event_type: EventType
    product_name: str | None = None
    product_id: int | None = None
    default_quantity: float | None = None
    unit: str | None = None
    default_cost: float | None = None
    cost_is_per_hectare: bool = False
    notes: str | None = None
    created_at: datetime | None = None


class QuickLogRequest(BaseModel):
    crop_cycle_ids: list[int] = Field(..., min_length=1)
    event_date: date
    preset_id: int | None = None
    event_type: EventType | None = None
    product_name: str | None = None
    quantity: float | None = Field(None, ge=0)
    unit: str | None = None
    cost: float | None = Field(None, ge=0)
    notes: str | None = None

    @model_validator(mode="after")
    def _require_type_or_preset(self) -> QuickLogRequest:
        if self.preset_id is None and self.event_type is None:
            raise ValueError("Informe preset_id ou event_type.")
        return self


class QuickLogResponse(BaseModel):
    created: list[AgriculturalEventOut]
