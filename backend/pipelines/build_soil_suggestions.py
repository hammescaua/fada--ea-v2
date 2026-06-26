"""Pipeline offline: solo dominante por município (EMBRAPA Solos) → sugestão de perfil.

Consulta o mapa de solos da EMBRAPA (SiBCS, escala ~1:5.000.000) por bbox ao redor
do centroide de cada município, pega a **ordem dominante por área** e a converte numa
**sugestão** dos fatores de solo do Perfil Agronômico (textura/profundidade/drenagem).

Honestidade (ADR-0028): a escala é regional, não de talhão — a sugestão é
**aproximada**, com confiança rotulada, e o produtor confirma/ajusta. Mapeamos só o
que é defensável a partir da ordem (profundidade é a mais confiável; textura/drenagem
só quando a ordem implica claramente). Ver dados-abertos da EMBRAPA (CC-BY-NC).

Uso:
    python -m pipelines.build_soil_suggestions

Requer o extra de ingestão:  pip install -e ".[data]"
"""

from __future__ import annotations

import asyncio
import inspect
import json
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CENTROIDS = REPO_ROOT / "data" / "geo" / "municipality_centroids.json"
OUT = REPO_ROOT / "data" / "geo" / "soil_suggestions.json"
_BBOX_DEG = 0.06  # ~6 km ao redor do centroide

# Ordem SiBCS → fatores sugeridos do perfil (conservador; só o defensável).
_ORDER_SUGGESTION: dict[str, dict[str, str]] = {
    "LATOSSOLOS": {"profundidade_solo": "profundo"},
    "NITOSSOLOS": {"profundidade_solo": "profundo", "textura_solo": "argiloso"},
    "ARGISSOLOS": {"profundidade_solo": "medio"},
    "CAMBISSOLOS": {"profundidade_solo": "medio"},
    "NEOSSOLOS": {"profundidade_solo": "raso"},
    "CHERNOSSOLOS": {"profundidade_solo": "medio"},
    "VERTISSOLOS": {"textura_solo": "argiloso"},
    "GLEISSOLOS": {"drenagem": "ma"},
    "PLANOSSOLOS": {"drenagem": "imperfeita"},
    "PLINTOSSOLOS": {"drenagem": "imperfeita"},
}


async def _dominant(lat: float, lon: float) -> tuple[str, str, float]:
    """Retorna (ordem_dominante, classe_dom, share_de_area). Vazio se sem dado."""
    import agrobr

    bbox = (lon - _BBOX_DEG, lat - _BBOX_DEG, lon + _BBOX_DEG, lat + _BBOX_DEG)
    r = agrobr.embrapa_solos.mapa_solos(bbox=bbox)
    r = await r if inspect.isawaitable(r) else r
    if r is None or len(r) == 0:
        return "", "", 0.0
    by_order = r.groupby("ordem1")["area_km2"].sum().sort_values(ascending=False)
    total = float(by_order.sum()) or 1.0
    order = str(by_order.index[0])
    share = float(by_order.iloc[0]) / total
    top_row = r.sort_values("area_km2", ascending=False).iloc[0]
    classe = str(top_row.get("classe_dom") or "")
    return order, classe, share


def _suggestion(order: str, classe: str) -> dict[str, str]:
    sug = dict(_ORDER_SUGGESTION.get(order, {}))
    # Latossolo férrico (classe com 'f', ex.: LVdf) → argiloso; senão, médio.
    if order == "LATOSSOLOS":
        sug["textura_solo"] = "argiloso" if "f" in classe.lower() else "medio"
    return sug


async def _build() -> dict:
    centroids = json.loads(CENTROIDS.read_text())
    out: dict[str, dict] = {}
    for code, info in centroids.items():
        try:
            order, classe, share = await _dominant(info["lat"], info["lon"])
        except Exception as exc:  # noqa: BLE001 — best-effort por município
            print(f"  ! {info['name']} ({code}): {type(exc).__name__}")
            continue
        if not order:
            continue
        out[code] = {
            "name": info["name"],
            "ordem_dominante": order,
            "classe_dom": classe,
            "area_share": round(share, 2),
            "confidence": "média" if share >= 0.6 else "baixa",
            "suggestion": _suggestion(order, classe),
        }
        print(f"  {info['name']}: {order} ({share:.0%}) -> {out[code]['suggestion']}")
    return {
        "source": "EMBRAPA Solos — Mapa de Solos do Brasil (SiBCS, ~1:5.000.000)",
        "fetched_at": date.today().isoformat(),
        "note": "Sugestão aproximada por ordem dominante do município; confirme no campo.",
        "municipalities": out,
    }


def main() -> None:
    doc = asyncio.run(_build())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    print(f"OK  {OUT.relative_to(REPO_ROOT)}  ({len(doc['municipalities'])} municípios)")


if __name__ == "__main__":
    main()
