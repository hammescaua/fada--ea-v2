"""Crédito rural e comparação de 2ª safra (ADR-0030)."""

import pytest
from fastapi.testclient import TestClient

from app.domain.finance import CropOption, compare_options, simulate_financing
from app.main import app

client = TestClient(app)


def test_price_installment_is_constant():
    s = simulate_financing(100_000, 12.0, 12, "price")
    assert s.first_installment == s.last_installment
    assert s.total_paid > s.principal
    assert s.total_interest == round(s.total_paid - s.principal, 2)


def test_sac_installment_decreases():
    s = simulate_financing(120_000, 10.0, 12, "sac")
    assert s.first_installment > s.last_installment


def test_zero_rate_no_interest():
    s = simulate_financing(60_000, 0.0, 6, "price")
    assert s.total_interest == 0.0
    assert s.first_installment == 10_000.0


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        simulate_financing(0, 10, 12)
    with pytest.raises(ValueError):
        simulate_financing(1000, 10, 0)
    with pytest.raises(ValueError):
        simulate_financing(1000, 10, 12, "bogus")


def test_compare_options_ranks_by_margin():
    opts = [
        CropOption("Trigo", 60, 70, 3000),       # 4200 - 3000 = 1200
        CropOption("Milho 2ª", 100, 50, 4000),   # 5000 - 4000 = 1000
        CropOption("Cobertura", 0, 0, 500),      # -500
    ]
    res = compare_options(opts)
    assert res[0].name == "Trigo" and res[0].rank == 1
    assert res[-1].name == "Cobertura"
    assert res[0].margin_per_ha == 1200.0
    assert res[0].delta_vs_best_per_ha == 0.0
    assert res[1].delta_vs_best_per_ha == -200.0  # Milho: 1000 - 1200


def test_simulate_endpoint():
    r = client.post(
        "/api/v1/credit/simulate",
        json={"principal": 100000, "annual_rate_pct": 12, "term_months": 12},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_interest"] > 0
    assert "não concede crédito" in body["disclaimer"]


def test_simulate_endpoint_with_area_returns_per_ha():
    r = client.post(
        "/api/v1/credit/simulate",
        json={"principal": 300000, "annual_rate_pct": 10, "term_months": 12, "area_ha": 100},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["principal_per_ha"] == 3000.0
    assert body["total_interest_per_ha"] > 0


def test_compare_endpoint():
    r = client.post(
        "/api/v1/credit/compare-crops",
        json={"options": [
            {"name": "Trigo", "yield_sc_ha": 60, "price_per_bag": 70, "cost_per_ha": 3000},
            {"name": "Milho", "yield_sc_ha": 100, "price_per_bag": 50, "cost_per_ha": 4000},
        ]},
    )
    assert r.status_code == 200
    assert r.json()["best"] == "Trigo"


def test_lines_endpoint_is_dated_and_cited():
    r = client.get("/api/v1/credit/lines")
    assert r.status_code == 200
    body = r.json()
    assert body["fetched_at"]
    assert body["source"]
    assert len(body["lines"]) >= 1
