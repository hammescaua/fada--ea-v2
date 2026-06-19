"""Casos de uso de captura de ground truth (Digital Twin foundational + flywheel).

Apenas captura e persiste. Nenhum uso em treino nesta fase (ADR-0009).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.farm import CropCycle, Farm, Field, Season, YieldObservation
from app.infra.repositories import FarmRepository


@dataclass
class FarmService:
    repo: FarmRepository

    def create_farm(self, name: str, municipality_code: int) -> Farm:
        return self.repo.add_farm(Farm(name=name, municipality_code=municipality_code))

    def list_farms(self) -> list[Farm]:
        return self.repo.list_farms()

    def create_field(
        self, farm_id: int, name: str, area_ha: float,
        latitude: float | None = None, longitude: float | None = None,
    ) -> Field:
        return self.repo.add_field(
            Field(farm_id=farm_id, name=name, area_ha=area_ha,
                  latitude=latitude, longitude=longitude)
        )

    def list_fields(self, farm_id: int) -> list[Field]:
        return self.repo.list_fields(farm_id)

    def list_cycles(self, farm_id: int) -> list[CropCycle]:
        return self.repo.list_cycles_by_farm(farm_id)

    def create_cycle(self, field_id: int, crop: str, season: str, **fields) -> CropCycle:
        return self.repo.add_cycle(
            CropCycle(field_id=field_id, crop=crop, season=Season.parse(season), **fields)
        )

    def get_cycle(self, cycle_id: int) -> CropCycle | None:
        return self.repo.get_cycle(cycle_id)

    def update_cycle(self, cycle_id: int, changes: dict) -> CropCycle:
        # valida invariantes reconstruindo a entidade após aplicar mudanças
        current = self.repo.get_cycle(cycle_id)
        if current is None:
            raise LookupError(f"CropCycle {cycle_id} inexistente")
        for k, v in changes.items():
            setattr(current, k, v)
        current.__post_init__()  # revalida (datas/área/produtividade)
        return self.repo.update_cycle(cycle_id, changes)

    def record_observation(self, **kwargs) -> YieldObservation:
        return self.repo.add_observation(YieldObservation(**kwargs))

    def list_observations(self) -> list[YieldObservation]:
        return self.repo.list_observations()
