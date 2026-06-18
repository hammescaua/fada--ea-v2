"""DTOs de planejamento (PlannedEvent, plano x realizado, agenda)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain.farm import EventType


class PlannedEventCreate(BaseModel):
    event_type: EventType
    planned_date: date
    product_name: str | None = None
    quantity: float | None = Field(None, ge=0)
    unit: str | None = None
    expected_cost: float | None = Field(None, ge=0)
    notes: str | None = None


class PlannedEventOut(BaseModel):
    id: int
    crop_cycle_id: int
    event_type: EventType
    planned_date: date
    product_name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    expected_cost: float | None = None
    notes: str | None = None
    created_at: datetime | None = None


class PlanVsActualResponse(BaseModel):
    planned_total_cost: float
    actual_total_cost: float
    cost_variance: float
    cost_variance_pct: float | None
    pct_budget_spent: float | None
    remaining_budget: float
    over_budget: bool
    area_ha: float | None
    planned_cost_per_ha: float | None
    actual_cost_per_ha: float | None
    planned_applications: int
    actual_applications: int
    expected_revenue: float | None
    expected_profit: float | None
    interpretation: str


class AgendaItemDTO(BaseModel):
    planned_event_id: int | None
    event_type: str
    planned_date: str
    product_name: str | None
    expected_cost: float | None
    status: str


class AgendaResponse(BaseModel):
    crop_cycle_id: int
    items: list[AgendaItemDTO]
    summary: dict[str, int]
