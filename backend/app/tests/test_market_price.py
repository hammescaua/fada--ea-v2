"""Testes do domínio/serviço de mercado (preço observado)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from app.data.connectors.market_snapshot import MarketSnapshotStore
from app.domain.market import PricePoint, PriceSnapshot, summarize
from app.services.market import MarketService, PriceUnavailable


def _snap(values: list[tuple[str, float]], fetched: str = "2026-06-24") -> PriceSnapshot:
    return PriceSnapshot(
        crop="soja",
        source="CEPEA/ESALQ",
        place="Paranaguá/PR",
        unit="BRL/sc60kg",
        fetched_at=date.fromisoformat(fetched),
        series=tuple(PricePoint(date.fromisoformat(d), v) for d, v in values),
    )


# -- domínio puro -----------------------------------------------------------

def test_summarize_descriptive_stats():
    snap = _snap([("2026-06-01", 100.0), ("2026-06-10", 110.0), ("2026-06-20", 120.0)])
    s = summarize(snap, reference_day=date(2026, 6, 24))
    assert s.latest_value == 120.0
    assert s.latest_day == date(2026, 6, 20)
    assert s.n_points == 3
    assert s.window_days == 19
    assert s.mean_value == 110.0
    assert s.min_value == 100.0
    assert s.max_value == 120.0
    assert s.change_pct == 20.0  # 100 -> 120
    assert s.staleness_days == 4
    assert s.is_stale is False


def test_summarize_flags_staleness():
    snap = _snap([("2026-06-01", 130.0)], fetched="2026-06-24")
    s = summarize(snap, reference_day=date(2026, 6, 24))
    assert s.staleness_days == 23
    assert s.is_stale is True


def test_snapshot_rejects_empty_series():
    with pytest.raises(ValueError):
        PriceSnapshot(
            crop="soja", source="x", place="y", unit="z",
            fetched_at=date(2026, 6, 24), series=(),
        )


# -- connector + serviço (fixture em disco) ---------------------------------

def _write_artifact(tmp_path) -> MarketSnapshotStore:
    doc = {
        "crop": "soja", "source": "CEPEA/ESALQ", "place": "Paranaguá/PR",
        "unit": "BRL/sc60kg", "fetched_at": "2026-06-24",
        "series": [
            {"day": "2026-06-02", "value": 128.74},
            {"day": "2026-06-23", "value": 133.50},
        ],
    }
    (tmp_path / "soja_price.json").write_text(json.dumps(doc))
    return MarketSnapshotStore(base_dir=tmp_path)


def test_service_reads_artifact(tmp_path):
    svc = MarketService(store=_write_artifact(tmp_path))
    out = svc.price("soja", today=date(2026, 6, 24))
    assert out["source"] == "CEPEA/ESALQ"
    assert out["summary"].latest_value == 133.50
    assert out["summary"].is_stale is False
    assert "não prevê preço" in out["disclaimer"]


def test_latest_price_helper(tmp_path):
    svc = MarketService(store=_write_artifact(tmp_path))
    assert svc.latest_price_per_bag("soja") == 133.50


def test_service_missing_artifact_is_graceful(tmp_path):
    svc = MarketService(store=MarketSnapshotStore(base_dir=tmp_path))
    assert svc.latest_price_per_bag("soja") is None
    with pytest.raises(PriceUnavailable):
        svc.price("soja")
