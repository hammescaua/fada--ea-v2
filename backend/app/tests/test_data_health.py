"""Frescor das fontes públicas (ADR-0018 — honestidade visível)."""

from datetime import date

from app.services.data_health import data_sources_health


def test_reports_every_source_with_status():
    rows = data_sources_health(today=date(2026, 6, 26))
    labels = {r["label"] for r in rows}
    assert "Preço da soja" in labels
    assert "Solo (EMBRAPA)" in labels
    for r in rows:
        assert r["status"] in {"atual", "desatualizado", "ausente", "ok"}


def test_price_freshness_in_known_range():
    rows = {r["label"]: r for r in data_sources_health(today=date(2026, 6, 26))}
    price = rows["Preço da soja"]
    # artefato versionado existe; se presente, idade deve ser não-negativa
    if price["status"] != "ausente":
        assert price["age_days"] is None or price["age_days"] >= 0


def test_stale_price_flagged(monkeypatch):
    # preço com validade de 7 dias deve marcar "desatualizado" muito depois
    rows = {r["label"]: r for r in data_sources_health(today=date(2030, 1, 1))}
    price = rows["Preço da soja"]
    if price["status"] != "ausente":
        assert price["status"] == "desatualizado"
