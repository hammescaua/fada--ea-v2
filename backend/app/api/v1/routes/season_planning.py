"""Endpoint de planejamento de safra (brief de decisão pré-safra).

Agrega serviços determinísticos. O payload reúne dataclasses (cenários, custos) e
seções opcionais; deixamos o ``jsonable_encoder`` do FastAPI serializar — por isso
sem ``response_model`` rígido (é um endpoint de composição).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.routes.planting_date import _service as _planting_service
from app.api.v1.routes.regional_intelligence import _model
from app.api.v1.routes.regional_intelligence import get_service as _regional_service
from app.data.connectors.zarc_store import ZarcStore
from app.infra.db import get_session
from app.infra.repositories import AgronomicProfileRepository, FarmRepository
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
    municipality: str | None = Query(None, description="Município (ex.: Horizontina)"),
    field_id: int | None = Query(
        None, description="Talhão: usa seu perfil agronômico e deriva o município."
    ),
    crop: str = Query("soja"),
    season: str = Query("2026/27"),
    uf: str = Query("RS"),
    price_per_bag: float | None = Query(
        None, gt=0, description="Preço opcional; se omitido, usa CEPEA ao vivo."
    ),
    session: Session = Depends(get_session),
    svc: SeasonPlanningService = Depends(get_season_service),
) -> dict:
    profile: dict | None = None
    # Talhão tem prioridade: deriva município e carrega o perfil para personalizar.
    if field_id is not None:
        field = FarmRepository(session).get_field(field_id)
        if field is None:
            raise HTTPException(404, f"Talhão {field_id} inexistente.")
        farm = FarmRepository(session).get_farm(field.farm_id)
        info = _model().municipalities().get(str(farm.municipality_code))
        if info is None:
            raise HTTPException(404, "Município do talhão fora da região coberta.")
        municipality = info["name"]
        profile = AgronomicProfileRepository(session).get(field_id) or None
    if municipality is None:
        raise HTTPException(422, "Informe municipality ou field_id.")
    try:
        return svc.brief(municipality, crop, season, uf, price_per_bag, profile)
    except MunicipalityNotInRegion as exc:
        raise HTTPException(404, f"Município '{municipality}' fora da região coberta.") from exc
    except CropNotSupported as exc:
        raise HTTPException(422, f"Cultura não suportada: {exc}.") from exc
    except InvalidSeason as exc:
        raise HTTPException(422, f"Safra inválida: {exc}.") from exc
