# FADA V2 — Visão geral e estado de conclusão

> **Marco V2:** previsão **personalizada por talhão, antes de plantar**, ancorada em
> dados públicos oficiais, com honestidade visível e explicação em linguagem natural.
> Foco geográfico: **Noroeste RS** (profundidade, não largura).

A V1 entregou inteligência **regional** (microrregião) de apoio à decisão. A V2
desce ao **talhão** e ao **pré-safra**: duas lavouras da mesma região passam a ter
previsões diferentes porque solo, manejo, cultivar e histórico são diferentes.

## A jornada do agricultor (a V2 em 4 passos)

A Início mostra **um único próximo passo** conforme o estado do produtor:

1. **Cadastrar fazenda e talhão** — município + área.
2. **Perfil do Talhão** — ~20 fatores agronômicos padronizados (solo, manejo,
   cultivar). Pode pré-preencher o solo pela **localização (EMBRAPA)** ou por um
   **laudo CQFS**. É o que personaliza a previsão *antes de plantar*.
3. **Planejar a safra** — margem esperada, melhor janela de plantio (ZARC oficial),
   e o que mais move produtividade e lucro neste talhão.
4. **Acompanhar a lavoura** — registrar operações; o FADA aprende com os resultados
   e afina as próximas previsões (a posteriori).

## O que a V2 acrescentou à V1

| Capacidade V2 | Como | ADR |
|---|---|---|
| Dados públicos oficiais no runtime, leves e datados | `agrobr` distila offline → artefato JSON; runtime só lê | 0018 |
| Preço (CEPEA), custo (CONAB), janela (ZARC/MAPA) ao vivo | pipelines + connectors + rotas | 0018 |
| Personalização a priori por talhão (antes de plantar) | Perfil Agronômico (~20 fatores) | — |
| Personalização sensível ao cenário (veranico × chuva) | fatores de água pesam por cenário climático | 0023 |
| Convergência a priori → a posteriori | perfil vira o *prior_bias* do encolhimento bayesiano | 0025 |
| Histórico de manejo × resultado por safra | snapshot de manejo por ciclo | 0026 |
| Camada de conhecimento citável ("o porquê") | base curada com fontes (fundação de RAG) | 0027 |
| Solo automático pela localização (EMBRAPA) | mapa SiBCS → ordem dominante → fatores sugeridos | 0028 |
| Explicação em linguagem natural das projeções | narração determinística, ancorada no número | — |
| LLM **gratuito** para reescrever a explicação (offline-first) | endpoint OpenAI-compatible (Groq free tier), degrada para determinístico | 0029 |
| Cartão de decisão unificado (clima/manejo/histórico) | efeito sempre `[baixo, ponto, alto]` | 0024 |
| Honestidade visível (frescor das fontes) | idade + status por fonte em Sistema | 0018 |

## Pilares de engenharia (mantidos da V1)

- **Determinístico-first.** O domínio decide o número; o LLM apenas coordena e
  explica (ADR-0002). Nunca um número inventado por modelo de linguagem.
- **Honestidade.** Tudo datado, com incerteza (intervalo/cenários/N) e fonte citada.
  Degradação graciosa: sem o dado público, o app continua funcionando.
- **Modular monolith / DDD.** `domain/` (puro) → `services/` → `api/`. Um deploy.
- **Runtime leve.** `agrobr` é dependência só de pipeline (`[data]`); o hot path não
  importa pandas nem faz rede para fontes pesadas.

## Estado de conclusão

- Backend: **283 testes** passando, `ruff` limpo; runtime funciona **sem** o `agrobr`
  instalado (lê só os artefatos versionados em `data/`).
- Frontend: build limpo; navegação com **5 destinos primários** (jornada) +
  ferramentas avançadas colapsadas.
- Dados públicos versionados e datados: preço, custo, ZARC, centróides, solo.

## Próximos passos (pós-V2, opcionais)

- **LLM gratuito ativável** (ADR-0029): defina `FADA_FREE_LLM_API_KEY` (chave grátis
  Groq) para explicações mais fluidas; RAG sobre a base citável (ADR-0027) + captura
  por voz/foto são o passo seguinte. Regra dura do ADR-0002 mantida.
- **Atualização agendada** dos artefatos públicos (preço/custo/ZARC).
- **Fundamentos de produção**: migrações Alembic, auth/LGPD, cache de briefs.
- **Solo de maior resolução** (SoilGrids/levantamentos estaduais) cruzado com o
  laudo CQFS do próprio talhão.
