"""Endpoints de What-If de data de plantio."""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.routes.regional_intelligence import _model
from app.services.planting_date import PlantingDateService, load_grid
from app.services.regional_intelligence import (
    CropNotSupported,
    InvalidSeason,
    MunicipalityNotInRegion,
)
from app.schemas.planting_date import (
    PlantingDateSimulationRequest,
    PlantingDateSimulationResponse,
    PlantingWindowOptimizationRequest,
    PlantingWindowOptimizationResponse,
)

router = APIRouter()


@lru_cache
def _service() -> PlantingDateService:
    return PlantingDateService(model=_model(), grid=load_grid())


def get_service() -> PlantingDateService:
    try:
        return _service()
    except FileNotFoundError as exc:
        raise HTTPException(503, "Modelo/grid ausente. Rode pipelines.train e "
                                 "pipelines.build_planting_grid.") from exc


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, CropNotSupported):
        return HTTPException(422, f"Cultura não suportada no MVP: {exc}. Apenas 'soja'.")
    if isinstance(exc, MunicipalityNotInRegion):
        return HTTPException(422, f"Município '{exc}' fora da região do MVP "
                                  "(microrregião Três Passos/RS).")
    if isinstance(exc, (InvalidSeason, ValueError)):
        return HTTPException(422, f"Entrada inválida: {exc}.")
    raise exc


@router.post("/planting-date-simulation", response_model=PlantingDateSimulationResponse)
def planting_date_simulation(
    body: PlantingDateSimulationRequest,
    service: PlantingDateService = Depends(get_service),
) -> PlantingDateSimulationResponse:
    try:
        result = service.simulate(
            municipality=body.municipality, crop=body.crop, season=body.season,
            planting_date=body.planting_date, risk_aversion=body.risk_aversion,
        )
    except Exception as exc:  # noqa: BLE001
        raise _handle(exc) from exc
    return PlantingDateSimulationResponse(**result)


@router.post("/planting-window-optimization", response_model=PlantingWindowOptimizationResponse)
def planting_window_optimization(
    body: PlantingWindowOptimizationRequest,
    service: PlantingDateService = Depends(get_service),
) -> PlantingWindowOptimizationResponse:
    try:
        result = service.optimize(
            municipality=body.municipality, crop=body.crop, season=body.season,
            risk_aversion=body.risk_aversion, top_n=body.top_n,
        )
    except Exception as exc:  # noqa: BLE001
        raise _handle(exc) from exc
    return PlantingWindowOptimizationResponse(**result)
