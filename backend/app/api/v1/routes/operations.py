"""Endpoints da timeline de eventos e do catálogo de produtos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db import get_session
from app.infra.repositories import EventRepository, ProductRepository
from app.schemas.operations import (
    AgriculturalEventCreate,
    AgriculturalEventOut,
    ProductCreate,
    ProductOut,
)
from app.services.operations import EventService, ProductService

router = APIRouter()


def get_event_service(session: Session = Depends(get_session)) -> EventService:
    return EventService(repo=EventRepository(session))


def get_product_service(session: Session = Depends(get_session)) -> ProductService:
    return ProductService(repo=ProductRepository(session))


@router.post(
    "/crop-cycles/{cycle_id}/events", response_model=AgriculturalEventOut, status_code=201
)
def add_event(
    cycle_id: int, body: AgriculturalEventCreate,
    svc: EventService = Depends(get_event_service),
) -> AgriculturalEventOut:
    try:
        e = svc.record_event(
            crop_cycle_id=cycle_id, event_type=body.event_type.value,
            event_date=body.event_date,
            **body.model_dump(exclude={"event_type", "event_date"}),
        )
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return AgriculturalEventOut(**vars(e))


@router.get("/crop-cycles/{cycle_id}/events", response_model=list[AgriculturalEventOut])
def list_events(
    cycle_id: int, svc: EventService = Depends(get_event_service)
) -> list[AgriculturalEventOut]:
    return [AgriculturalEventOut(**vars(e)) for e in svc.timeline(cycle_id)]


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    body: ProductCreate, svc: ProductService = Depends(get_product_service)
) -> ProductOut:
    p = svc.create_product(
        category=body.category.value, commercial_name=body.commercial_name,
        **body.model_dump(exclude={"category", "commercial_name"}),
    )
    return ProductOut(**vars(p))


@router.get("/products", response_model=list[ProductOut])
def list_products(svc: ProductService = Depends(get_product_service)) -> list[ProductOut]:
    return [ProductOut(**vars(p)) for p in svc.list_products()]
