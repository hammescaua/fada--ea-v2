"""IBGE / SIDRA — Produção Agrícola Municipal (PAM).

Fonte autoritativa do *ground truth* de produtividade: rendimento médio municipal
(kg/ha) por ano, tabela 1612. É a variável-alvo do modelo. API SIDRA:
https://apisidra.ibge.gov.br.
"""

from __future__ import annotations

from app.data.connectors.base import HttpDataSource

_SIDRA_URL = "https://apisidra.ibge.gov.br/values"
_LOCALITIES = "https://servicodados.ibge.gov.br/api/v1/localidades"

# Tabela 1612 (lavouras temporárias): v112 = rendimento médio (kg/ha); c81/2713 = soja.
_TABLE = "1612"
_VAR_YIELD = "112"
_CLASSIF_SOYBEAN = "c81/2713"
_MISSING = {"...", "..", "-", "X"}


class IbgeConnector:
    def __init__(self, source: HttpDataSource | None = None) -> None:
        self._http = source or HttpDataSource()

    def soybean_yield_kg_ha(self, municipality_code: int) -> dict[int, float]:
        """Série anual {ano_colheita: rendimento kg/ha} para um município."""
        url = (
            f"{_SIDRA_URL}/t/{_TABLE}/n6/{municipality_code}"
            f"/v/{_VAR_YIELD}/p/all/{_CLASSIF_SOYBEAN}"
        )
        rows = self._http.get_json(url)[1:]  # primeira linha é cabeçalho
        out: dict[int, float] = {}
        for r in rows:
            value = r.get("V")
            if value in _MISSING or value is None:
                continue
            out[int(r["D3N"])] = float(value)
        return out

    def microregion_municipalities(self, microregion_id: int) -> list[tuple[int, str]]:
        """Lista (código, nome) dos municípios de uma microrregião."""
        data = self._http.get_json(f"{_LOCALITIES}/microrregioes/{microregion_id}/municipios")
        return [(int(m["id"]), m["nome"]) for m in data]

    def municipality_centroid(self, municipality_code: int) -> tuple[float, float]:
        """Latitude/longitude aproximada (centroide) de um município.

        Calcula a média dos vértices da malha GeoJSON do IBGE. Precisão de centroide
        é suficiente para consultar a grade de reanálise climática (~10–25 km).
        """
        data = self._http.get_json(
            f"https://servicodados.ibge.gov.br/api/v3/malhas/municipios/{municipality_code}"
            "?formato=application/vnd.geo+json&qualidade=minima"
        )
        pts = _flatten_coords(data["features"][0]["geometry"]["coordinates"])
        lon = sum(p[0] for p in pts) / len(pts)
        lat = sum(p[1] for p in pts) / len(pts)
        return lat, lon


def _flatten_coords(geometry: object) -> list[list[float]]:
    """Extrai pares [lon, lat] de uma geometria GeoJSON aninhada."""
    out: list[list[float]] = []

    def rec(x: object) -> None:
        if isinstance(x, (list, tuple)):
            if len(x) == 2 and all(isinstance(v, (int, float)) for v in x):
                out.append([float(x[0]), float(x[1])])
            else:
                for item in x:
                    rec(item)

    rec(geometry)
    return out
