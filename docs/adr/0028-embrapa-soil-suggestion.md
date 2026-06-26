# ADR-0028 — Sugestão de solo automática pela localização (EMBRAPA Solos)

**Status:** Aceito · **Data:** 2026-06-26 · **Marco:** V2.0 (mais certeza, menos digitação)

## Contexto
O Perfil Agronômico tem fatores de solo (textura, profundidade, drenagem) que pesam
muito na produtividade — sobretudo nos cenários de veranico (ADR-0023). Mas o
agricultor incerto **não sabe a classe do seu solo de cabeça**, e exigir um laudo
completo antes de qualquer estimativa trava o uso. O dono pediu **mais certeza nos
números a partir de dados públicos/oficiais, automatizando captura**.

A EMBRAPA publica o mapa de solos do Brasil (SiBCS, escala ~1:5.000.000) via WFS,
acessível pelo `agrobr.embrapa_solos.mapa_solos(bbox=...)`. É uma fonte **oficial**
que dá a **ordem de solo dominante** por região — um ponto de partida honesto para
pré-preencher os fatores de solo.

## Decisão
Distilar o mapa EMBRAPA em um artefato pequeno e datado, no padrão ADR-0018
(pipeline offline → JSON; runtime leve só lê):

- **Pipeline** `pipelines/build_soil_suggestions.py`: para cada município da região,
  consulta `mapa_solos(bbox)` (caixa ±0.06° em torno do centróide de
  `data/geo/municipality_centroids.json`), calcula a **ordem dominante por área** e a
  mapeia para um fragmento de perfil sugerido. Gera `data/geo/soil_suggestions.json`
  (datado, com `source`/`note`).
- **Mapeamento conservador** ordem → fatores (ex.: LATOSSOLOS→profundo;
  NITOSSOLOS→profundo+argiloso; NEOSSOLOS→raso; GLEISSOLOS→drenagem má). Latossolo
  férrico (classe com "f") sugere textura argilosa.
- **Confiança**: `"média"` se a ordem dominante cobre ≥60% da área da caixa, senão
  `"baixa"` — sempre exibida.
- **Connector** `data/connectors/soil_suggestion.py` (`SoilSuggestionStore`) lê o
  artefato; degrada para `None` se ausente.
- **Endpoint** `GET /fields/{id}/soil-suggestion` resolve o município pela fazenda do
  talhão e devolve `profile_fragment` + `ordem_dominante` + `confidence` + fonte.
- **UI** (Perfil do Talhão): botão "Sugerir solo pela localização (EMBRAPA)" que
  **mescla** o fragmento no perfil e mostra uma nota — o agricultor confirma/ajusta.

**Princípio mantido (ADR-0002 / honestidade):** a sugestão é um **palpite oficial de
ponto de partida**, não verdade absoluta. A escala 1:5M é grosseira → rotulamos como
**aproximada, confira**. O laudo CQFS (ADR, `/agronomic/soil-analysis`) continua sendo
a fonte preferencial quando o produtor tiver. O domínio decide o número; isto só
pré-preenche entradas que o usuário pode sobrescrever.

## Justificativa
- **Menos digitação, mais adesão**: o produtor incerto sai do zero com um palpite
  oficial em vez de um campo em branco.
- **Mais certeza por dado público**, exatamente o pedido — sem treinar nada, sem LLM.
- Reaproveita a infra ADR-0018 (artefato datado, runtime sem pandas/agrobr) e os
  centróides já versionados (ADR de janela/ZARC).

## Consequências
- (+) Fatores de solo deixam de ser um bloqueio; estimativas divergem por município
  já no dia 1 mesmo sem laudo.
- (+) Auditável e testável (artefato versionado; testes pulam de forma graciosa se
  ausente).
- (−) Escala grosseira: precisão limitada dentro do município (por isso "confira").
  Refino futuro: SoilGrids/levantamentos estaduais de maior resolução, ou cruzar com
  a análise CQFS do próprio talhão.

## Próximos passos
Atualização agendada do artefato junto dos demais (preço/custo/ZARC). Quando houver
laudo CQFS no talhão, dar-lhe precedência sobre a sugestão regional.
