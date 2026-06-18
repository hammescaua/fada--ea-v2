"""Modelos ORM (tabelas). Separados das entidades de domínio (mapeadas nos repos)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


class FarmORM(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    municipality_code: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    fields: Mapped[list[FieldORM]] = relationship(
        back_populates="farm", cascade="all, delete-orphan"
    )


class FieldORM(Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"))
    name: Mapped[str] = mapped_column(String(200))
    area_ha: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    farm: Mapped[FarmORM] = relationship(back_populates="fields")
    cycles: Mapped[list[CropCycleORM]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )


class CropCycleORM(Base):
    __tablename__ = "crop_cycles"

    id: Mapped[int] = mapped_column(primary_key=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"))
    crop: Mapped[str] = mapped_column(String(60))
    season_label: Mapped[str] = mapped_column(String(20))
    harvest_year: Mapped[int]
    area_ha: Mapped[float | None]
    cultivar: Mapped[str | None] = mapped_column(String(120), nullable=True)
    planned_planting_date: Mapped[date | None]
    actual_planting_date: Mapped[date | None]
    harvest_date: Mapped[date | None]
    actual_yield_sc_ha: Mapped[float | None]
    target_yield_sc_ha: Mapped[float | None]
    expected_price_per_bag: Mapped[float | None]
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    field: Mapped[FieldORM] = relationship(back_populates="cycles")
    observations: Mapped[list[YieldObservationORM]] = relationship(
        back_populates="cycle", cascade="all, delete-orphan"
    )
    events: Mapped[list[AgriculturalEventORM]] = relationship(
        back_populates="cycle", cascade="all, delete-orphan"
    )
    planned_events: Mapped[list[PlannedEventORM]] = relationship(
        back_populates="cycle", cascade="all, delete-orphan"
    )


class YieldObservationORM(Base):
    __tablename__ = "yield_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    crop_cycle_id: Mapped[int] = mapped_column(ForeignKey("crop_cycles.id"))
    actual_yield_sc_ha: Mapped[float] = mapped_column(Float)
    area_ha: Mapped[float] = mapped_column(Float)
    actual_planting_date: Mapped[date | None]
    actual_harvest_date: Mapped[date | None]
    cultivar: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    cycle: Mapped[CropCycleORM] = relationship(back_populates="observations")


class AgriculturalEventORM(Base):
    __tablename__ = "agricultural_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    crop_cycle_id: Mapped[int] = mapped_column(ForeignKey("crop_cycles.id"))
    event_type: Mapped[str] = mapped_column(String(40))
    event_date: Mapped[date]
    product_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    quantity: Mapped[float | None]
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cost: Mapped[float | None]
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    cycle: Mapped[CropCycleORM] = relationship(back_populates="events")


class PlannedEventORM(Base):
    __tablename__ = "planned_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    crop_cycle_id: Mapped[int] = mapped_column(ForeignKey("crop_cycles.id"))
    event_type: Mapped[str] = mapped_column(String(40))
    planned_date: Mapped[date]
    product_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quantity: Mapped[float | None]
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expected_cost: Mapped[float | None]
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    cycle: Mapped[CropCycleORM] = relationship(back_populates="planned_events")


class EventPresetORM(Base):
    __tablename__ = "event_presets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    event_type: Mapped[str] = mapped_column(String(40))
    product_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    default_quantity: Mapped[float | None]
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    default_cost: Mapped[float | None]
    cost_is_per_hectare: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(40))
    commercial_name: Mapped[str] = mapped_column(String(200))
    active_ingredient: Mapped[str | None] = mapped_column(String(200), nullable=True)
    formulation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FarmPerformanceProfileORM(Base):
    """Memória adaptativa por fazenda (um perfil por fazenda)."""

    __tablename__ = "farm_performance_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), unique=True)
    number_of_cycles: Mapped[int]
    mean_relative_residual: Mapped[float] = mapped_column(Float)
    mean_residual_sc_ha: Mapped[float] = mapped_column(Float)
    median_residual_sc_ha: Mapped[float] = mapped_column(Float)
    variance_relative: Mapped[float] = mapped_column(Float)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
