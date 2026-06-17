"""DTOs da timeline de eventos e do catálogo de produtos."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain.farm import EventType
from app.domain.catalog import ProductCategory


class AgriculturalEventCreate(BaseModel):
    event_type: EventType
    event_date: date
    product_name: str | None = None
    product_id: int | None = None
    quantity: float | None = Field(None, ge=0)
    unit: str | None = Field(None, examples=["L/ha", "kg/ha", "L", "kg"])
    cost: float | None = Field(None, ge=0, description="Custo total da operação (R$)")
    notes: str | None = None


class AgriculturalEventOut(BaseModel):
    id: int
    crop_cycle_id: int
    event_type: EventType
    event_date: date
    product_name: str | None = None
    product_id: int | None = None
    quantity: float | None = None
    unit: str | None = None
    cost: float | None = None
    notes: str | None = None
    created_at: datetime | None = None


class ProductCreate(BaseModel):
    category: ProductCategory
    commercial_name: str
    active_ingredient: str | None = None
    formulation: str | None = None
    unit: str | None = None
    description: str | None = None


class ProductOut(BaseModel):
    id: int
    category: ProductCategory
    commercial_name: str
    active_ingredient: str | None = None
    formulation: str | None = None
    unit: str | None = None
    description: str | None = None
    created_at: datetime | None = None
