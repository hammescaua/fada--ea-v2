"""Repositórios: mapeiam ORM <-> entidades de domínio. Domínio nunca vê SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.catalog import Product, ProductCategory
from app.domain.farm import (
    AgriculturalEvent,
    CropCycle,
    EventType,
    Farm,
    Field,
    Season,
    YieldObservation,
)
from app.infra.models import (
    AgriculturalEventORM,
    CropCycleORM,
    FarmORM,
    FieldORM,
    ProductORM,
    YieldObservationORM,
)


def _farm(o: FarmORM) -> Farm:
    return Farm(id=o.id, name=o.name, municipality_code=o.municipality_code,
                created_at=o.created_at)


def _field(o: FieldORM) -> Field:
    return Field(id=o.id, farm_id=o.farm_id, name=o.name, area_ha=o.area_ha,
                 latitude=o.latitude, longitude=o.longitude, created_at=o.created_at)


def _cycle(o: CropCycleORM) -> CropCycle:
    return CropCycle(
        id=o.id, field_id=o.field_id, crop=o.crop,
        season=Season(o.season_label, o.harvest_year),
        area_ha=o.area_ha, cultivar=o.cultivar,
        planned_planting_date=o.planned_planting_date,
        actual_planting_date=o.actual_planting_date,
        harvest_date=o.harvest_date, actual_yield_sc_ha=o.actual_yield_sc_ha,
        notes=o.notes, created_at=o.created_at,
    )


def _event(o: AgriculturalEventORM) -> AgriculturalEvent:
    return AgriculturalEvent(
        id=o.id, crop_cycle_id=o.crop_cycle_id, event_type=EventType(o.event_type),
        event_date=o.event_date, product_name=o.product_name, product_id=o.product_id,
        quantity=o.quantity, unit=o.unit, cost=o.cost, notes=o.notes,
        created_at=o.created_at,
    )


def _product(o: ProductORM) -> Product:
    return Product(
        id=o.id, category=ProductCategory(o.category), commercial_name=o.commercial_name,
        active_ingredient=o.active_ingredient, formulation=o.formulation,
        unit=o.unit, description=o.description, created_at=o.created_at,
    )


def _obs(o: YieldObservationORM) -> YieldObservation:
    return YieldObservation(
        id=o.id, crop_cycle_id=o.crop_cycle_id, actual_yield_sc_ha=o.actual_yield_sc_ha,
        area_ha=o.area_ha, actual_planting_date=o.actual_planting_date,
        actual_harvest_date=o.actual_harvest_date, cultivar=o.cultivar,
        notes=o.notes, created_at=o.created_at,
    )


class FarmRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def _save(self, o):
        self.s.add(o)
        self.s.commit()
        self.s.refresh(o)
        return o

    def add_farm(self, farm: Farm) -> Farm:
        o = FarmORM(name=farm.name, municipality_code=farm.municipality_code)
        return _farm(self._save(o))

    def list_farms(self) -> list[Farm]:
        return [_farm(o) for o in self.s.scalars(select(FarmORM).order_by(FarmORM.id))]

    def get_farm(self, farm_id: int) -> Farm | None:
        o = self.s.get(FarmORM, farm_id)
        return _farm(o) if o else None

    def add_field(self, f: Field) -> Field:
        if self.s.get(FarmORM, f.farm_id) is None:
            raise LookupError(f"Farm {f.farm_id} inexistente")
        o = FieldORM(farm_id=f.farm_id, name=f.name, area_ha=f.area_ha,
                     latitude=f.latitude, longitude=f.longitude)
        return _field(self._save(o))

    def list_fields(self, farm_id: int) -> list[Field]:
        stmt = select(FieldORM).where(FieldORM.farm_id == farm_id).order_by(FieldORM.id)
        return [_field(o) for o in self.s.scalars(stmt)]

    def add_cycle(self, c: CropCycle) -> CropCycle:
        if self.s.get(FieldORM, c.field_id) is None:
            raise LookupError(f"Field {c.field_id} inexistente")
        o = CropCycleORM(
            field_id=c.field_id, crop=c.crop, season_label=c.season.label,
            harvest_year=c.season.harvest_year, area_ha=c.area_ha, cultivar=c.cultivar,
            planned_planting_date=c.planned_planting_date,
            actual_planting_date=c.actual_planting_date, harvest_date=c.harvest_date,
            actual_yield_sc_ha=c.actual_yield_sc_ha, notes=c.notes,
        )
        return _cycle(self._save(o))

    def get_cycle(self, cycle_id: int) -> CropCycle | None:
        o = self.s.get(CropCycleORM, cycle_id)
        return _cycle(o) if o else None

    def update_cycle(self, cycle_id: int, changes: dict) -> CropCycle:
        o = self.s.get(CropCycleORM, cycle_id)
        if o is None:
            raise LookupError(f"CropCycle {cycle_id} inexistente")
        for key, value in changes.items():
            setattr(o, key, value)
        return _cycle(self._save(o))

    def field_of_cycle(self, cycle_id: int) -> Field | None:
        o = self.s.get(CropCycleORM, cycle_id)
        return _field(self.s.get(FieldORM, o.field_id)) if o else None

    def add_observation(self, obs: YieldObservation) -> YieldObservation:
        if self.s.get(CropCycleORM, obs.crop_cycle_id) is None:
            raise LookupError(f"CropCycle {obs.crop_cycle_id} inexistente")
        o = YieldObservationORM(
            crop_cycle_id=obs.crop_cycle_id, actual_yield_sc_ha=obs.actual_yield_sc_ha,
            area_ha=obs.area_ha, actual_planting_date=obs.actual_planting_date,
            actual_harvest_date=obs.actual_harvest_date, cultivar=obs.cultivar, notes=obs.notes,
        )
        return _obs(self._save(o))

    def list_observations(self) -> list[YieldObservation]:
        stmt = select(YieldObservationORM).order_by(YieldObservationORM.id)
        return [_obs(o) for o in self.s.scalars(stmt)]


class EventRepository:
    """Timeline de eventos agrícolas (parte do agregado CropCycle)."""

    def __init__(self, session: Session) -> None:
        self.s = session

    def add_event(self, e: AgriculturalEvent) -> AgriculturalEvent:
        if self.s.get(CropCycleORM, e.crop_cycle_id) is None:
            raise LookupError(f"CropCycle {e.crop_cycle_id} inexistente")
        o = AgriculturalEventORM(
            crop_cycle_id=e.crop_cycle_id, event_type=e.event_type.value,
            event_date=e.event_date, product_name=e.product_name, product_id=e.product_id,
            quantity=e.quantity, unit=e.unit, cost=e.cost, notes=e.notes,
        )
        self.s.add(o)
        self.s.commit()
        self.s.refresh(o)
        return _event(o)

    def list_by_cycle(self, cycle_id: int) -> list[AgriculturalEvent]:
        stmt = (
            select(AgriculturalEventORM)
            .where(AgriculturalEventORM.crop_cycle_id == cycle_id)
            .order_by(AgriculturalEventORM.event_date, AgriculturalEventORM.id)
        )
        return [_event(o) for o in self.s.scalars(stmt)]


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def add_product(self, p: Product) -> Product:
        o = ProductORM(
            category=p.category.value, commercial_name=p.commercial_name,
            active_ingredient=p.active_ingredient, formulation=p.formulation,
            unit=p.unit, description=p.description,
        )
        self.s.add(o)
        self.s.commit()
        self.s.refresh(o)
        return _product(o)

    def list_products(self) -> list[Product]:
        return [_product(o) for o in self.s.scalars(select(ProductORM).order_by(ProductORM.id))]
