"""Utilidades geográficas mínimas (IBGE).

Mapeia o prefixo de 2 dígitos do código de município IBGE para a sigla da UF.
Usado para localizar a referência regional correta (ex.: benchmark de custo por UF).
"""

from __future__ import annotations

_UF_BY_CODE = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP", 41: "PR",
    42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


def uf_from_ibge_municipality(code: int | None) -> str | None:
    """Sigla da UF a partir do código IBGE de município (7 dígitos). ``None`` se
    desconhecido."""
    if code is None:
        return None
    return _UF_BY_CODE.get(code // 100000)
