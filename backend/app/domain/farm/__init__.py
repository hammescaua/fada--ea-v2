"""Farm — fundação do Digital Twin (entidades puras, sem ORM).

Agregado: Farm -> Field -> CropCycle -> YieldObservation. Season é Value Object
(rótulo + ano de colheita), não entidade (ADR-0009). Mínimo necessário para iniciar
o flywheel de ground truth; solo/CAR/manejo ficam para fases futuras.
"""

from app.domain.farm.entities import (
    CropCycle,
    Farm,
    Field,
    Season,
    YieldObservation,
)
from app.domain.farm.events import (
    APPLICATION_EVENTS,
    AgriculturalEvent,
    EventType,
)

__all__ = [
    "Farm",
    "Field",
    "Season",
    "CropCycle",
    "YieldObservation",
    "AgriculturalEvent",
    "EventType",
    "APPLICATION_EVENTS",
]
