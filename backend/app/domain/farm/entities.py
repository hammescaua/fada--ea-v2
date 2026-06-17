"""Entidades do domínio Farm (puras, com invariantes mínimas)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Season:
    """Value Object: safra como rótulo + ano de colheita (ex.: '2026/27' -> 2027)."""

    label: str
    harvest_year: int

    @classmethod
    def parse(cls, label: str) -> Season:
        first = label.split("/")[0].strip()
        year = int(first)
        return cls(label=label, harvest_year=year + 1 if "/" in label else year)


@dataclass
class Farm:
    name: str
    municipality_code: int
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Farm.name não pode ser vazio")


@dataclass
class Field:
    """Talhão (subdivisão de manejo de uma fazenda)."""

    farm_id: int
    name: str
    area_ha: float
    latitude: float | None = None
    longitude: float | None = None
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.area_ha <= 0:
            raise ValueError("Field.area_ha deve ser positivo")


@dataclass
class CropCycle:
    """Uma safra completa em um talhão — raiz do agregado de eventos agrícolas.

    Datas canônicas e produtividade vivem aqui (não nos eventos). Os eventos
    PLANTING/HARVEST capturam apenas custo/insumos dessas operações (ADR-0011).
    """

    field_id: int
    crop: str
    season: Season
    area_ha: float | None = None
    cultivar: str | None = None
    planned_planting_date: date | None = None
    actual_planting_date: date | None = None
    harvest_date: date | None = None
    actual_yield_sc_ha: float | None = None
    notes: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.area_ha is not None and self.area_ha <= 0:
            raise ValueError("CropCycle.area_ha deve ser positivo")
        if self.actual_yield_sc_ha is not None and self.actual_yield_sc_ha < 0:
            raise ValueError("actual_yield_sc_ha não pode ser negativo")
        if (
            self.actual_planting_date
            and self.harvest_date
            and self.harvest_date < self.actual_planting_date
        ):
            raise ValueError("colheita não pode ser anterior ao plantio")


@dataclass
class YieldObservation:
    """Ground truth informado pelo produtor — o ativo do flywheel.

    Nunca é sobrescrito por estimativa e (por ora) não alimenta treino (ADR-0009).
    """

    crop_cycle_id: int
    actual_yield_sc_ha: float
    area_ha: float
    actual_planting_date: date | None = None
    actual_harvest_date: date | None = None
    cultivar: str | None = None
    notes: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.actual_yield_sc_ha < 0:
            raise ValueError("actual_yield_sc_ha não pode ser negativo")
        if self.area_ha <= 0:
            raise ValueError("area_ha deve ser positivo")
        if (
            self.actual_planting_date
            and self.actual_harvest_date
            and self.actual_harvest_date < self.actual_planting_date
        ):
            raise ValueError("colheita não pode ser anterior ao plantio")
