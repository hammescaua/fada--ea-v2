"""Pipeline offline: coleta preço observado (CEPEA/ESALQ) via agrobr e destila
um artefato JSON pequeno e datado para o runtime ler.

Por que offline: o ``agrobr`` é assíncrono e arrasta dependências pesadas
(pandas, duckdb) e fontes instáveis (rate-limit, circuit-breaker). Mantemos isso
fora do caminho quente da API — exatamente como o artefato do modelo. O runtime
só lê ``data/market/<crop>_price.json`` (ver app/data/connectors/market_snapshot).

Uso:
    python -m pipelines.build_market_snapshot --crop soja --days 120

Requer o extra de ingestão:  pip install -e ".[data]"
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, timedelta
from pathlib import Path

# Raiz do repositório (.../fada--ea-v2), três níveis acima deste arquivo.
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "market"

# Mapeia a cultura do FADA para o produto CEPEA correspondente.
_CEPEA_PRODUCT = {"soja": "soja", "milho": "milho"}


async def _fetch_series(crop: str, days: int) -> dict:
    import agrobr  # import tardio: dependência só do pipeline, não do runtime

    product = _CEPEA_PRODUCT.get(crop, crop)
    inicio = (date.today() - timedelta(days=days)).isoformat()
    df = await agrobr.cepea.indicador(product, inicio=inicio)
    if df is None or len(df) == 0:
        raise SystemExit(f"CEPEA retornou série vazia para '{product}'.")

    df = df.sort_values("data")
    series = [
        {"day": _as_iso(row["data"]), "value": round(float(row["valor"]), 2)}
        for _, row in df.iterrows()
    ]
    last = df.iloc[-1]
    return {
        "crop": crop,
        "source": "CEPEA/ESALQ",
        "place": str(last.get("praca") or "—"),
        "unit": str(last.get("unidade") or "BRL/sc60kg"),
        "methodology": str(last.get("metodologia") or "indicador_esalq"),
        "fetched_at": date.today().isoformat(),
        "series": series,
    }


def _as_iso(value: object) -> str:
    # Aceita datetime.date, datetime.datetime e pandas.Timestamp (subclasse de date,
    # cujo isoformat traz a hora). Sempre devolve apenas YYYY-MM-DD.
    return str(value)[:10]


def main() -> None:
    parser = argparse.ArgumentParser(description="Destila cotação CEPEA em artefato JSON.")
    parser.add_argument("--crop", default="soja")
    parser.add_argument("--days", type=int, default=120, help="Janela de série a coletar.")
    args = parser.parse_args()

    doc = asyncio.run(_fetch_series(args.crop, args.days))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.crop}_price.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    n = len(doc["series"])
    last = doc["series"][-1]
    print(f"OK  {out.relative_to(REPO_ROOT)}  ({n} pontos; "
          f"último {last['day']} = R$ {last['value']:.2f}/sc, {doc['place']})")


if __name__ == "__main__":
    main()
