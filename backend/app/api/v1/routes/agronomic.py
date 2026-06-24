"""Endpoints do Perfil Agronômico (estimativa personalizada a priori)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.routes.regional_intelligence import get_service as _regional_service
from app.domain.agronomy import UnknownFactor
from app.schemas.agronomic import (
    AgronomicEstimateRequest,
    AgronomicEstimateResponse,
    FactorOut,
)
from app.services.agronomic import AgronomicService
from app.services.regional_intelligence import (
    CropNotSupported,
    InvalidSeason,
    MunicipalityNotInRegion,
)

router = APIRouter()


def get_agronomic_service() -> AgronomicService:
    return AgronomicService(regional=_regional_service())


@router.get("/agronomic/factors", response_model=list[FactorOut])
def agronomic_factors_endpoint(
    svc: AgronomicService = Depends(get_agronomic_service),
) -> list[FactorOut]:
    return [FactorOut(**f) for f in svc.factors_catalog()]


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
