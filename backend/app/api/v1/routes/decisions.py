"""Endpoint da camada de decisão (atenção por flags + ranking multi-critério)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.routes.regional_intelligence import _model
from app.infra.db import get_session
from app.infra.repositories import EventRepository, FarmRepository, PlanningRepository
from app.schemas.decisions import DecisionsResponse
from app.services.decisions import DecisionsService, FarmNotFound
from app.services.insights import InsightsService

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> DecisionsService:
    try:
        model = _model()
    except FileNotFoundError as exc:
        raise HTTPException(503, "Modelo ausente.") from exc
    farms = FarmRepository(session)
    events = EventRepository(session)
    return DecisionsService(
        farms=farms, events=events, planning=PlanningRepository(session), model=model,
        insights=InsightsService(farms=farms, events=events, model=model),
    )


@router.get("/farms/{farm_id}/decisions", response_model=DecisionsResponse)
def decisions(farm_id: int, svc: DecisionsService = Depends(get_service)) -> DecisionsResponse:
    try:
        return DecisionsResponse(**svc.decisions(farm_id))
    except FarmNotFound as exc:
        raise HTTPException(404, f"Farm {exc} inexistente") from exc
