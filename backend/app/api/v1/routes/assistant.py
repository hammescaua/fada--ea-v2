"""Endpoint conversacional /assistant."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.routes.planting_date import _service as _planting_service
from app.api.v1.routes.regional_intelligence import _model
from app.engine import build_explainer
from app.engine.orchestrator import DeterministicRouter, Orchestrator
from app.infra.db import get_session
from app.infra.repositories import EventRepository, FarmRepository
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.cost import CostService
from app.services.regional_intelligence import RegionalIntelligenceService

router = APIRouter()


def get_orchestrator(session: Session = Depends(get_session)) -> Orchestrator:
    try:
        model = _model()
        planting = _planting_service()
    except FileNotFoundError as exc:
        raise HTTPException(503, "Modelo/grid ausente.") from exc
    names = [info["name"] for info in model.municipalities().values()]
    return Orchestrator(
        regional=RegionalIntelligenceService(model=model, explainer=build_explainer()),
        planting=planting,
        cost=CostService(
            farms=FarmRepository(session), events=EventRepository(session), model=model
        ),
        router=DeterministicRouter(known_municipalities=names),
    )


@router.post("/assistant", response_model=AssistantResponse)
def assistant(
    body: AssistantRequest, orch: Orchestrator = Depends(get_orchestrator)
) -> AssistantResponse:
    return AssistantResponse(
        **orch.handle(
            body.message, ctx_municipality=body.municipality,
            ctx_crop_cycle_id=body.crop_cycle_id, ctx_price_per_bag=body.price_per_bag,
        )
    )
