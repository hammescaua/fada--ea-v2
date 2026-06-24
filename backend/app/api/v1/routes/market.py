"""Endpoints de mercado (preço observado de fonte oficial)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.market import MarketPriceResponse, PricePointOut, PriceSummaryOut
from app.services.market import MarketService, PriceUnavailable

router = APIRouter()


def get_market_service() -> MarketService:
    return MarketService()


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
