"""Serviço ZARC: janela oficial de plantio e verificação de uma data.

Fonte de verdade para a janela de plantio (substitui o GDD caseiro nesse papel;
o GDD segue como interpolador na simulação de data). Resolve o município por nome
via climatologia do modelo regional, reaproveitando o resolvedor já existente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.data.connectors.zarc_store import ZarcStore
from app.domain.zarc import PlantingWindows


class ZarcUnavailable(Exception):
    """Sem artefato ZARC para a cultura/UF (fonte não coletada)."""


class MunicipalityNotInZarc(Exception):
    """Município não consta no artefato ZARC distilado."""


@dataclass
class ZarcService:
    store: ZarcStore

    def planting_window(
        self, municipality_code: int, crop: str = "soja", uf: str = "RS"
    ) -> dict:
        meta = self.store.meta(crop, uf)
        if meta is None:
            raise ZarcUnavailable(f"{crop}/{uf}")
        windows = self.store.windows(crop, uf, municipality_code)
        if windows is None:
            raise MunicipalityNotInZarc(str(municipality_code))
        return {**meta, **_windows_payload(windows), "disclaimer": _disclaimer(meta)}

    def evaluate_date(
        self, municipality_code: int, planting_date: date,
        crop: str = "soja", uf: str = "RS",
    ) -> dict:
        out = self.planting_window(municipality_code, crop, uf)
        evald = _eval(out, planting_date)
        return {**out, **evald, "planting_date": planting_date.isoformat()}


def _windows_payload(w: PlantingWindows) -> dict:
    return {
        "municipality_code": w.municipality_code,
        "municipality_name": w.municipality_name,
        "windows_by_risk": {
            str(risk): [{"start": s, "end": e} for s, e in wins]
            for risk, wins in w.windows_by_risk.items()
        },
    }


def _eval(payload: dict, planting_date: date) -> dict:
    # Reconstrói PlantingWindows a partir do payload para avaliar a data.
    by_risk = {
        int(r): [(x["start"], x["end"]) for x in wins]
        for r, wins in payload["windows_by_risk"].items()
    }
    w = PlantingWindows(
        municipality_code=payload["municipality_code"],
        municipality_name=payload["municipality_name"],
        windows_by_risk=by_risk,
    )
    return w.evaluate(planting_date.month, planting_date.day)


def _disclaimer(meta: dict) -> str:
    return (
        f"Janela oficial {meta['source']} (soja {meta['manejo'].lower()}, safra "
        f"{meta['safra']}, {meta['portaria']}). As janelas variam por solo e ciclo; "
        "mostramos a mais ampla do município por nível de risco. Risco menor = mais "
        "conservador."
    )
