"""Endpoint do Cartão de Decisão — hub unificado (guia §4 / Fatia 2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.routes.regional_intelligence import _model
from app.api.v1.routes.season_planning import get_season_service
from app.infra.db import get_session
from app.infra.repositories import (
    AgronomicProfileRepository,
    EventRepository,
    FarmRepository,
    PlanningRepository,
)
from app.schemas.decision_card import (
    DecisionCardOut,
    DecisionCardsResponse,
    DecisionEffectOut,
    EvidenceOut,
)
from app.services.decision_cards import DecisionCardService
from app.services.decisions import DecisionsService
from app.services.insights import InsightsService
from app.services.weather import WeatherService

router = APIRouter()


def get_card_service(session: Session = Depends(get_session)) -> DecisionCardService:
    try:
        model = _model()
    except FileNotFoundError as exc:
        raise HTTPException(503, "Modelo ausente.") from exc
    farms = FarmRepository(session)
    events = EventRepository(session)
    decisions = DecisionsService(
        farms=farms, events=events, planning=PlanningRepository(session), model=model,
        insights=InsightsService(farms=farms, events=events, model=model),
    )
    return DecisionCardService(
        farms=farms,
        profiles=AgronomicProfileRepository(session),
        model=model,
        weather=WeatherService(farms=farms),
        decisions=decisions,
        season=get_season_service(),
    )


@router.get("/farms/{farm_id}/decision-cards", response_model=DecisionCardsResponse)
def decision_cards_endpoint(
    farm_id: int,
    field_id: int | None = Query(None, description="Talhão (habilita cartões de manejo)"),
    season: str = Query("2026/27"),
    svc: DecisionCardService = Depends(get_card_service),
) -> DecisionCardsResponse:
    if svc.farms.get_farm(farm_id) is None:
        raise HTTPException(404, f"Fazenda {farm_id} inexistente.")
    cards = svc.cards(farm_id, field_id, season)
    return DecisionCardsResponse(
        farm_id=farm_id,
        field_id=field_id,
        n_cards=len(cards),
        cards=[
            DecisionCardOut(
                id=c.id, source=c.source, decision=c.decision,
                recommendation=c.recommendation, confidence=c.confidence,
                horizon=c.horizon, disclaimer=c.disclaimer, n_data=c.n_data,
                severity=c.severity,
                effect=(
                    DecisionEffectOut(
                        basis=c.effect.basis,
                        yield_sc_ha=c.effect.yield_sc_ha,
                        profit_brl_ha=c.effect.profit_brl_ha,
                    )
                    if c.effect else None
                ),
                why=[EvidenceOut(label=e.label, detail=e.detail) for e in c.why],
            )
            for c in cards
        ],
        note="Cartões de decisão unificados: clima (proativo), manejo (efeito em "
             "R$/ha) e histórico (atenção). Cada efeito vem com intervalo; previsão "
             "e estimativas nunca como certeza.",
    )
