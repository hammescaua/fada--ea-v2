"""Trilha de conhecimento do Assistente (RAG-lite citável) — ADR-0027."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.agronomy import grounded_answer, looks_explanatory, search_knowledge
from app.main import app

pytestmark = pytest.mark.skipif(not settings.model_path.exists(), reason="modelo ausente")


# -- recuperação (pura) -----------------------------------------------------

def test_search_matches_synonyms():
    assert search_knowledge("por que devo me preocupar com ferrugem?")[0].key == "fungicida"
    assert search_knowledge("o que é veranico?")[0].key == "veranico"
    assert search_knowledge("vale a pena fazer calagem?")[0].key == "acidez_corrigida"


def test_looks_explanatory():
    assert looks_explanatory("por que aplicar fungicida?")
    assert looks_explanatory("o que é inoculação")
    assert not looks_explanatory("qual a melhor data para plantar soja em Horizontina?")


def test_grounded_answer_cites_source():
    ans = grounded_answer(search_knowledge("ferrugem"))
    assert "Fonte:" in ans and "Antiferrugem" in ans


def test_search_no_match():
    assert search_knowledge("preço do trator novo") == []


# -- endpoint ---------------------------------------------------------------

def test_assistant_answers_why_with_source():
    r = TestClient(app).post("/api/v1/assistant",
                             json={"message": "por que aplicar fungicida na soja?"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "knowledge"
    assert "Fonte:" in body["answer"]
    assert body["result"]["sources"]


def test_assistant_number_question_still_routes_to_domain():
    # Pergunta de número não deve cair na trilha de conhecimento.
    r = TestClient(app).post(
        "/api/v1/assistant",
        json={"message": "qual a melhor data para plantar soja em Horizontina?"},
    )
    assert r.status_code == 200
    assert r.json()["intent"] != "knowledge"
