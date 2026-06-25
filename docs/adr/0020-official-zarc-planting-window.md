# ADR-0020 — Janela de plantio: ZARC oficial como fonte de verdade

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0

## Contexto
A V1 calcula uma janela de plantio com **GDD próprio** (fenologia base 10 °C) e a
exibe rotulada como "janela ZARC". É elegante, mas é uma **fonte caseira competindo
com a fonte oficial**. Para o agricultor, o que o **ZARC do MAPA** indica tem peso
legal e de seguro (Proagro, crédito) que o GDD caseiro não tem. A tábua de risco
oficial está disponível (CC-BY) via `agrobr.zarc`.

## Decisão
Adotar o **ZARC oficial do MAPA como fonte de verdade** da janela de plantio, de
forma **aditiva** (não se remove o otimizador GDD):

1. Pipeline `build_zarc_windows` (offline, ADR-0018) destila a tábua de 36
   decêndios em **janelas MM-DD por nível de risco (20/30/40%)** por município →
   `data/zarc/soja_rs.json` (safra 2025/2026, 497 municípios do RS).
2. A matemática decêndio→janela é **domínio puro e testado** (`domain/zarc`),
   incluindo a fusão da virada do ano (out→jan, típica da soja no RS).
3. Por decêndio tomamos o **menor risco indicado entre as configurações de
   solo/ciclo** do município (janela mais ampla), **rotulada como tal** — sem
   fingir precisão de solo que não temos no cadastro ainda.
4. `ZarcService` expõe a janela oficial e avalia se uma data de plantio está
   dentro do ZARC e em que nível de risco (`GET /zarc/planting-window`).
5. O **otimizador GDD permanece** como interpolador/ranqueador de datas; a UI passa
   a exibir a **janela oficial** separada da "janela do otimizador (GDD)".

## Justificativa
- Alinha o FADA ao instrumento que o produtor usa para **crédito e seguro**.
- Honestidade (ADR-0003): mostra a fonte (portaria, safra, manejo) e explicita a
  agregação por solo/ciclo, em vez de um número caseiro sem proveniência.
- Aditivo: zero regressão no otimizador existente; risco controlado.

## Consequências
- (+) Janela de plantio com autoridade oficial e citável.
- (+) Base para futura personalização por **solo do talhão** (EMBRAPA Solos) e
  **ciclo da cultivar**, que hoje colapsam na "janela mais ampla".
- (−) A agregação por solo/ciclo pode mostrar janelas iguais entre níveis de risco
  quando o melhor solo é favorável em todo o período (caso de Horizontina). É
  honesto, mas só ganha resolução quando soubermos o solo/ciclo do talhão.
- (−) Mais um artefato a versionar e re-coletar por safra.

## Próximos passos
Selecionar solo/ciclo do talhão para janelas específicas; cruzar a data recomendada
pelo otimizador com o nível de risco ZARC na própria recomendação.
