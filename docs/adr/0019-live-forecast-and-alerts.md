# ADR-0019 — Previsão ao vivo e alertas: dado vivo no runtime vs artefato destilado

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0

## Contexto
O ADR-0018 estabeleceu que dado público pesado/instável é coletado **offline** e
servido como artefato JSON datado. A **previsão do tempo** é diferente em natureza:
é **leve** (JSON pequeno do Open-Meteo Forecast), **inerentemente ao vivo** (muda a
cada ciclo de modelo) e **só tem valor se fresca**. Destilá-la num artefato a
contragosto a deixaria velha. É também a maior lacuna da V1: tornar o FADA
**proativo** ("vai gear? vem veranico? tem janela pra pulverizar?").

## Decisão
Definir **dois regimes** para dado externo, escolhidos pela natureza do dado:

1. **Destilado (ADR-0018):** séries pesadas/instáveis e de baixa frequência
   (preço, custo CONAB, ZARC, PAM) → pipeline offline → artefato datado → runtime lê.
2. **Ao vivo (este ADR):** dado leve e que precisa ser fresco (previsão) → **chamada
   de runtime** por connector, **sem cache de disco**, com **degradação graciosa**
   (fonte fora do ar → o serviço sinaliza indisponível; nunca inventa clima).

A previsão entra pelo `OpenMeteoConnector.daily_forecast` (mesma fonte da reanálise
histórica, agora também forecast). O **motor de alertas é domínio puro**
(`domain/weather`): gera alertas **nomeados, com janela, evidência e confiança** —
sem "score mágico" (coerente com ADR-0016). Regras iniciais: geada, veranico,
chuva intensa e janela de pulverização.

Honestidade (ADR-0003): a **confiança decai com o horizonte** e os alertas de chuva
trazem a **probabilidade** da fonte — nunca comunicados como certeza.

Coordenadas resolvidas offline: lat/lon do talhão georreferenciado, com *fallback*
para o **centroide do município** (lookup destilado do dataset, sem chamada extra
ao IBGE).

## Justificativa
- Forçar a previsão no regime de artefato a tornaria estruturalmente velha.
- Forçar preço/custo no regime ao vivo colocaria pandas/duckdb e downloads de
  dezenas de MB no caminho quente da API — exatamente o que o ADR-0018 evita.
- A escolha por **natureza do dado** (peso × frescor) mantém o runtime leve e
  honesto em ambos os casos.

## Consequências
- (+) FADA passa de retrospectivo a **proativo** sem trair o determinismo.
- (+) Sem dependência nova no runtime (Open-Meteo é HTTP/JSON; já usado na V1).
- (−) A rota de previsão depende de rede externa → tratada como 502 + UI que não
   bloqueia a tela.
- (−) Sem cache, cada consulta bate na fonte. Aceitável no volume atual; um cache
   **com TTL** (não permanente) é a evolução natural se o tráfego crescer.

## Próximos passos
Monitores proativos (scheduler) que avaliam os alertas periodicamente e notificam
(push do PWA) — fecha o ciclo "inteligência que chega sozinha".
