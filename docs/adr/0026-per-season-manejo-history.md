# ADR-0026 — Histórico de manejo por safra (manejo × resultado)

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0 (captura de dados / aprendizado)

## Contexto
A personalização aprende o **viés agregado** do talhão (ADR-0025), mas o perfil era
**estático por talhão** — não havia **histórico de manejo por safra**. Sem isso, o
sistema não consegue (no futuro) aprender o efeito de **cada variável** ("quanto o
fungicida rendeu PRA MIM nas últimas safras?"), nem mostrar ao produtor a visão que
ele pede: *o que fiz × o que colhi*.

## Decisão
Capturar o **manejo (snapshot do Perfil Agronômico) por safra**, separado do perfil
"atual" do talhão (que mira a próxima safra):

- Tabela `crop_cycle_manejo` (um manejo por `CropCycle`, JSON) —
  `GET/PUT /crop-cycles/{id}/manejo`.
- `GET /fields/{id}/manejo-history`: por safra, o manejo registrado (ou o perfil
  atual como **proxy**, sinalizado), a **expectativa daquele manejo sob o clima real
  do ano** (`regional_fitted × multiplicador do manejo`) e a **produtividade real**,
  com o desvio (real vs previsto).
- UI no Perfil do Talhão: tabela "manejo × resultado" + ação "salvar perfil atual
  como manejo da safra".

## Justificativa
- Entrega a visão de **histórico** pedida e dá sentido ao registro (combustível do
  flywheel).
- É a **base de dados de treino** para, no futuro, aprender o efeito de cada variável
  com dado real e **revisar a matriz a priori** (hoje de literatura).
- Tabela separada (não coluna nova em `crop_cycles`) → `create_all` cria sem
  migração de coluna; não quebra bancos existentes.

## Consequências
- (+) Cada safra passa a ter um registro auditável (manejo, previsto, real, desvio).
- (+) Caminho aberto para regressão por-variável quando houver volume (sem trair o
  determinismo: o aprendizado é offline e versionado, como o modelo).
- (−) Hoje o snapshot é manual; integrá-lo ao fluxo de fechamento de safra (ao
  registrar a colheita, congelar o manejo) é o refino natural.

## Próximos passos
Congelar o manejo automaticamente ao registrar a colheita. Com volume, treinar a
revisão da matriz por variável. RAG agronômico para explicar o histórico com fonte.
