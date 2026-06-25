# ADR-0023 — Personalização sensível ao cenário climático

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0 (pilar pré-safra, foco Noroeste RS)

## Contexto
A personalização a priori (ADR-0022) aplicava o efeito de cada fator de forma
**fixa**, igual em qualquer ano. Mas no Noroeste do RS a variância de produtividade
da soja é governada pelo **estresse hídrico reprodutivo (veranico)** — e o solo do
talhão **interage** com o ano: solo arenoso/raso/compactado penaliza muito mais em
ano seco; drenagem ruim penaliza em ano úmido; irrigação vale no seco. Aplicar o
mesmo % nos três cenários subestima o risco real do talhão vulnerável.

## Decisão
Tornar a personalização **sensível ao cenário** (pessimista/normal/otimista, que o
modelo regional já produz). Os fatores **hídricos** recebem um **peso por cenário**:
- "Tampão de seca" (textura, profundidade, compactação, MO, irrigação): efeito
  **amplificado** no pessimista (×1,6) e **atenuado** no otimista (×0,4).
- Drenagem (excesso de água): inverso — amplificado no otimista.
- Demais fatores (sanidade, fertilidade, cultivar): peso 1,0 nos três (neutros).

Calcula-se um **multiplicador por cenário** (`scenario_multipliers`, puro, limitado
a [0,50;1,25]). O **ponto** e o **intervalo** continuam usando o multiplicador flat
(= cenário normal, pesos 1,0), preservando a referência — **sem regressão no ponto**.
Apenas os **cenários** divergem por clima, e isso atravessa para a **margem de risco**
do brief de safra (lucro no cenário pessimista). Uma `water_sensitivity_note`
comunica honestamente quando o talhão é sensível a veranico ou a excesso de chuva.

## Justificativa
- É a variável que mais move a produtividade na região; ignorá-la tornava a
  personalização irrealista para o risco.
- Mantém honestidade e determinismo: pesos documentados e auditáveis; cenário normal
  idêntico ao a priori; o pessimista de um talhão arenoso fica realisticamente pior.
- Profundidade sobre largura: aprofunda o foco no Noroeste em vez de expandir região.

## Consequências
- (+) O cenário pessimista (e a margem de risco) refletem a vulnerabilidade hídrica
  real do talhão — decisão de risco muito mais útil.
- (+) Base para, no futuro, condicionar os pesos ao clima **previsto** da safra
  (Open-Meteo/ZARC) em vez de cenários genéricos.
- (−) Pesos por cenário são estimativas agronômicas (não calibradas ao talhão);
  rotulados como tal, e o ponto permanece conservador (flat).

## Validação (smoke, Horizontina)
Mesma região; só muda a textura do solo:
- Argiloso: pessimista 38,6 · normal 52,7 · otimista 56,2 sc/ha.
- Arenoso: pessimista **32,7** · normal 47,6 · otimista 53,9 sc/ha (+ nota de veranico).
