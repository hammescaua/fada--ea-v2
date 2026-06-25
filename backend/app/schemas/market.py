"""DTOs de mercado (preço observado)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class PricePointOut(BaseModel):
    day: date
    value: float


class PriceSummaryOut(BaseModel):
    latest_value: float
    latest_day: date
    n_points: int
    window_days: int
    mean_value: float
    min_value: float
    max_value: float
    change_pct: float
    staleness_days: int
    is_stale: bool


class MarketPriceResponse(BaseModel):
    crop: str
    source: str
    place: str
    unit: str
    fetched_at: date
    summary: PriceSummaryOut
    series: list[PricePointOut]
    disclaimer: str
