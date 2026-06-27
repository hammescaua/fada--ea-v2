"""Cliente LLM compartilhado — gratuito-primeiro, degrada para None (ADR-0029).

Uma única porta para o LLM. ``chat()`` escolhe o provedor ativo (gratuito >
Anthropic > nenhum) e **sempre** degrada graciosamente: devolve ``None`` se não há
provedor, ou se a chamada falhar/estourar o tempo. O chamador então usa o texto
determinístico. O LLM nunca gera números (ADR-0002) — ele só verbaliza.

O provedor gratuito é um endpoint **OpenAI-compatible** (ex.: Groq free tier),
chamado via ``httpx`` (já presente), sem SDK pesado no runtime.
"""

from __future__ import annotations

from app.core.config import settings


def provider() -> str:
    return settings.llm_provider


_REFINE_SYSTEM = (
    "Você reescreve uma explicação agronômica para um agricultor brasileiro, deixando-a "
    "mais clara e natural. REGRAS: não invente nem altere NENHUM número, data, nome de "
    "fator ou fonte — preserve todos exatamente. Não acrescente recomendações novas. "
    "Mantenha o mesmo idioma (português) e seja conciso."
)


def refine_narrative(text: str, facts: dict | None = None) -> str:
    """Reescreve uma narrativa determinística de forma mais fluida (se houver LLM).

    Preserva os números (eles vêm do domínio). Sem provedor ou em erro, devolve o
    texto original inalterado — o caminho determinístico nunca quebra.
    """
    if settings.llm_provider == "none" or not text:
        return text
    user = text if not facts else f"{text}\n\nDados (apenas para contexto): {facts}"
    out = chat(_REFINE_SYSTEM, user, max_tokens=400)
    return out or text


def chat(system: str, user: str, *, max_tokens: int = 500) -> str | None:
    """Uma rodada de chat. Retorna o texto, ou ``None`` se indisponível/erro."""
    prov = settings.llm_provider
    if prov == "free":
        return _openai_compatible(system, user, max_tokens=max_tokens)
    if prov == "anthropic":
        return _anthropic(system, user, max_tokens=max_tokens)
    return None


def _openai_compatible(system: str, user: str, *, max_tokens: int) -> str | None:
    try:
        import httpx

        resp = httpx.post(
            f"{settings.free_llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.free_llm_api_key}"},
            json={
                "model": settings.free_llm_model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=settings.llm_timeout_seconds,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        return text.strip() or None
    except Exception:  # noqa: BLE001 — qualquer falha degrada para determinístico
        return None


def _anthropic(system: str, user: str, *, max_tokens: int) -> str | None:
    try:
        import anthropic

        client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key, timeout=settings.llm_timeout_seconds
        )
        msg = client.messages.create(
            model=settings.llm_orchestrator_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = msg.content[0].text
        return text.strip() or None
    except Exception:  # noqa: BLE001
        return None
