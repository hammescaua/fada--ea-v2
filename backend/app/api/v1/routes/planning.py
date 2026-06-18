"""Endpoints de planejamento: PlannedEvent, plano x realizado e agenda."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db import get_session
from app.infra.repositories import EventRepository, FarmRepository, PlanningRepository
from app.schemas.decisions import CostProjectionResponse
from app.schemas.planning import (
    AgendaResponse,
    PlanVsActualResponse,
    PlannedEventCreate,
    PlannedEventOut,
)
from app.services.planning import CycleNotFound, PlanningService

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> PlanningService:
    return PlanningService(
        farms=FarmRepository(session), planning=PlanningRepository(session),
        events=EventRepository(session),
    )


@router.post("/crop-cycles/{cycle_id}/planned-events", response_model=PlannedEventOut,
             status_code=201)
def add_planned_event(
    cycle_id: int, body: PlannedEventCreate, svc: PlanningService = Depends(get_service)
) -> PlannedEventOut:
    try:
        p = svc.add_planned_event(
            cycle_id, event_type=body.event_type, planned_date=body.planned_date,
            **body.model_dump(exclude={"event_type", "planned_date"}),
        )
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return PlannedEventOut(**vars(p))


@router.get("/crop-cycles/{cycle_id}/planned-events", response_model=list[PlannedEventOut])
def list_planned(cycle_id: int, svc: PlanningService = Depends(get_service)) -> list[PlannedEventOut]:
    return [PlannedEventOut(**vars(p)) for p in svc.list_planned(cycle_id)]


@router.get("/crop-cycles/{cycle_id}/plan-vs-actual", response_model=PlanVsActualResponse)
def plan_vs_actual(
    cycle_id: int, svc: PlanningService = Depends(get_service)
) -> PlanVsActualResponse:
    try:
        return PlanVsActualResponse(**svc.plan_vs_actual(cycle_id))
    except CycleNotFound as exc:
        raise HTTPException(404, f"CropCycle {exc} inexistente") from exc


@router.get("/crop-cycles/{cycle_id}/agenda", response_model=AgendaResponse)
def agenda(cycle_id: int, svc: PlanningService = Depends(get_service)) -> AgendaResponse:
    try:
        return AgendaResponse(**svc.agenda(cycle_id))
    except CycleNotFound as exc:
        raise HTTPException(404, f"CropCycle {exc} inexistente") from exc


@router.get("/crop-cycles/{cycle_id}/cost-projection", response_model=CostProjectionResponse)
def cost_projection(
    cycle_id: int, svc: PlanningService = Depends(get_service)
) -> CostProjectionResponse:
    try:
        return CostProjectionResponse(**svc.project_cost(cycle_id))
    except CycleNotFound as exc:
        raise HTTPException(404, f"CropCycle {exc} inexistente") from exc
