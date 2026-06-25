# ADR-0024 — Cartão de Decisão unificado (o hub do "Decision Agent")

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0 (Fatia 2 do Guia de Execução)

## Contexto
A V2 acumulou inteligências boas, porém **em formatos diferentes e espalhadas**:
alertas de clima (proativo), recomendações econômicas de manejo (efeito em R$/ha) e
flags de atenção por talhão (histórico). O nome do produto é *Decision Agent*, mas
não havia um **formato único de decisão**. O Guia de Execução (§4) especifica um
"Cartão de Decisão" padronizado como o coração do produto.

## Decisão
Criar o contrato único `DecisionCard` (domínio puro) e um **agregador** que **funde
as fontes já existentes** nele — sem recalcular nada:

```
DecisionCard { id, source(clima|manejo|historico), decision, recommendation,
  effect{ basis, yield_sc_ha[low,ponto,high], profit_brl_ha[low,ponto,high] } | null,
  why[Evidence], confidence, horizon, n_data, disclaimer, severity }
```

- **Construtores puros** mapeam cada fonte: `from_weather_alert`,
  `from_economic_recommendation`, `from_attention_flag`.
- **Regras de honestidade (não negociáveis):** o efeito vem **sempre com intervalo**
  (nunca número seco); clima/preço **nunca** como certeza; o cartão aponta o
  trade-off, **não** prescreve laudo (ADR-0003/0016); o `why` é auditável.
- `DecisionCardService` agrega por fazenda (clima + histórico) e por talhão
  (manejo, quando há perfil + preço + custo), com degradação graciosa por fonte.
- Rota `GET /farms/{id}/decision-cards?field_id=`; a página `decisoes` vira o **hub**
  (clima→manejo→histórico), com o detalhe histórico/rankings abaixo.

## Justificativa
- Materializa o diferencial ("agente que liga manejo → efeito em produtividade E
  lucro, com incerteza") num formato único e reconhecível.
- **Reuso total**: zero tecnologia nova; reorganização de produto sobre o que já
  existe (clima ADR-0019, recomendações econômicas ADR-0022, decisões ADR-0016).
- Banda de incerteza do efeito de manejo proporcional à confiança do fator —
  honra "efeito sempre com intervalo" sem fingir calibração.

## Consequências
- (+) Um só lugar e um só formato para "onde olhar e o que está em jogo".
- (+) Base para novas fontes (NDVI futuro entra como mais um `source`).
- (−) O cartão de manejo depende do brief (perfil + preço + custo); sem isso, só
  aparecem clima e histórico — comunicado na UI.

## Nota sobre o Guia de Execução
O Guia assume "código não começou"; na prática a **Fatia 1 (clima prospectivo +
alertas)** e a **tese manejo→resultado** já estavam implementadas. Esta ADR executa
a **Fatia 2 (cartão unificado + `decisoes` viva)**. Mantém-se o desvio acordado com
o dono: **sem WhatsApp**, foco em **profundidade no Noroeste** antes de expandir.
