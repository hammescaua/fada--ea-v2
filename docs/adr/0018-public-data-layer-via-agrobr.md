# ADR-0018 — Camada de dados públicos oficiais via agrobr (offline → artefato datado)

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0

## Contexto
A V1 entrega valor sobretudo **após** a colheita (análise). As maiores dores do
produtor são **antes/durante** a safra (preço, janela ZARC, previsão, custo de
referência) e quase todas correspondem a **dado público oficial** que a V1 não usa.
O ecossistema [`agrobr`](https://agrobr.dev/docs/) expõe ~40 fontes oficiais
(CEPEA, CONAB, ZARC, INMET, IBGE, B3, Agrofit, EMBRAPA Solos, SICAR…) como
DataFrames limpos — mas é **assíncrono**, traz dependências pesadas (pandas, duckdb)
e fala com fontes instáveis (rate-limit, circuit-breaker, downloads de dezenas de MB).

## Decisão
Adotar `agrobr` como **acelerador de ingestão**, atrás de um limite rígido:

1. `agrobr` é **dependência só de pipeline** — extra opcional `[data]` no
   `pyproject`. **Nunca** importado no runtime da API.
2. Pipelines offline (`pipelines/build_*`) coletam via `agrobr` e **destilam um
   artefato JSON pequeno e datado** em `data/<dominio>/…` (ex.:
   `data/market/soja_price.json`), versionado como o artefato do modelo.
3. O **runtime lê apenas o artefato** por um connector leve (json + domínio puro),
   exatamente como `RegionalYieldModel.load`. Sem pandas, sem rede no caminho quente.
4. **Datar tudo** (`fetched_at` + data do último dado) e expor **defasagem**; fonte
   ausente → o serviço diz o que não sabe (degradação graciosa), nunca inventa.
5. A **fonte de verdade** continua sendo o órgão oficial citado; `agrobr` é o meio.

Primeira fatia entregue: **preço observado CEPEA/ESALQ** → módulo `domain/market`,
serviço, rota `GET /market/price`, e integração no Financeiro (preço da saca passa
a ser opcional; default = cotação oficial ao vivo, com `price_source` rastreável).

## Justificativa
- Em vez de escrever e manter ~15 connectors frágeis (cf. o stub vazio da CONAB na
  V1), consome-se uma API unificada com *fallback* entre fontes.
- O FADA fica útil **no dia 1, sem depender de nenhuma fazenda cadastrada** — o que
  destrava o flywheel em vez de esperar por ele.
- Mantém o princípio de runtime leve e auditável (ADR-0006): número servido vem de
  artefato inspecionável, não de chamada de rede opaca.
- Preserva a honestidade (ADR-0003): preço é **observado**, nunca previsto.

## Consequências
- (+) Runtime continua sem pandas/duckdb; testes do runtime não dependem de `agrobr`.
- (+) Reprodutível e cacheável; artefato versionável (DVC).
- (−) O dado é tão fresco quanto a última execução do pipeline → exige um
   **scheduler** de refresh (próximo passo da V2.0) e comunicação de defasagem.
- (−) Acrescenta dependência externa (`agrobr`) à toolchain de ingestão: **fixar
   versão** e validar licença por fonte (há CC-BY, CC-BY-NC e ODbL).

## Próximas fatias (mesmo padrão)
ZARC oficial (substitui o GDD caseiro como verdade), CONAB custo de produção
(benchmark de custo/ha), e expansão IBGE/PAM para todo o RS (engorda o dataset de
treino sem fazenda). Ver `FADA_V2_ANALISE_ESTRATEGICA.md`.
