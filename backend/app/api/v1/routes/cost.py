"""Endpoints financeiros (Cost Engine)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.routes.regional_intelligence import _model
from app.infra.db import get_session
from app.infra.repositories import EventRepository, FarmRepository
from app.schemas.cost import (
    CostBreakdownOut,
    FinancialsRequest,
    FinancialsResponse,
    ScenarioResultOut,
)
from app.services.cost import AreaUnknown, CostService, CycleNotFound

router = APIRouter()


def get_cost_service(session: Session = Depends(get_session)) -> CostService:
    return CostService(
        farms=FarmRepository(session), events=EventRepository(session), model=_model()
    )


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, CycleNotFound):
        return HTTPException(404, f"CropCycle {exc} inexistente")
    if isinstance(exc, AreaUnknown):
        return HTTPException(
            422, "Área desconhecida: informe area_ha no CropCycle ou no Field."
        )
    raise exc


@router.get("/crop-cycles/{cycle_id}/cost", response_model=CostBreakdownOut)
def cost_breakdown_endpoint(
    cycle_id: int, svc: CostService = Depends(get_cost_service)
) -> CostBreakdownOut:
    try:
        b = svc.breakdown(cycle_id)
    except (CycleNotFound, AreaUnknown) as exc:
        raise _handle(exc) from exc
    return CostBreakdownOut(**vars(b))


@router.post("/crop-cycles/{cycle_id}/financials", response_model=FinancialsResponse)
def financials_endpoint(
    cycle_id: int, body: FinancialsRequest, svc: CostService = Depends(get_cost_service)
) -> FinancialsResponse:
    try:
        result = svc.financials(cycle_id, body.price_per_bag)
    except (CycleNotFound, AreaUnknown) as exc:
        raise _handle(exc) from exc
    return FinancialsResponse(
        breakdown=CostBreakdownOut(**vars(result["breakdown"])),
        price_per_bag=result["price_per_bag"],
        break_even_yield_sc_ha=result["break_even_yield_sc_ha"],
        yield_source=result["yield_source"],
        scenarios=[ScenarioResultOut(**vars(s)) for s in result["scenarios"]],
    )
