"""DTOs do domínio Farm / captura de ground truth."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class FarmCreate(BaseModel):
    name: str = Field(..., examples=["Fazenda Boa Vista"])
    municipality_code: int = Field(..., examples=[4309605])


class FarmOut(BaseModel):
    id: int
    name: str
    municipality_code: int
    created_at: datetime | None = None


class FieldCreate(BaseModel):
    name: str = Field(..., examples=["Talhão 1"])
    area_ha: float = Field(..., gt=0, examples=[85.0])
    latitude: float | None = None
    longitude: float | None = None


class FieldOut(BaseModel):
    id: int
    farm_id: int
    name: str
    area_ha: float
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime | None = None


class CropCycleCreate(BaseModel):
    crop: str = Field("soja", examples=["soja"])
    season: str = Field(..., examples=["2026/27"])
    area_ha: float | None = Field(None, gt=0)
    cultivar: str | None = None
    planned_planting_date: date | None = None
    actual_planting_date: date | None = None
    harvest_date: date | None = None
    actual_yield_sc_ha: float | None = Field(None, ge=0)
    notes: str | None = None


class CropCycleUpdate(BaseModel):
    """Atualização parcial da safra conforme ela progride (datas, produtividade...)."""

    area_ha: float | None = Field(None, gt=0)
    cultivar: str | None = None
    planned_planting_date: date | None = None
    actual_planting_date: date | None = None
    harvest_date: date | None = None
    actual_yield_sc_ha: float | None = Field(None, ge=0)
    notes: str | None = None


class CropCycleOut(BaseModel):
    id: int
    field_id: int
    crop: str
    season: str
    harvest_year: int
    area_ha: float | None = None
    cultivar: str | None = None
    planned_planting_date: date | None = None
    actual_planting_date: date | None = None
    harvest_date: date | None = None
    actual_yield_sc_ha: float | None = None
    notes: str | None = None
    created_at: datetime | None = None


class YieldObservationCreate(BaseModel):
    crop_cycle_id: int
    actual_yield_sc_ha: float = Field(..., ge=0, examples=[58.0])
    area_ha: float = Field(..., gt=0, examples=[85.0])
    actual_planting_date: date | None = None
    actual_harvest_date: date | None = None
    cultivar: str | None = Field(None, examples=["BMX Ícone"])
    notes: str | None = None


class YieldObservationOut(BaseModel):
    id: int
    crop_cycle_id: int
    actual_yield_sc_ha: float
    area_ha: float
    actual_planting_date: date | None = None
    actual_harvest_date: date | None = None
    cultivar: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
