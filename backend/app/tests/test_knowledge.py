"""Base de conhecimento agronômico citável (ADR-0027)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.agronomy import for_factor, guide
from app.main import app

pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")


def test_every_entry_has_a_source():
    entries = guide()
    assert len(entries) >= 12
    assert all(e.sources for e in entries)         # nada sem fonte
    assert all(e.explanation and e.practical for e in entries)


def test_for_factor_lookup():
    assert for_factor("fungicida") is not None
    assert for_factor("veranico") is not None      # tema transversal
    assert for_factor("inexistente") is None


def test_knowledge_endpoint():
    r = TestClient(app).get("/api/v1/agronomic/knowledge")
    assert r.status_code == 200
    body = r.json()
    assert any("ferrugem" in e["title"].lower() for e in body)
    assert all(e["sources"] for e in body)


def test_factors_catalog_enriched_with_sources():
    r = TestClient(app).get("/api/v1/agronomic/factors")
    assert r.status_code == 200
    by_key = {f["key"]: f for f in r.json()}
    assert by_key["fungicida"]["sources"]          # fungicida tem fonte
    assert by_key["fungicida"]["explanation"]
