"""Casos de uso da timeline de eventos e do catálogo de produtos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.catalog import Product, ProductCategory
from app.domain.farm import AgriculturalEvent, EventType
from app.infra.repositories import EventRepository, ProductRepository


@dataclass
class EventService:
    repo: EventRepository

    def record_event(
        self, crop_cycle_id: int, event_type: str, event_date: date, **fields
    ) -> AgriculturalEvent:
        return self.repo.add_event(
            AgriculturalEvent(
                crop_cycle_id=crop_cycle_id, event_type=EventType(event_type),
                event_date=event_date, **fields,
            )
        )

    def timeline(self, crop_cycle_id: int) -> list[AgriculturalEvent]:
        return self.repo.list_by_cycle(crop_cycle_id)


@dataclass
class ProductService:
    repo: ProductRepository

    def create_product(self, category: str, commercial_name: str, **fields) -> Product:
        return self.repo.add_product(
            Product(category=ProductCategory(category), commercial_name=commercial_name, **fields)
        )

    def list_products(self) -> list[Product]:
        return self.repo.list_products()
