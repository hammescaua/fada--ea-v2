# ADR-0002 — LLM apenas onde agrega valor; domínio é determinístico

**Status:** Aceito · **Data:** 2026-06-16

## Contexto
O conceito original define ~12 "agentes" (Climate, Soil, Cost, Machinery, Input,
Yield, Market, etc.). A leitura ingênua transforma cada um em um agente de LLM
independente que conversa com os demais.

## Decisão
A **maioria dos "agentes" é serviço de domínio determinístico** (Python puro,
testável, reprodutível). O LLM (**Claude**) é usado **somente** em três papéis:

1. **Orquestração de intenção** — interpretar a pergunta do agricultor e decidir
   quais ferramentas determinísticas chamar (padrão *tool use*).
2. **Explicação em linguagem natural** — traduzir números e cenários em texto claro.
3. **Research / RAG** — sumarizar EMBRAPA, boletins e literatura técnica.

O LLM **nunca produz um número diretamente**; ele invoca a ferramenta que o calcula.

## Justificativa
- Cálculo de adubação, custo, GDD ou margem é determinístico e auditável. Passá-lo
  por um LLM adiciona **custo, latência e risco de alucinação por zero benefício**.
- Reprodutibilidade científica exige que o mesmo input gere o mesmo output —
  incompatível com geração estocástica de valores.
- Concentrar o LLM em poucos pontos reduz drasticamente custo de tokens e superfície
  de erro.

## Consequências
- (+) Saídas numéricas auditáveis e testáveis por unidade.
- (+) Custo de LLM previsível e baixo.
- (+) Confiança: o agricultor pode rastrear de onde veio cada número.
- (−) Menos "mágico" do que um enxame de agentes — intencional.

## Modelos
Padrão para os papéis de LLM: família **Claude** mais recente — Opus para
orquestração/explicação que exigem raciocínio; Haiku para tarefas baratas de alto
volume. IDs configuráveis via `core/config.py`.
