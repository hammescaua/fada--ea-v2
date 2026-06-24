"""Endpoints ZARC (janela oficial de plantio do MAPA)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.routes.regional_intelligence import _model
from app.data.connectors.zarc_store import ZarcStore
from app.schemas.zarc import WindowOut, ZarcWindowResponse
from app.services.zarc import MunicipalityNotInZarc, ZarcService, ZarcUnavailable

router = APIRouter()


def get_zarc_service() -> ZarcService:
    return ZarcService(store=ZarcStore())


def _resolve_code(municipality: str) -> tuple[int, str]:
    """Resolve nome -> (código, nome canônico) pela climatologia do modelo regional."""
    target = municipality.strip().lower()
    for code, info in _model().municipalities().items():
        if info["name"].lower() == target:
            return int(code), info["name"]
    raise HTTPException(404, f"Município '{municipality}' fora da região coberta.")


@router.get("/zarc/planting-window", response_model=ZarcWindowResponse)
def zarc_planting_window_endpoint(
    municipality: str = Query(..., description="Nome do município (ex.: Horizontina)"),
    crop: str = Query("soja"),
    uf: str = Query("RS"),
    planting_date: date | None = Query(
        None, description="Data opcional para verificar se está dentro do ZARC"
    ),
    svc: ZarcService = Depends(get_zarc_service),
) -> ZarcWindowResponse:
    code, _ = _resolve_code(municipality)
    try:
        if planting_date is not None:
            data = svc.evaluate_date(code, planting_date, crop, uf)
        else:
            data = svc.planting_window(code, crop, uf)
    except ZarcUnavailable as exc:
        raise HTTPException(
            404,
            f"Sem janela ZARC para '{crop}/{uf}'. Rode o pipeline build_zarc_windows.",
        ) from exc
    except MunicipalityNotInZarc as exc:
        raise HTTPException(404, f"Município sem janela ZARC distilada ({exc}).") from exc

    return ZarcWindowResponse(
        **{k: data[k] for k in (
            "crop", "uf", "safra", "manejo", "portaria", "source", "fetched_at",
            "note", "municipality_code", "municipality_name", "disclaimer",
        )},
        windows_by_risk={
            risk: [WindowOut(**w) for w in wins]
            for risk, wins in data["windows_by_risk"].items()
        },
        planting_date=data.get("planting_date"),
        within_zarc=data.get("within_zarc"),
        risk_level=data.get("risk_level"),
        interpretation=data.get("interpretation"),
    )
