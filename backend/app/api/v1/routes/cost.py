"""Endpoints financeiros (Cost Engine)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.routes.regional_intelligence import _model
from app.infra.db import get_session
from app.infra.repositories import EventRepository, FarmRepository
from app.schemas.benchmark import (
    CostBenchmarkComparisonResponse,
    CostComparisonOut,
    CostComponentOut,
)
from app.schemas.cost import (
    CostBreakdownOut,
    FinancialsRequest,
    FinancialsResponse,
    ScenarioResultOut,
)
from app.services.benchmark import BenchmarkService, BenchmarkUnavailable
from app.services.cost import AreaUnknown, CostService, CycleNotFound, PriceUnknown
from app.services.market import MarketService

router = APIRouter()


def get_cost_service(session: Session = Depends(get_session)) -> CostService:
    return CostService(
        farms=FarmRepository(session),
        events=EventRepository(session),
        model=_model(),
        market=MarketService(),
    )


def get_benchmark_service() -> BenchmarkService:
    return BenchmarkService()


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, CycleNotFound):
        return HTTPException(404, f"CropCycle {exc} inexistente")
    if isinstance(exc, AreaUnknown):
        return HTTPException(
            422, "Área desconhecida: informe area_ha no CropCycle ou no Field."
        )
    if isinstance(exc, PriceUnknown):
        return HTTPException(
            422,
            "Sem preço: informe price_per_bag, cadastre o preço esperado na safra, "
            "ou rode o pipeline de cotação (build_market_snapshot).",
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
    except (CycleNotFound, AreaUnknown, PriceUnknown) as exc:
        raise _handle(exc) from exc
    return FinancialsResponse(
        breakdown=CostBreakdownOut(**vars(result["breakdown"])),
        price_per_bag=result["price_per_bag"],
        price_source=result["price_source"],
        break_even_yield_sc_ha=result["break_even_yield_sc_ha"],
        yield_source=result["yield_source"],
        scenarios=[ScenarioResultOut(**vars(s)) for s in result["scenarios"]],
    )


@router.get(
    "/crop-cycles/{cycle_id}/cost-benchmark",
    response_model=CostBenchmarkComparisonResponse,
)
def cost_benchmark_comparison_endpoint(
    cycle_id: int,
    svc: CostService = Depends(get_cost_service),
    bench: BenchmarkService = Depends(get_benchmark_service),
) -> CostBenchmarkComparisonResponse:
    try:
        breakdown, crop, uf = svc.cost_context(cycle_id)
    except (CycleNotFound, AreaUnknown) as exc:
        raise _handle(exc) from exc
    if uf is None:
        raise HTTPException(422, "UF do município desconhecida para o benchmark.")
    try:
        data = bench.compare_cost(breakdown.cost_per_hectare, crop, uf)
    except BenchmarkUnavailable as exc:
        raise HTTPException(
            404,
            f"Sem benchmark de custo para '{crop}/{uf}'. Rode o pipeline "
            "build_cost_benchmark para popular o artefato.",
        ) from exc
    return CostBenchmarkComparisonResponse(
        **{k: data[k] for k in (
            "crop", "uf", "safra", "technology", "source", "fetched_at",
            "coe_per_ha", "cot_per_ha", "ct_per_ha", "actual_cost_per_ha",
            "primary", "disclaimer",
        )},
        references={k: CostComparisonOut(**vars(v)) for k, v in data["references"].items()},
        components=[CostComponentOut(**vars(c)) for c in data["components"]],
    )
