"""Endpoint de planejamento de safra (brief de decisão pré-safra).

Agrega serviços determinísticos. O payload reúne dataclasses (cenários, custos) e
seções opcionais; deixamos o ``jsonable_encoder`` do FastAPI serializar — por isso
sem ``response_model`` rígido (é um endpoint de composição).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.routes.planting_date import _service as _planting_service
from app.api.v1.routes.regional_intelligence import get_service as _regional_service
from app.data.connectors.zarc_store import ZarcStore
from app.services.benchmark import BenchmarkService
from app.services.market import MarketService
from app.services.regional_intelligence import (
    CropNotSupported,
    InvalidSeason,
    MunicipalityNotInRegion,
)
from app.services.season_planning import SeasonPlanningService
from app.services.zarc import ZarcService

router = APIRouter()


def get_season_service() -> SeasonPlanningService:
    return SeasonPlanningService(
        regional=_regional_service(),
        planting=_planting_service(),
        zarc=ZarcService(store=ZarcStore()),
        market=MarketService(),
        benchmark=BenchmarkService(),
    )


@router.get("/planning/season-brief")
def season_brief_endpoint(
    municipality: str = Query(..., description="Município (ex.: Horizontina)"),
    crop: str = Query("soja"),
    season: str = Query("2026/27"),
    uf: str = Query("RS"),
    price_per_bag: float | None = Query(
        None, gt=0, description="Preço opcional; se omitido, usa CEPEA ao vivo."
    ),
    svc: SeasonPlanningService = Depends(get_season_service),
) -> dict:
    try:
        return svc.brief(municipality, crop, season, uf, price_per_bag)
    except MunicipalityNotInRegion as exc:
        raise HTTPException(404, f"Município '{municipality}' fora da região coberta.") from exc
    except CropNotSupported as exc:
        raise HTTPException(422, f"Cultura não suportada: {exc}.") from exc
    except InvalidSeason as exc:
        raise HTTPException(422, f"Safra inválida: {exc}.") from exc
