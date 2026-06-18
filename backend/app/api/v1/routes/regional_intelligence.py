"""Endpoint /regional-intelligence — Camada 1, Modo Básico."""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.domain.yield_estimation import RegionalYieldModel
from app.engine import build_explainer
from app.schemas.regional_intelligence import (
    RegionalIntelligenceRequest,
    RegionalIntelligenceResponse,
)
from app.services.regional_intelligence import (
    CropNotSupported,
    InvalidSeason,
    MunicipalityNotInRegion,
    RegionalIntelligenceService,
)

router = APIRouter()


@lru_cache
def _model() -> RegionalYieldModel:
    if not settings.model_path.exists():
        raise FileNotFoundError(settings.model_path)
    return RegionalYieldModel.load(settings.model_path)


def get_service() -> RegionalIntelligenceService:
    try:
        model = _model()
    except FileNotFoundError as exc:
        raise HTTPException(503, "Modelo não treinado. Rode pipelines.train.") from exc
    return RegionalIntelligenceService(model=model, explainer=build_explainer())


@router.get("/municipalities")
def municipalities(
    service: RegionalIntelligenceService = Depends(get_service),
) -> list[dict]:
    """Municípios cobertos pelo MVP (para popular seletores no frontend)."""
    return sorted(
        ({"code": int(c), "name": i["name"]} for c, i in service.model.municipalities().items()),
        key=lambda m: m["name"],
    )


@router.post("/regional-intelligence", response_model=RegionalIntelligenceResponse)
def regional_intelligence(
    body: RegionalIntelligenceRequest,
    service: RegionalIntelligenceService = Depends(get_service),
) -> RegionalIntelligenceResponse:
    try:
        result = service.run(municipality=body.municipality, crop=body.crop, season=body.season)
    except CropNotSupported as exc:
        raise HTTPException(422, f"Cultura não suportada no MVP: {exc}. Apenas 'soja'.") from exc
    except MunicipalityNotInRegion as exc:
        raise HTTPException(
            422,
            f"Município '{exc}' fora da região do MVP (microrregião Três Passos/RS).",
        ) from exc
    except InvalidSeason as exc:
        raise HTTPException(422, f"Safra inválida: {exc}. Use o formato 'AAAA/AA'.") from exc
    return RegionalIntelligenceResponse(**result)
