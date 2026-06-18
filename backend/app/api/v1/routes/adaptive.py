"""Endpoints de Adaptive Farm Intelligence."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.routes.regional_intelligence import _model
from app.infra.db import get_session
from app.infra.repositories import AdaptiveRepository, FarmRepository
from app.schemas.adaptive import (
    FarmProfileOut,
    PersonalizedIntelligenceRequest,
    PersonalizedIntelligenceResponse,
)
from app.services.adaptive import AdaptiveService, FarmNotFound
from app.services.regional_intelligence import MunicipalityNotInRegion

router = APIRouter()


def get_service(session: Session = Depends(get_session)) -> AdaptiveService:
    try:
        model = _model()
    except FileNotFoundError as exc:
        raise HTTPException(503, "Modelo ausente.") from exc
    return AdaptiveService(
        farms=FarmRepository(session), adaptive=AdaptiveRepository(session), model=model
    )


def _profile_out(svc: AdaptiveService, profile, farm_id: int) -> FarmProfileOut:
    return FarmProfileOut(
        farm_id=profile.farm_id, number_of_cycles=profile.number_of_cycles,
        bias_percentage=profile.bias_percentage,
        mean_relative_residual=round(profile.mean_relative_residual, 4),
        mean_residual_sc_ha=round(profile.mean_residual_sc_ha, 1),
        median_residual_sc_ha=round(profile.median_residual_sc_ha, 1),
        variance_relative=round(profile.variance_relative, 4),
        last_updated=profile.last_updated,
        residual_history=svc.residual_history(farm_id),
    )


@router.post("/farms/{farm_id}/performance-profile/recompute", response_model=FarmProfileOut)
def recompute_profile(
    farm_id: int, svc: AdaptiveService = Depends(get_service)
) -> FarmProfileOut:
    try:
        profile = svc.recompute_profile(farm_id)
    except FarmNotFound as exc:
        raise HTTPException(404, f"Farm {exc} inexistente") from exc
    return _profile_out(svc, profile, farm_id)


@router.get("/farms/{farm_id}/performance-profile", response_model=FarmProfileOut)
def get_profile(farm_id: int, svc: AdaptiveService = Depends(get_service)) -> FarmProfileOut:
    profile = svc.adaptive.get_profile(farm_id)
    if profile is None:
        raise HTTPException(404, "Perfil ainda não computado. Use /recompute.")
    return _profile_out(svc, profile, farm_id)


@router.post("/personalized-intelligence", response_model=PersonalizedIntelligenceResponse)
def personalized_intelligence(
    body: PersonalizedIntelligenceRequest, svc: AdaptiveService = Depends(get_service)
) -> PersonalizedIntelligenceResponse:
    try:
        result = svc.personalized_intelligence(body.farm_id, body.season)
    except FarmNotFound as exc:
        raise HTTPException(404, f"Farm {exc} inexistente") from exc
    except MunicipalityNotInRegion as exc:
        raise HTTPException(422, f"Município fora da região do MVP: {exc}.") from exc
    except KeyError as exc:
        raise HTTPException(
            422, "Município da fazenda fora da região coberta pelo modelo."
        ) from exc
    return PersonalizedIntelligenceResponse(**result)
