"""Recuperação sobre a base de conhecimento (RAG-lite, determinístico) — ADR-0027.

Casa a pergunta livre do produtor com os verbetes citáveis do guia agronômico, por
sobreposição de termos + sinônimos do domínio (ferrugem→fungicida, calagem→acidez…).
Sem embeddings/LLM: funciona offline e é testável. Um RAG vetorial pode substituir
esta busca depois, mantendo a mesma interface (LLM explica, domínio decide número).
"""

from __future__ import annotations

import unicodedata

from app.domain.agronomy.knowledge import KnowledgeEntry, guide

# Sinônimos/gatilhos → chave do verbete (robustez sem busca semântica).
_SYNONYMS: dict[str, str] = {
    "ferrugem": "fungicida", "asiatica": "fungicida", "fungicida": "fungicida",
    "calagem": "acidez_corrigida", "calcario": "acidez_corrigida",
    "acidez": "acidez_corrigida", "aluminio": "acidez_corrigida", "ph": "acidez_corrigida",
    "fosforo": "fertilidade_p", "potassio": "fertilidade_k",
    "rizobio": "inoculacao", "inocular": "inoculacao", "inoculacao": "inoculacao",
    "nitrogenio": "inoculacao",
    "nematoide": "nematoides", "nematoides": "nematoides",
    "zarc": "janela_plantio", "epoca": "janela_plantio", "semeadura": "janela_plantio",
    "cultivar": "cultivar", "variedade": "cultivar",
    "rotacao": "rotacao", "braquiaria": "rotacao",
    "daninha": "manejo_daninhas", "buva": "manejo_daninhas", "capim": "manejo_daninhas",
    "praga": "manejo_pragas", "percevejo": "manejo_pragas", "lagarta": "manejo_pragas",
    "arenoso": "textura_solo", "argiloso": "textura_solo", "argila": "textura_solo",
    "palhada": "plantio_direto",
    "estiagem": "veranico", "seca": "veranico", "veranico": "veranico",
    "geada": "geada",
}

# Marcadores que indicam pergunta EXPLICATIVA (e não de número/decisão).
_EXPLANATORY = (
    "por que", "porque", "porq", "pq", "o que e", "o que sao", "explic",
    "para que serve", "importancia", "qual a vantagem", "vale a pena", "preciso de",
    "devo aplicar", "como funciona", "como manejar", "saber sobre", "entender", "fonte",
)


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def _tokens(s: str) -> set[str]:
    return {w for w in _norm(s).replace("?", " ").replace(",", " ").split() if len(w) >= 3}


def looks_explanatory(message: str) -> bool:
    n = _norm(message)
    return any(m in n for m in _EXPLANATORY)


def search_knowledge(query: str, k: int = 3) -> list[KnowledgeEntry]:
    """Verbetes mais relevantes para a pergunta (ordenados). Determinístico."""
    qtokens = _tokens(query)
    qnorm = _norm(query)
    target_keys = {key for syn, key in _SYNONYMS.items() if syn in qnorm}

    scored: list[tuple[int, KnowledgeEntry]] = []
    for e in guide():
        etokens = _tokens(f"{e.title} {e.explanation} {e.key}")
        score = len(qtokens & etokens) + (3 if e.key in target_keys else 0)
        if score > 0:
            scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:k]]


def grounded_answer(entries: list[KnowledgeEntry]) -> str:
    """Resposta fundamentada e citada a partir do verbete principal."""
    if not entries:
        return (
            "Não encontrei esse tema no guia agronômico. Posso explicar fungicida/"
            "ferrugem, inoculação, calagem, fósforo/potássio, época (ZARC), cultivar, "
            "rotação, nematoides, veranico, entre outros."
        )
    top = entries[0]
    answer = f"{top.explanation} Na prática: {top.practical} (Fonte: {'; '.join(top.sources)})"
    related = [e.title for e in entries[1:]]
    if related:
        answer += f" Veja também: {', '.join(related)}."
    return answer
