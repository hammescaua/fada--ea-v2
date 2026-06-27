"""Crédito rural (Plano Safra) e comparação de 2ª safra/inverno (ADR-0030)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data.connectors.credit_store import CreditStore
from app.domain.finance import CropOption, compare_options, simulate_financing
from app.schemas.credit import (
    CompareCropsRequest,
    CompareCropsResponse,
    CreditCatalogResponse,
    CreditLineOut,
    CropMarginOut,
    FinancingRequest,
    FinancingResponse,
)

router = APIRouter()

_FIN_DISCLAIMER = (
    "Simulação determinística (sistema Price/SAC) com a taxa que você informou. "
    "Taxas e condições reais variam por linha, público e instituição — confirme com "
    "seu agente financeiro. O FADA não concede crédito."
)
_CMP_DISCLAIMER = (
    "Comparação de margem por hectare com os números que você informou (ou "
    "referências a confirmar). Não é previsão de produtividade; é a conta de quanto "
    "sobra em cada opção, lado a lado, para apoiar a decisão de 2ª safra/inverno."
)


@router.get("/credit/lines", response_model=CreditCatalogResponse)
def credit_lines_endpoint() -> CreditCatalogResponse:
    """Catálogo de referência das linhas do Plano Safra (datado e citado)."""
    store = CreditStore()
    meta = store.meta()
    return CreditCatalogResponse(
        **meta, lines=[CreditLineOut(**ln) for ln in store.lines()]
    )


@router.post("/credit/simulate", response_model=FinancingResponse)
def credit_simulate_endpoint(body: FinancingRequest) -> FinancingResponse:
    """Simula um financiamento (custeio/investimento): parcela, juros, custo total."""
    try:
        s = simulate_financing(
            body.principal, body.annual_rate_pct, body.term_months, body.system
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    per_ha = (
        {
            "principal_per_ha": round(s.principal / body.area_ha, 2),
            "total_interest_per_ha": round(s.total_interest / body.area_ha, 2),
        }
        if body.area_ha
        else {}
    )
    return FinancingResponse(**vars(s), **per_ha, disclaimer=_FIN_DISCLAIMER)


@router.post("/credit/compare-crops", response_model=CompareCropsResponse)
def credit_compare_crops_endpoint(body: CompareCropsRequest) -> CompareCropsResponse:
    """Compara margem/ha entre opções de 2ª safra/inverno (trigo, milho 2ª, etc.)."""
    try:
        margins = compare_options(
            [
                CropOption(o.name, o.yield_sc_ha, o.price_per_bag, o.cost_per_ha)
                for o in body.options
            ]
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return CompareCropsResponse(
        options=[CropMarginOut(**vars(m)) for m in margins],
        best=margins[0].name,
        disclaimer=_CMP_DISCLAIMER,
    )
