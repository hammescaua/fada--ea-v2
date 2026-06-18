"""Endpoints de Field Intelligence e Insight Engine."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.routes.regional_intelligence import _model
from app.infra.db import get_session
from app.infra.repositories import EventRepository, FarmRepository
from app.schemas.insights import FieldAnalyticsResponse, InsightsResponse
from app.services.insights import FarmNotFound, InsightsService

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> InsightsService:
    try:
        model = _model()
    except FileNotFoundError as exc:
        raise HTTPException(503, "Modelo ausente.") from exc
    return InsightsService(
        farms=FarmRepository(session), events=EventRepository(session), model=model
    )


@router.get("/farms/{farm_id}/field-analytics", response_model=FieldAnalyticsResponse)
def field_analytics(
    farm_id: int, svc: InsightsService = Depends(get_service)
) -> FieldAnalyticsResponse:
    try:
        return FieldAnalyticsResponse(**svc.field_analytics(farm_id))
    except FarmNotFound as exc:
        raise HTTPException(404, f"Farm {exc} inexistente") from exc


@router.get("/farms/{farm_id}/insights", response_model=InsightsResponse)
def insights(farm_id: int, svc: InsightsService = Depends(get_service)) -> InsightsResponse:
    try:
        return InsightsResponse(**svc.insights(farm_id))
    except FarmNotFound as exc:
        raise HTTPException(404, f"Farm {exc} inexistente") from exc
