"""Casos de uso de What-If de data de plantio: simulação e otimização.

Lê o grid pré-computado (features por município × data × ano), resolve o município,
encaixa a data pedida na resolução do grid e delega a agregação ao domínio
``planting_date``. Reusa a resolução de município e o parsing de safra do serviço
de inteligência regional.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from statistics import median

from app.core.config import settings
from app.domain.crop import SOYBEAN_RS
from app.domain.features import SOYBEAN_FEATURE_NAMES
from app.domain.planting_date import (
    PlantingDateOutcome,
    optimize_planting_window,
    simulate_planting_date,
)
from app.domain.yield_estimation import RegionalYieldModel
from app.services.regional_intelligence import (
    CropNotSupported,
    MunicipalityNotInRegion,
    _normalize,
    parse_harvest_year,
)

GRID_PATH = settings.data_dir / "features" / "soybean_planting_grid_tres_passos.csv"
SCOPE_NOTE = (
    "Esta análise captura a dimensão de RISCO CLIMÁTICO da data de plantio (exposição "
    "a déficit hídrico, veranico e calor no período reprodutivo), não o potencial "
    "produtivo intrínseco (fotoperíodo, radiação, ciclo), que exige dado de campo. Por "
    "isso a otimização opera DENTRO da janela ZARC, onde o potencial é tido como "
    "adequado, e responde: qual data minimiza o risco climático e maximiza a robustez. "
    "Resultados são comparativos (deltas vs data-base), não garantias."
)
# Data-base de referência (regional-típica, ~01/11) para expressar deltas relativos.
# Encaixada na resolução do grid em tempo de execução.
BASELINE_TARGET = (11, 1)


@dataclass(frozen=True)
class GridData:
    features: dict[tuple[int, str], list[dict[str, float]]]
    offsets: dict[tuple[int, str], tuple[int, int]]  # (mediana R1, mediana R6) em dias
    mmdds: list[str]


@lru_cache
def load_grid() -> GridData:
    features: dict[tuple[int, str], list[dict]] = defaultdict(list)
    r1: dict[tuple[int, str], list[int]] = defaultdict(list)
    r6: dict[tuple[int, str], list[int]] = defaultdict(list)
    with open(GRID_PATH, newline="") as fh:
        for row in csv.DictReader(fh):
            key = (int(row["municipality_code"]), row["planting_mmdd"])
            features[key].append({f: float(row[f]) for f in SOYBEAN_FEATURE_NAMES})
            r1[key].append(int(row["r1_offset_days"]))
            r6[key].append(int(row["r6_offset_days"]))
    offsets = {
        k: (round(median(r1[k])), round(median(r6[k]))) for k in features
    }
    mmdds = sorted({mmdd for _, mmdd in features})
    return GridData(features=dict(features), offsets=offsets, mmdds=mmdds)


def _mmdd_to_ref(mmdd: str) -> date:
    m, d = (int(x) for x in mmdd.split("-"))
    return date(2000, m, d)


def _snap(target: date, mmdds: list[str]) -> str:
    ref = date(2000, target.month, target.day)
    return min(mmdds, key=lambda m: abs((_mmdd_to_ref(m) - ref).days))


def _within_zarc(mmdd: str) -> bool:
    start, end = SOYBEAN_RS.planting_window
    ref = _mmdd_to_ref(mmdd)
    return _mmdd_to_ref(f"{start[0]:02d}-{start[1]:02d}") <= ref <= _mmdd_to_ref(
        f"{end[0]:02d}-{end[1]:02d}"
    )


def _reproductive_window(planting: date, key: tuple[int, str], grid: GridData) -> dict[str, str]:
    off_r1, off_r6 = grid.offsets[key]
    return {
        "r1_begin_flowering": (planting + timedelta(days=off_r1)).strftime("%d/%m/%Y"),
        "r6_full_seed": (planting + timedelta(days=off_r6)).strftime("%d/%m/%Y"),
    }


def _justify(o: PlantingDateOutcome, baseline_expected: float) -> str:
    delta = round(o.expected_sc_ha - baseline_expected, 1)
    sign = "+" if delta >= 0 else ""
    return (
        f"Produtividade esperada {o.expected_sc_ha} sc/ha ({sign}{delta} vs data-base "
        f"regional), com piso de {o.downside_sc_ha} sc/ha em anos secos e estabilidade "
        f"(IQR) de {o.stability_sc_ha} sc/ha. Déficit reprodutivo mediano "
        f"{o.risk_drivers['deficit_reprodutivo_mediano_mm']} mm; veranico adverso "
        f"{o.risk_drivers['veranico_adverso_dias']} dias."
    )


@dataclass
class PlantingDateService:
    model: RegionalYieldModel
    grid: GridData

    def _resolve(self, municipality: str) -> tuple[int, str]:
        target = _normalize(municipality)
        for code, info in self.model.municipalities().items():
            if _normalize(info["name"]) == target:
                return int(code), info["name"]
        raise MunicipalityNotInRegion(municipality)

    def _baseline_expected(self, code: int, harvest_year: int) -> float:
        baseline_mmdd = _snap(date(2000, *BASELINE_TARGET), self.grid.mmdds)
        feats = self.grid.features[(code, baseline_mmdd)]
        return simulate_planting_date(
            self.model, feats, harvest_year, baseline_mmdd, True
        ).expected_sc_ha

    def simulate(
        self, municipality: str, crop: str, season: str, planting_date: str,
        risk_aversion: float = 0.5,
    ) -> dict:
        if _normalize(crop) != "soja":
            raise CropNotSupported(crop)
        harvest_year = parse_harvest_year(season)
        code, canonical = self._resolve(municipality)

        requested = date.fromisoformat(planting_date)
        snapped = _snap(requested, self.grid.mmdds)
        key = (code, snapped)
        planting = date(harvest_year - 1, *(int(x) for x in snapped.split("-")))

        outcome = simulate_planting_date(
            self.model, self.grid.features[key], harvest_year, snapped,
            _within_zarc(snapped), risk_aversion,
        )
        baseline = self._baseline_expected(code, harvest_year)
        return {
            "municipality": canonical,
            "municipality_code": code,
            "crop": "soja",
            "season": season,
            "harvest_year": harvest_year,
            "requested_planting_date": planting_date,
            "evaluated_planting_date": planting.strftime("%d/%m/%Y"),
            "snapped_note": (
                None if requested.strftime("%m-%d") == snapped
                else f"Data encaixada na resolução do grid ({snapped})."
            ),
            "within_zarc": outcome.within_zarc,
            "phenology": _reproductive_window(planting, key, self.grid),
            **_outcome_dict(outcome, baseline),
            "explanation": _justify(outcome, baseline),
            "scope_note": SCOPE_NOTE,
        }

    def optimize(
        self, municipality: str, crop: str, season: str, risk_aversion: float = 0.5,
        top_n: int = 5,
    ) -> dict:
        if _normalize(crop) != "soja":
            raise CropNotSupported(crop)
        harvest_year = parse_harvest_year(season)
        code, canonical = self._resolve(municipality)

        grid = {mmdd: self.grid.features[(code, mmdd)] for mmdd in self.grid.mmdds}
        zarc = {mmdd: _within_zarc(mmdd) for mmdd in self.grid.mmdds}
        ranked = optimize_planting_window(
            self.model, grid, harvest_year, zarc, risk_aversion, top_n
        )
        baseline = self._baseline_expected(code, harvest_year)

        recs = []
        for o in ranked:
            planting = date(harvest_year - 1, *(int(x) for x in o.planting_date.split("-")))
            recs.append({
                "planting_date": planting.strftime("%d/%m/%Y"),
                "phenology": _reproductive_window(planting, (code, o.planting_date), self.grid),
                **_outcome_dict(o, baseline),
                "justification": _justify(o, baseline),
            })
        return {
            "municipality": canonical,
            "municipality_code": code,
            "crop": "soja",
            "season": season,
            "harvest_year": harvest_year,
            "risk_aversion": risk_aversion,
            "objective": "equivalente-certeza = mediana − λ·(mediana − P10) (ADR-0008)",
            "zarc_window": (
                f"{SOYBEAN_RS.planting_window[0][1]:02d}/{SOYBEAN_RS.planting_window[0][0]:02d}"
                f" a {SOYBEAN_RS.planting_window[1][1]:02d}/{SOYBEAN_RS.planting_window[1][0]:02d}"
            ),
            "baseline_expected_sc_ha": round(baseline, 1),
            "top_recommendations": recs,
            "scope_note": SCOPE_NOTE,
        }


def _outcome_dict(o: PlantingDateOutcome, baseline: float) -> dict:
    return {
        "expected_yield_sc_ha": o.expected_sc_ha,
        "delta_vs_baseline_sc_ha": round(o.expected_sc_ha - baseline, 1),
        "confidence_interval_sc_ha": list(o.interval_sc_ha),
        "scenarios": [
            {"name": "pessimista", "yield_sc_ha": o.pessimista_sc_ha},
            {"name": "normal", "yield_sc_ha": o.normal_sc_ha},
            {"name": "otimista", "yield_sc_ha": o.otimista_sc_ha},
        ],
        "downside_sc_ha": o.downside_sc_ha,
        "stability_iqr_sc_ha": o.stability_sc_ha,
        "risk_score": o.risk_score,
        "risk_drivers": o.risk_drivers,
        "n_years": o.n_years,
    }
