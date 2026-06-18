"""Expectativa regional sob o clima REAL do ano (compartilhado por adaptive e insights).

Computa o *fitted* do modelo regional para um (município, ano) usando as features
reais daquele ano — isolando o efeito da propriedade/talhão do efeito do clima.
"""

from __future__ import annotations

import csv
from functools import lru_cache

from app.core.config import settings
from app.domain.features import SOYBEAN_FEATURE_NAMES
from app.domain.units import kg_per_ha_to_bags_per_ha
from app.domain.yield_estimation import RegionalYieldModel

FEATURES_PATH = settings.data_dir / "features" / "soybean_tres_passos.csv"


@lru_cache
def features_lookup() -> dict[tuple[int, int], dict[str, float]]:
    """{(municipio, ano_colheita): features} para computar o fitted regional do ano."""
    out: dict[tuple[int, int], dict[str, float]] = {}
    if not FEATURES_PATH.exists():
        return out
    with open(FEATURES_PATH, newline="") as fh:
        for row in csv.DictReader(fh):
            key = (int(row["municipality_code"]), int(row["harvest_year"]))
            out[key] = {f: float(row[f]) for f in SOYBEAN_FEATURE_NAMES}
    return out


def regional_fitted_sc_ha(
    model: RegionalYieldModel, municipality_code: int, harvest_year: int
) -> float:
    """Fitted regional (sc/ha) sob o clima real do ano; fallback à climatologia normal."""
    feats = features_lookup().get((municipality_code, harvest_year))
    if feats is not None:
        kg = model.predict_kg_ha({**feats, "harvest_year": harvest_year})
        return kg_per_ha_to_bags_per_ha(kg)
    try:
        return model.estimate(municipality_code, harvest_year).point_sc_ha
    except KeyError:
        return 0.0
