"""Endpoints de mercado (preço observado de fonte oficial)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.benchmark import CostBenchmarkResponse, CostComponentOut
from app.schemas.market import MarketPriceResponse, PricePointOut, PriceSummaryOut
from app.services.benchmark import BenchmarkService, BenchmarkUnavailable
from app.services.market import MarketService, PriceUnavailable

router = APIRouter()


def get_market_service() -> MarketService:
    return MarketService()


def get_benchmark_service() -> BenchmarkService:
    return BenchmarkService()


@router.get("/market/price", response_model=MarketPriceResponse)
def market_price_endpoint(
    crop: str = Query("soja", description="Cultura (ex.: soja)"),
    svc: MarketService = Depends(get_market_service),
) -> MarketPriceResponse:
    try:
        data = svc.price(crop)
    except PriceUnavailable as exc:
        raise HTTPException(
            404,
            f"Sem cotação coletada para '{crop}'. Rode o pipeline "
            "build_market_snapshot para popular o artefato.",
        ) from exc
    s = data["summary"]
    return MarketPriceResponse(
        crop=data["crop"],
        source=data["source"],
        place=data["place"],
        unit=data["unit"],
        fetched_at=data["fetched_at"],
        summary=PriceSummaryOut(**vars(s)),
        series=[PricePointOut(day=p.day, value=p.value) for p in data["series"]],
        disclaimer=data["disclaimer"],
    )


@router.get("/market/cost-benchmark", response_model=CostBenchmarkResponse)
def cost_benchmark_endpoint(
    crop: str = Query("soja", description="Cultura (ex.: soja)"),
    uf: str = Query("RS", description="UF (ex.: RS)"),
    svc: BenchmarkService = Depends(get_benchmark_service),
) -> CostBenchmarkResponse:
    try:
        data = svc.cost_benchmark(crop, uf)
    except BenchmarkUnavailable as exc:
        raise HTTPException(
            404,
            f"Sem benchmark de custo para '{crop}/{uf}'. Rode o pipeline "
            "build_cost_benchmark para popular o artefato.",
        ) from exc
    return CostBenchmarkResponse(
        **{k: data[k] for k in (
            "crop", "uf", "safra", "technology", "source", "fetched_at",
            "coe_per_ha", "cot_per_ha", "ct_per_ha", "disclaimer",
        )},
        components=[CostComponentOut(**vars(c)) for c in data["components"]],
    )

