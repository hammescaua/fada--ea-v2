# ADR-0029 — LLM gratuito para explicação (OpenAI-compatible, degradação graciosa)

**Status:** Aceito · **Data:** 2026-06-26 · **Marco:** V2.0 (camada de linguagem)

## Contexto
A V2 já tinha o scaffold de LLM (ADR-0002): o domínio decide o número, o LLM só
**verbaliza/explica** — com fallback determinístico para rodar offline. Mas o único
provedor era a **Anthropic (pago)**. O dono pediu explicitamente que a parte de LLM
use **um modelo gratuito**.

Restrições do ambiente: execução **efêmera, sem GPU**, saída HTTPS via proxy. Um
modelo **local** (Ollama) não é prático aqui. A opção gratuita viável é um endpoint
**hospedado com free tier**.

## Decisão
Adotar um cliente LLM **compartilhado e provedor-agnóstico**, priorizando o gratuito:

- `engine/llm_client.py`: `chat(system, user)` escolhe o provedor ativo e **sempre**
  degrada para `None` (sem provedor, erro ou timeout) → o chamador usa o texto
  determinístico.
  - **Gratuito (padrão recomendado):** endpoint **OpenAI-compatible** (`/chat/completions`)
    via `httpx` — sem SDK pesado. Default aponta para **Groq** (free tier rápido:
    `llama-3.3-70b-versatile`), mas serve qualquer provedor compatível (OpenRouter,
    etc.) trocando `FADA_FREE_LLM_BASE_URL`/`MODEL`.
  - **Pago (opcional):** Anthropic, como antes.
- Prioridade em `settings.llm_provider`: **gratuito > Anthropic > nenhum**.
- `explainer.py` unificado: `LLMExplainer` (usa `chat`) ou `TemplateExplainer`
  (determinístico); `build_explainer()` escolhe pelo provedor.
- `refine_narrative(text)`: deixa a narrativa por talhão/brief mais fluida **sem
  tocar nos números**; sem LLM, devolve o texto original.
- Timeout duro (`FADA_LLM_TIMEOUT_SECONDS`, 12s) em toda chamada.
- Provedor ativo exposto em `GET /system/status` (campo `llm`) e na página Sistema.

**Princípio mantido (ADR-0002):** o LLM **nunca** gera nem altera número, data, fator
ou fonte — só reescreve em linguagem mais clara. Tudo verificável; o caminho
determinístico é o piso e nunca quebra.

## Como ativar (gratuito)
1. Criar uma conta grátis na Groq (console.groq.com) e gerar uma API key.
2. Definir no ambiente (ex.: Codespace):
   `FADA_FREE_LLM_API_KEY=<sua_chave>`
   (opcional: `FADA_FREE_LLM_MODEL`, `FADA_FREE_LLM_BASE_URL` para outro provedor).
3. Reiniciar o backend; a página **Sistema** mostra "Explicação (LLM): gratuito (…)".

## Consequências
- (+) Explicação por LLM **sem custo**, mantendo honestidade e offline-first.
- (+) Uma só porta (`chat`) para todo uso de LLM; trocar de provedor é configuração.
- (+) Sem dependência nova obrigatória no runtime (usa `httpx`, já presente).
- (−) Chamada externa no caminho da estimativa quando ativado (mitigado por timeout
  curto + fallback). Free tiers têm limites de taxa — aceitável para uso individual.

## Próximos passos
Cache curto das explicações (evitar recomputar). RAG com o LLM citando a base do
ADR-0027. Captura por voz/foto (LLM estrutura a entrada) — sempre com a regra dura
do ADR-0002.
