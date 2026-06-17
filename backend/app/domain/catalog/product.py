"""Produto do catálogo de insumos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ProductCategory(str, Enum):
    FERTILIZER = "FERTILIZER"
    SEED = "SEED"
    HERBICIDE = "HERBICIDE"
    FUNGICIDE = "FUNGICIDE"
    INSECTICIDE = "INSECTICIDE"
    FOLIAR = "FOLIAR"
    ADJUVANT = "ADJUVANT"
    OTHER = "OTHER"


@dataclass
class Product:
    category: ProductCategory
    commercial_name: str
    active_ingredient: str | None = None
    formulation: str | None = None
    unit: str | None = None
    description: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.commercial_name.strip():
            raise ValueError("commercial_name não pode ser vazio")
