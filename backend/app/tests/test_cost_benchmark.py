"""Testes do domínio/serviço de benchmark de custo (CONAB)."""

from __future__ import annotations

import json

import pytest

from app.data.connectors.cost_benchmark import CostBenchmarkStore
from app.core.geo import uf_from_ibge_municipality
from app.domain.benchmark import compare_cost
from app.services.benchmark import BenchmarkService, BenchmarkUnavailable


# -- domínio puro -----------------------------------------------------------

def test_compare_cost_descriptors():
    assert compare_cost(5200, 4668, "COE").descriptor == "acima"   # +11%
    assert compare_cost(4000, 4668, "COE").descriptor == "abaixo"  # -14%
    assert compare_cost(4668, 4668, "COE").descriptor == "na média"
    assert compare_cost(4900, 4668, "COE").descriptor == "na média"  # +5%, dentro da banda


def test_compare_cost_values():
    c = compare_cost(5830, 4668.36, "COE — caixa")
    assert c.reference_per_ha == 4668.36
    assert c.delta_per_ha == round(5830 - 4668.36, 2)
    assert c.ratio_pct == round(5830 / 4668.36 * 100, 1)


def test_uf_from_ibge():
    assert uf_from_ibge_municipality(4309605) == "RS"  # Horizontina
    assert uf_from_ibge_municipality(3550308) == "SP"  # São Paulo
    assert uf_from_ibge_municipality(None) is None


# -- serviço (fixture em disco) ---------------------------------------------

def _store(tmp_path) -> CostBenchmarkStore:
    doc = {
        "crop": "soja", "uf": "RS", "safra": "2025/26", "technology": "alta",
        "source": "CONAB", "fetched_at": "2026-06-24",
        "coe_per_ha": 4668.36, "cot_per_ha": 5830.27, "ct_per_ha": 6655.94,
        "components": [
            {"item": "Tratores e Colheitadeiras", "value_per_ha": 1015.22, "share_pct": 21.75},
        ],
    }
    (tmp_path / "soja_rs_cost.json").write_text(json.dumps(doc))
    return CostBenchmarkStore(base_dir=tmp_path)


def test_service_benchmark(tmp_path):
    svc = BenchmarkService(store=_store(tmp_path))
    out = svc.cost_benchmark("soja", "RS")
    assert out["coe_per_ha"] == 4668.36
    assert out["ct_per_ha"] == 6655.94
    assert len(out["components"]) == 1
    assert "safra inteira" in out["disclaimer"]


def test_service_comparison(tmp_path):
    svc = BenchmarkService(store=_store(tmp_path))
    out = svc.compare_cost(5500.0, "soja", "RS")
    assert out["primary"] == "coe"
    assert set(out["references"]) == {"coe", "cot", "ct"}
    assert out["references"]["coe"].descriptor == "acima"   # 5500 vs 4668 (+18%)
    assert out["references"]["ct"].descriptor == "abaixo"   # 5500 vs 6656 (-17%)


def test_service_missing_is_graceful(tmp_path):
    svc = BenchmarkService(store=CostBenchmarkStore(base_dir=tmp_path))
    with pytest.raises(BenchmarkUnavailable):
        svc.cost_benchmark("soja", "RS")
