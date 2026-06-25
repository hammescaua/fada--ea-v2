"""Pipeline offline: custo de produção de referência (CONAB) → artefato JSON datado.

Destila os três custos canônicos por hectare (COE/COT/CT) e os principais
componentes de custo para a cultura/UF, a partir do ``agrobr`` (ver ADR-0018).

Uso:
    python -m pipelines.build_cost_benchmark --crop soja --uf RS

Requer o extra de ingestão:  pip install -e ".[data]"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "benchmarks"

# Itens de linha começam com numeração ("8 - Sementes", "3.1 - Tratores"); linhas
# de subtotal ("TOTAL DE…", "CUSTO FIXO…") não — filtramos para não dupli­car.
_LINE_ITEM = re.compile(r"^\s*\d")
_LABEL_PREFIX = re.compile(r"^\s*[\d.]+\s*-\s*")
_TOP_COMPONENTS = 8


async def _fetch(crop: str, uf: str) -> dict:
    import agrobr  # import tardio: dependência só do pipeline

    totals = await agrobr.conab.custo_producao_total(crop, uf=uf)
    df = await agrobr.conab.custo_producao(crop, uf=uf)

    items = []
    for _, r in df.iterrows():
        raw = str(r["item"])
        if not _LINE_ITEM.match(raw) or r.get("valor_ha") is None:
            continue
        items.append(
            {
                "item": _LABEL_PREFIX.sub("", raw).strip(),
                "value_per_ha": round(float(r["valor_ha"]), 2),
                "share_pct": round(float(r["participacao_pct"]), 2),
            }
        )
    items.sort(key=lambda c: c["value_per_ha"], reverse=True)

    return {
        "crop": crop,
        "uf": uf,
        "safra": str(totals["safra"]),
        "technology": str(totals["tecnologia"]),
        "source": "CONAB",
        "fetched_at": date.today().isoformat(),
        "coe_per_ha": round(float(totals["coe_ha"]), 2),
        "cot_per_ha": round(float(totals["cot_ha"]), 2),
        "ct_per_ha": round(float(totals["ct_ha"]), 2),
        "components": items[:_TOP_COMPONENTS],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Destila custo CONAB em artefato JSON.")
    parser.add_argument("--crop", default="soja")
    parser.add_argument("--uf", default="RS")
    args = parser.parse_args()

    doc = asyncio.run(_fetch(args.crop, args.uf))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.crop}_{args.uf.lower()}_cost.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    print(f"OK  {out.relative_to(REPO_ROOT)}  (safra {doc['safra']}: COE "
          f"R$ {doc['coe_per_ha']:.0f}/ha · COT R$ {doc['cot_per_ha']:.0f} · "
          f"CT R$ {doc['ct_per_ha']:.0f}; {len(doc['components'])} componentes)")


if __name__ == "__main__":
    main()
