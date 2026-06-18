"""Captura rápida: presets de operação e quick-log (1..N talhões em uma chamada)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.farm import AgriculturalEvent, EventPreset, EventType
from app.infra.repositories import EventRepository, FarmRepository, PresetRepository


class PresetNotFound(Exception):
    pass


class CycleNotFound(Exception):
    pass


@dataclass
class CaptureService:
    presets: PresetRepository
    events: EventRepository
    farms: FarmRepository

    def create_preset(self, name: str, event_type: str, **fields) -> EventPreset:
        return self.presets.add_preset(
            EventPreset(name=name, event_type=EventType(event_type), **fields)
        )

    def list_presets(self) -> list[EventPreset]:
        return self.presets.list_presets()

    def quick_log(
        self,
        crop_cycle_ids: list[int],
        event_date: date,
        *,
        preset_id: int | None = None,
        event_type: str | None = None,
        product_name: str | None = None,
        quantity: float | None = None,
        unit: str | None = None,
        cost: float | None = None,
        notes: str | None = None,
    ) -> list[AgriculturalEvent]:
        """Registra a mesma operação em um ou vários talhões (reduz atrito).

        Com ``preset_id``, herda tipo/produto/dose/custo do preset; o custo é
        resolvido por talhão quando o preset é por hectare.
        """
        preset = None
        if preset_id is not None:
            preset = self.presets.get_preset(preset_id)
            if preset is None:
                raise PresetNotFound(preset_id)

        et = EventType((preset.event_type.value if preset else event_type))
        created: list[AgriculturalEvent] = []
        for cycle_id in crop_cycle_ids:
            cycle = self.farms.get_cycle(cycle_id)
            if cycle is None:
                raise CycleNotFound(cycle_id)
            area = cycle.area_ha or (
                f.area_ha if (f := self.farms.field_of_cycle(cycle_id)) else None
            )
            resolved_cost = cost
            if resolved_cost is None and preset is not None:
                resolved_cost = preset.cost_for_area(area)
            created.append(self.events.add_event(AgriculturalEvent(
                crop_cycle_id=cycle_id, event_type=et, event_date=event_date,
                product_name=product_name or (preset.product_name if preset else None),
                product_id=preset.product_id if preset else None,
                quantity=quantity if quantity is not None else (
                    preset.default_quantity if preset else None),
                unit=unit or (preset.unit if preset else None),
                cost=resolved_cost, notes=notes or (preset.notes if preset else None),
            )))
        return created
