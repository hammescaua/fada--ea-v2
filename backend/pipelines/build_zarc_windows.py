"""Pipeline offline: tábua de risco ZARC (MAPA) → janelas de plantio por município.

Destila, por município, as **janelas oficiais de plantio** da soja por nível de
risco (20/30/40%), a partir dos 36 decêndios da tábua ZARC via ``agrobr``. Os
decêndios favoráveis (valor > 0) são reduzidos por `decendios_to_windows`
(domínio puro, testado) a intervalos MM-DD. Ver ADR-0018 e ADR-0020.

Para cada decêndio tomamos o **menor risco indicado entre as configurações de
solo/ciclo** do município (janela mais ampla; rotulada como tal). Uso:

    python -m pipelines.build_zarc_windows --crop soja --uf RS

Requer o extra de ingestão:  pip install -e ".[data]"
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date
from pathlib import Path

from app.domain.zarc import RISK_LEVELS, decendios_to_windows

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "zarc"
_DEC_COLS = [f"dec{i}" for i in range(1, 37)]
# Safras a tentar, da mais recente para a mais antiga com soja publicada.
_SAFRA_PREFERENCE = ("2025/2026", "2024/2025")


async def _fetch_uf(crop: str, uf: str):
    import agrobr  # import tardio: dependência só do pipeline

    last_exc: Exception | None = None
    for safra in _SAFRA_PREFERENCE:
        try:
            df = await agrobr.zarc.zoneamento(cultura=crop, uf=uf, safra=safra)
            if df is not None and len(df) > 0:
                return df, safra
        except Exception as exc:  # noqa: BLE001 — safra pode não ter a cultura
            last_exc = exc
    raise SystemExit(f"ZARC sem dados de '{crop}/{uf}' nas safras {_SAFRA_PREFERENCE}: {last_exc}")


def _municipality_windows(rows) -> dict[int, list[tuple[str, str]]]:
    """Para um município (várias linhas de solo/ciclo), janelas por nível de risco."""
    # Melhor (menor) risco indicado por decêndio, entre as configurações.
    best: dict[int, int | None] = {}
    for d_idx, col in enumerate(_DEC_COLS, start=1):
        nonzero = [int(v) for v in rows[col].tolist() if v and int(v) > 0]
        best[d_idx] = min(nonzero) if nonzero else None
    out: dict[int, list[tuple[str, str]]] = {}
    for risk in RISK_LEVELS:
        favorable = {i for i, b in best.items() if b is not None and b <= risk}
        out[risk] = decendios_to_windows(favorable)
    return out


async def _build(crop: str, uf: str) -> dict:
    df, safra = await _fetch_uf(crop, uf)
    manejo = str(df["manejo"].mode().iloc[0]) if "manejo" in df else "Sequeiro"
    portaria = str(df["portaria"].mode().iloc[0]) if "portaria" in df else ""

    municipalities: dict[str, dict] = {}
    for geocodigo, rows in df.groupby("geocodigo"):
        code = int(geocodigo)
        windows = _municipality_windows(rows)
        municipalities[str(code)] = {
            "name": str(rows["municipio"].iloc[0]),
            "n_configs": int(len(rows)),
            "windows_by_risk": {str(r): windows[r] for r in RISK_LEVELS},
        }
    return {
        "crop": crop,
        "uf": uf,
        "safra": safra,
        "manejo": manejo,
        "portaria": portaria,
        "source": "ZARC/MAPA",
        "fetched_at": date.today().isoformat(),
        "note": "Janela mais ampla entre solos/ciclos do município, por nível de risco.",
        "municipalities": municipalities,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Destila janelas ZARC em artefato JSON.")
    parser.add_argument("--crop", default="soja")
    parser.add_argument("--uf", default="RS")
    args = parser.parse_args()

    doc = asyncio.run(_build(args.crop, args.uf))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.crop}_{args.uf.lower()}.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    n = len(doc["municipalities"])
    print(f"OK  {out.relative_to(REPO_ROOT)}  (safra {doc['safra']}, {n} municípios, "
          f"manejo {doc['manejo']})")


if __name__ == "__main__":
    main()
