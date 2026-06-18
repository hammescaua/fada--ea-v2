"""Endpoints de captura rápida (presets e quick-log)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db import get_session
from app.infra.repositories import EventRepository, FarmRepository, PresetRepository
from app.schemas.capture import (
    EventPresetCreate,
    EventPresetOut,
    QuickLogRequest,
    QuickLogResponse,
)
from app.schemas.operations import AgriculturalEventOut
from app.services.capture import CaptureService, CycleNotFound, PresetNotFound

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> CaptureService:
    return CaptureService(
        presets=PresetRepository(session), events=EventRepository(session),
        farms=FarmRepository(session),
    )


@router.post("/event-presets", response_model=EventPresetOut, status_code=201)
def create_preset(
    body: EventPresetCreate, svc: CaptureService = Depends(get_service)
) -> EventPresetOut:
    p = svc.create_preset(
        name=body.name, event_type=body.event_type.value,
        **body.model_dump(exclude={"name", "event_type"}),
    )
    return EventPresetOut(**vars(p))


@router.get("/event-presets", response_model=list[EventPresetOut])
def list_presets(svc: CaptureService = Depends(get_service)) -> list[EventPresetOut]:
    return [EventPresetOut(**vars(p)) for p in svc.list_presets()]


@router.post("/quick-log", response_model=QuickLogResponse, status_code=201)
def quick_log(body: QuickLogRequest, svc: CaptureService = Depends(get_service)) -> QuickLogResponse:
    try:
        created = svc.quick_log(
            crop_cycle_ids=body.crop_cycle_ids, event_date=body.event_date,
            preset_id=body.preset_id,
            event_type=body.event_type.value if body.event_type else None,
            product_name=body.product_name, quantity=body.quantity, unit=body.unit,
            cost=body.cost, notes=body.notes,
        )
    except PresetNotFound as exc:
        raise HTTPException(404, f"Preset {exc} inexistente") from exc
    except CycleNotFound as exc:
        raise HTTPException(404, f"CropCycle {exc} inexistente") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return QuickLogResponse(created=[AgriculturalEventOut(**vars(e)) for e in created])
