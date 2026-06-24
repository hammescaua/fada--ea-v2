"""Testes da interpretação de análise de solo (CQFS) → fatores do perfil."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.domain.agronomy import SoilAnalysis, classify_soil_analysis
from app.domain.agronomy.soil import (
    classify_acidity,
    classify_organic_matter,
    classify_phosphorus,
    classify_potassium,
)
from app.main import app


# -- classificadores (puros) ------------------------------------------------

def test_phosphorus_by_clay_class():
    # Classe 3 (21–40% argila): crítico 6,0 mg/dm³.
    assert classify_phosphorus(2.0, clay_pct=30) == "baixo"     # < 0,5·6
    assert classify_phosphorus(4.0, clay_pct=30) == "medio"     # 0,5–1·6
    assert classify_phosphorus(8.0, clay_pct=30) == "alto"      # 1–2·6
    assert classify_phosphorus(15.0, clay_pct=30) == "muito_alto"  # ≥2·6
    # Solo argiloso (>60%): crítico 3,0 → mesmo P vira classe mais alta.
    assert classify_phosphorus(4.0, clay_pct=70) == "alto"


def test_potassium_by_ctc():
    assert classify_potassium(20, ctc=10) == "baixo"   # crítico 60
    assert classify_potassium(50, ctc=10) == "medio"
    assert classify_potassium(80, ctc=10) == "alto"
    assert classify_potassium(130, ctc=10) == "muito_alto"


def test_organic_matter():
    assert classify_organic_matter(2.0) == "baixa"
    assert classify_organic_matter(3.5) == "media"
    assert classify_organic_matter(6.0) == "alta"


def test_acidity():
    assert classify_acidity(6.0, 2.0) == "recente"   # pH alto, Al baixo
    assert classify_acidity(5.2, 15.0) == "antiga"
    assert classify_acidity(4.8, 25.0) == "nao"
    assert classify_acidity(None, None) is None


def test_classify_only_provided_fields():
    frag, notes = classify_soil_analysis(SoilAnalysis(p_mehlich=2.0, clay_pct=30))
    assert frag == {"fertilidade_p": "baixo"}
    assert len(notes) == 1 and notes[0]["factor"] == "fertilidade_p"


# -- endpoint ---------------------------------------------------------------

def test_soil_analysis_endpoint():
    r = TestClient(app).post("/api/v1/agronomic/soil-analysis", json={
        "p_mehlich": 2.0, "k_mehlich": 30, "clay_pct": 30, "ctc": 10,
        "ph_water": 4.8, "al_saturation_pct": 25, "organic_matter_pct": 2.0,
    })
    assert r.status_code == 200
    body = r.json()
    frag = body["profile_fragment"]
    assert frag["fertilidade_p"] == "baixo"
    assert frag["acidez_corrigida"] == "nao"
    assert frag["materia_organica"] == "baixa"
    assert "CQFS" in body["disclaimer"]


def test_soil_analysis_empty_is_valid():
    r = TestClient(app).post("/api/v1/agronomic/soil-analysis", json={})
    assert r.status_code == 200 and r.json()["profile_fragment"] == {}
