"""Testes do domínio/serviço ZARC (janela oficial de plantio)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from app.data.connectors.zarc_store import ZarcStore
from app.domain.zarc import (
    PlantingWindows,
    decendio_bounds,
    decendios_to_windows,
    in_window,
)
from app.services.zarc import MunicipalityNotInZarc, ZarcService, ZarcUnavailable


# -- decêndios (puro) -------------------------------------------------------

def test_decendio_bounds():
    assert decendio_bounds(1) == ((1, 1), (1, 10))     # 1º decêndio de janeiro
    assert decendio_bounds(3) == ((1, 21), (1, 31))    # 3º de janeiro
    assert decendio_bounds(28) == ((10, 1), (10, 10))  # 1º de outubro
    assert decendio_bounds(36) == ((12, 21), (12, 31)) # 3º de dezembro


def test_decendio_out_of_range():
    with pytest.raises(ValueError):
        decendio_bounds(37)


def test_windows_contiguous():
    assert decendios_to_windows({28, 29, 30}) == [("10-01", "10-31")]


def test_windows_wrap_year():
    # Soja no RS: out–dez (28..36) + início de janeiro (1..3) viram uma janela só.
    favorable = {28, 29, 30, 31, 32, 33, 34, 35, 36, 1, 2, 3}
    assert decendios_to_windows(favorable) == [("10-01", "01-31")]


def test_windows_two_disjoint():
    assert decendios_to_windows({1, 2, 10, 11}) == [("01-01", "01-20"), ("04-01", "04-20")]


# -- in_window (puro) -------------------------------------------------------

def test_in_window_normal():
    assert in_window(10, 15, "10-01", "10-31") is True
    assert in_window(11, 1, "10-01", "10-31") is False


def test_in_window_wrap():
    assert in_window(11, 1, "10-01", "01-31") is True   # dentro (nov)
    assert in_window(1, 15, "10-01", "01-31") is True   # dentro (jan)
    assert in_window(3, 1, "10-01", "01-31") is False   # fora (mar)


def test_planting_windows_evaluate():
    w = PlantingWindows(4309605, "Horizontina", {20: [("10-01", "01-31")], 30: [], 40: []})
    assert w.best_risk_for(11, 1) == 20
    out = w.evaluate(11, 1)
    assert out["within_zarc"] is True and out["risk_level"] == 20
    assert w.evaluate(3, 1)["within_zarc"] is False


# -- serviço (fixture em disco) ---------------------------------------------

def _store(tmp_path) -> ZarcStore:
    doc = {
        "crop": "soja", "uf": "RS", "safra": "2025/2026", "manejo": "Sequeiro",
        "portaria": "Port.379", "source": "ZARC/MAPA", "fetched_at": "2026-06-24",
        "note": "teste",
        "municipalities": {
            "4309605": {
                "name": "Horizontina", "n_configs": 15,
                "windows_by_risk": {
                    "20": [["10-01", "01-31"]], "30": [["10-01", "01-31"]],
                    "40": [["10-01", "01-31"]],
                },
            },
        },
    }
    (tmp_path / "soja_rs.json").write_text(json.dumps(doc))
    return ZarcStore(base_dir=tmp_path)


def test_service_window(tmp_path):
    svc = ZarcService(store=_store(tmp_path))
    out = svc.planting_window(4309605, "soja", "RS")
    assert out["municipality_name"] == "Horizontina"
    assert out["windows_by_risk"]["20"][0]["start"] == "10-01"
    assert "ZARC" in out["disclaimer"]


def test_service_evaluate_date(tmp_path):
    svc = ZarcService(store=_store(tmp_path))
    inside = svc.evaluate_date(4309605, date(2026, 11, 1), "soja", "RS")
    assert inside["within_zarc"] is True and inside["risk_level"] == 20
    outside = svc.evaluate_date(4309605, date(2026, 3, 1), "soja", "RS")
    assert outside["within_zarc"] is False


def test_service_errors(tmp_path):
    svc = ZarcService(store=_store(tmp_path))
    with pytest.raises(MunicipalityNotInZarc):
        svc.planting_window(9999999, "soja", "RS")
    empty = ZarcService(store=ZarcStore(base_dir=tmp_path / "nope"))
    with pytest.raises(ZarcUnavailable):
        empty.planting_window(4309605, "soja", "RS")
