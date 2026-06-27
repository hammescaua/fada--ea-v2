# ADR-0031 — Projeção plurianual de produtividade × rentabilidade

**Status:** Aceito · **Data:** 2026-06-27 · **Marco:** V2.0 (fechamento — olhar à frente)

## Contexto
O produtor quer olhar **várias safras à frente** de soja: simular data, insumos,
manejo, preço e custo, e ver **produtividade e rentabilidade aproximadas** com
explicação. As peças existem (estimativa por talhão com cenários; economia; crédito),
mas faltava uma visão que projetasse **N safras lado a lado**.

## Decisão
Adicionar uma projeção plurianual **honesta e determinística** por talhão:

- A produtividade é calculada **uma vez** (via a estimativa personalizada do talhão:
  regional + perfil a priori + cenários seco/normal/favorável). Como **não existe
  previsão de tempo além de ~16 dias**, a base climática de cada safra futura é a
  **safra típica** da região e **se repete** — não fingimos prever o clima do ano X.
- A **rentabilidade varia por safra** conforme o que o produtor assume: **preço** e
  **custo**, com **tendência anual opcional** (ex.: custo +4%/ano). Sem valores
  informados, usa as fontes públicas datadas (CEPEA/CONAB).
- `domain/finance/projection.py` (puro): `next_seasons()` e `project_economics()`
  (receita/lucro/margem por cenário). `services/multiseason.py` orquestra; rota
  `GET /fields/{id}/multi-season`. UI: página **Projeção de Safras**.
- Narrativa em linguagem natural (determinística; o LLM gratuito, se houver, só a
  deixa mais fluida — ADR-0002/0029).

**Honestidade (pilar):** deixamos explícito, em texto e disclaimer, que a base
climática é a *safra típica* (repete) e que a variação entre safras vem das
hipóteses do produtor — não de uma "previsão" do ano. Tudo com intervalo/cenários,
nunca número único travestido de certeza.

## Justificativa
- Entrega exatamente o pedido ("ver várias safras à frente, com produtividade,
  rentabilidade e explicação") **sem** prometer previsão climática impossível.
- Reaproveita a estimativa por talhão e as fontes públicas; cálculo puro e testável.
- Eficiente: produtividade computada uma vez; só a economia itera por safra (e uma
  única chamada de narrativa).

## Consequências
- (+) O produtor compara o lucro provável das próximas safras sob cenários e
  hipóteses de preço/custo, num só lugar.
- (+) Determinístico, 100% testável; degrada (preço/custo 0 com nota) se faltarem
  artefatos públicos.
- (−) Não diferencia o clima ano-a-ano (impossível). Mitigado por rótulo "safra
  típica" e pelos 3 cenários. O aprendizado a posteriori refina o talhão ao longo do
  tempo, mas não prevê o clima futuro.

## Próximos passos
Incorporar o custo do crédito (ADR-0030) na margem líquida da projeção. Permitir
variar o manejo por safra (não só preço/custo). Sensibilidade a uma trajetória de
preço informada ponto a ponto.
