"""DTOs de crédito rural e comparação de 2ª safra (ADR-0030)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreditLineOut(BaseModel):
    key: str
    name: str
    purpose: str
    audience: str
    ref_rate_pct_year: list[float]
    limit: str | None = None
    note: str | None = None


class CreditCatalogResponse(BaseModel):
    source: str | None = None
    fetched_at: str | None = None
    safra: str | None = None
    vigencia: str | None = None
    note: str | None = None
    lines: list[CreditLineOut]


class FinancingRequest(BaseModel):
    principal: float = Field(..., gt=0, description="Valor financiado (R$)")
    annual_rate_pct: float = Field(..., ge=0, description="Taxa de juros anual (%)")
    term_months: int = Field(..., gt=0, le=600, description="Prazo em meses")
    system: str = Field("price", description="'price' (parcela fixa) ou 'sac'")
    area_ha: float | None = Field(None, gt=0, description="Área (ha) p/ custo por hectare")


class FinancingResponse(BaseModel):
    principal: float
    annual_rate_pct: float
    term_months: int
    system: str
    first_installment: float
    last_installment: float
    total_paid: float
    total_interest: float
    interest_over_principal_pct: float
    principal_per_ha: float | None = None
    total_interest_per_ha: float | None = None
    disclaimer: str


class CropOptionIn(BaseModel):
    name: str
    yield_sc_ha: float = Field(..., ge=0)
    price_per_bag: float = Field(..., ge=0)
    cost_per_ha: float = Field(..., ge=0)


class CompareCropsRequest(BaseModel):
    options: list[CropOptionIn] = Field(..., min_length=1)


class CropMarginOut(BaseModel):
    name: str
    revenue_per_ha: float
    cost_per_ha: float
    margin_per_ha: float
    break_even_sc_ha: float | None
    rank: int
    delta_vs_best_per_ha: float


class CompareCropsResponse(BaseModel):
    options: list[CropMarginOut]
    best: str
    disclaimer: str
