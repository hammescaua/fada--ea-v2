# ADR-0010 — Orchestrator conversacional determinístico-first

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
Queremos um modo conversacional ("qual a melhor data para plantar em Horizontina?").
Risco: transformar isso num agente que "raciocina" números — violando a
honestidade-first e o ADR-0002 (LLM não gera valores).

## Decisão
Orchestrator com **roteamento determinístico como padrão** e LLM (Claude) opcional:

1. **`DeterministicRouter`** extrai intenção e slots (município, safra, data de
   plantio) por regras/regex — offline, testável, sem dependências.
2. **Intenções** mapeiam 1:1 para os serviços determinísticos já existentes:
   `regional_intelligence`, `planting_simulation`, `planting_optimization`.
3. O LLM, quando há `ANTHROPIC_API_KEY`, pode assumir o roteamento/explicação via
   tool-use, **caindo no determinístico** em qualquer falha. Ele nunca produz números.
4. O orchestrator chama o serviço escolhido e **verbaliza** o resultado já calculado.

## Justificativa
- Mantém a prioridade do momento (flywheel, não mais "inteligência"): a camada
  conversacional é fina e não adiciona capacidade preditiva nova.
- Roteamento por regras é suficiente e auditável para o vocabulário do domínio
  (datas em PT-BR, nomes de municípios conhecidos, palavras-chave de intenção).
- Respeita ADR-0002: todos os números vêm dos domain services.

## Consequências
- (+) Funciona 100% offline e é testável; LLM é polimento opcional.
- (+) Custo zero por padrão; superfície de alucinação nula nos números.
- (−) Roteamento por regras tem cobertura limitada; perguntas fora do escopo caem em
  `unknown` com pedido de reformulação. Ampliar = habilitar o roteador Claude.
