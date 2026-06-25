"""Endpoints do Perfil Agronômico (estimativa personalizada a priori)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.routes.regional_intelligence import _model
from app.api.v1.routes.regional_intelligence import get_service as _regional_service
from app.data.connectors.zarc_store import ZarcStore
from app.domain.agronomy import (
    SoilAnalysis,
    UnknownFactor,
    classify_soil_analysis,
    planting_window_class,
    validate_profile,
)
from app.infra.db import get_session
from app.infra.repositories import AgronomicProfileRepository, FarmRepository
from app.schemas.agronomic import (
    AgronomicEstimateRequest,
    AgronomicEstimateResponse,
    AgronomicProfileResponse,
    FactorOut,
    SaveProfileRequest,
    SoilAnalysisRequest,
    SoilAnalysisResponse,
    SoilClassificationNote,
)
from app.services.agronomic import AgronomicService
from app.services.regional_intelligence import (
    CropNotSupported,
    InvalidSeason,
    MunicipalityNotInRegion,
)
from app.services.zarc import MunicipalityNotInZarc, ZarcService, ZarcUnavailable

router = APIRouter()


def get_agronomic_service() -> AgronomicService:
    return AgronomicService(regional=_regional_service())


def _municipality_name(code: int) -> str:
    info = _model().municipalities().get(str(code))
    if info is None:
        raise HTTPException(404, f"Município {code} fora da região coberta pelo modelo.")
    return info["name"]


@router.get("/agronomic/factors", response_model=list[FactorOut])
def agronomic_factors_endpoint(
    svc: AgronomicService = Depends(get_agronomic_service),
) -> list[FactorOut]:
    return [FactorOut(**f) for f in svc.factors_catalog()]


@router.get("/agronomic/planting-window-class")
def planting_window_class_endpoint(
    planting_date: date = Query(..., description="Data de plantio pretendida"),
    municipality: str | None = Query(None),
    field_id: int | None = Query(None),
    crop: str = Query("soja"),
    uf: str = Query("RS"),
    session: Session = Depends(get_session),
) -> dict:
    """Classifica a data de plantio (ZARC oficial) no fator 'janela_plantio'."""
    code = _resolve_code(municipality, field_id, session)
    zarc = ZarcService(store=ZarcStore())
    try:
        ev = zarc.evaluate_date(code, planting_date, crop, uf)
    except (ZarcUnavailable, MunicipalityNotInZarc) as exc:
        raise HTTPException(404, f"Sem janela ZARC para o município ({exc}).") from exc
    value = planting_window_class(ev["within_zarc"], ev["risk_level"])
    return {
        "profile_fragment": {"janela_plantio": value},
        "within_zarc": ev["within_zarc"],
        "risk_level": ev["risk_level"],
        "basis": ev["interpretation"],
    }


def _resolve_code(municipality: str | None, field_id: int | None, session: Session) -> int:
    """Resolve o código do município por nome OU pelo talhão (deriva da fazenda)."""
    if field_id is not None:
        field = FarmRepository(session).get_field(field_id)
        if field is None:
            raise HTTPException(404, f"Talhão {field_id} inexistente.")
        farm = FarmRepository(session).get_farm(field.farm_id)
        if _model().municipalities().get(str(farm.municipality_code)) is None:
            raise HTTPException(404, "Município do talhão fora da região coberta.")
        return farm.municipality_code
    if municipality is not None:
        target = municipality.strip().lower()
        for c, info in _model().municipalities().items():
            if info["name"].lower() == target:
                return int(c)
        raise HTTPException(404, f"Município '{municipality}' fora da região.")
    raise HTTPException(422, "Informe municipality ou field_id.")


@router.post("/agronomic/soil-analysis", response_model=SoilAnalysisResponse)
def soil_analysis_endpoint(body: SoilAnalysisRequest) -> SoilAnalysisResponse:
    """Classifica um laudo de análise de solo (CQFS-RS/SC) em fatores do perfil."""
    fragment, notes = classify_soil_analysis(SoilAnalysis(**body.model_dump()))
    return SoilAnalysisResponse(
        profile_fragment=fragment,
        notes=[SoilClassificationNote(**n) for n in notes],
        disclaimer=(
            "Classificação orientativa segundo CQFS-RS/SC (2016), ancorada no teor "
            "crítico. Confirme a recomendação com seu agrônomo. Você pode ajustar "
            "qualquer fator manualmente."
        ),
    )


@router.post("/agronomic/estimate", response_model=AgronomicEstimateResponse)
def agronomic_estimate_endpoint(
    body: AgronomicEstimateRequest,
    svc: AgronomicService = Depends(get_agronomic_service),
) -> AgronomicEstimateResponse:
    try:
        data = svc.personalized_estimate(
            body.municipality, body.crop, body.season, body.profile
        )
    except UnknownFactor as exc:
        raise HTTPException(422, f"Perfil inválido: {exc}") from exc
    except MunicipalityNotInRegion as exc:
        raise HTTPException(404, f"Município '{body.municipality}' fora da região.") from exc
    except CropNotSupported as exc:
        raise HTTPException(422, f"Cultura não suportada: {exc}.") from exc
    except InvalidSeason as exc:
        raise HTTPException(422, f"Safra inválida: {exc}.") from exc
    return AgronomicEstimateResponse(**data)


# -- Perfil persistido por talhão (capturar uma vez, reusar) ----------------

@router.get("/fields/{field_id}/agronomic-profile", response_model=AgronomicProfileResponse)
def get_field_profile_endpoint(
    field_id: int, session: Session = Depends(get_session)
) -> AgronomicProfileResponse:
    if FarmRepository(session).get_field(field_id) is None:
        raise HTTPException(404, f"Talhão {field_id} inexistente.")
    profile = AgronomicProfileRepository(session).get(field_id) or {}
    return AgronomicProfileResponse(field_id=field_id, profile=profile)


@router.put("/fields/{field_id}/agronomic-profile", response_model=AgronomicProfileResponse)
def save_field_profile_endpoint(
    field_id: int, body: SaveProfileRequest, session: Session = Depends(get_session)
) -> AgronomicProfileResponse:
    try:
        validate_profile(body.profile)
    except UnknownFactor as exc:
        raise HTTPException(422, f"Perfil inválido: {exc}") from exc
    try:
        saved = AgronomicProfileRepository(session).upsert(field_id, body.profile)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return AgronomicProfileResponse(field_id=field_id, profile=saved)


@router.get("/fields/{field_id}/estimate", response_model=AgronomicEstimateResponse)
def field_estimate_endpoint(
    field_id: int,
    season: str = Query("2026/27"),
    crop: str = Query("soja"),
    session: Session = Depends(get_session),
    svc: AgronomicService = Depends(get_agronomic_service),
) -> AgronomicEstimateResponse:
    farms = FarmRepository(session)
    field = farms.get_field(field_id)
    if field is None:
        raise HTTPException(404, f"Talhão {field_id} inexistente.")
    farm = farms.get_farm(field.farm_id)
    municipality = _municipality_name(farm.municipality_code)
    profile = AgronomicProfileRepository(session).get(field_id) or {}
    try:
        data = svc.personalized_estimate(municipality, crop, season, profile)
    except (CropNotSupported, InvalidSeason) as exc:
        raise HTTPException(422, str(exc)) from exc
    except MunicipalityNotInRegion as exc:
        raise HTTPException(404, str(exc)) from exc
    return AgronomicEstimateResponse(**data)
