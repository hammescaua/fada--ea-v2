# ADR-0005 — Pooling regional e separação tendência × clima

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
O ground truth (IBGE/PAM) é municipal e anual. Uma série única (Horizontina, 51 anos)
é pequena demais para treino robusto. Além disso, a produtividade tem **forte
tendência tecnológica** de décadas (genética, manejo): Horizontina foi de ~1841
(1974) para 3300 kg/ha (2024).

## Decisão
1. **Pooling regional:** treinar no painel dos 20 municípios da microrregião
   **Três Passos** (Noroeste RS), agroclimaticamente homogênea → 787 observações
   reais. Horizontina permanece como alvo de referência.
2. **Decompor tendência × clima:** incluir o **ano** como covariável para capturar o
   ganho tecnológico, deixando as features climáticas explicarem os **desvios** em
   torno da tendência. Sem isso, o modelo creditaria ganho de tecnologia ao clima.

## Justificativa
- n suficiente para comparar modelos e estimar incerteza sem overfitting.
- A homogeneidade agroclimática da microrregião torna o pooling defensável (mesmo
  regime de chuvas, latitude e calendário).
- A separação tendência/clima é prática consolidada na literatura de previsão de
  safras (decomposição tecnológico + anomalia climática).

## Validação
Validação **leave-one-year-out** (cada ano previsto por modelo treinado nos demais),
que reproduz o uso real: prever um ano climático não observado. MAE ≈ 7 sc/ha.

## Consequências
- (+) Dataset real robusto; incerteza honesta.
- (+) Projeção da safra futura (2026/27) extrapola a tendência pelo termo de ano.
- (−) Assume homogeneidade intra-microrregião; expansão exigirá efeitos regionais
  (V2/V3). Extrapolar a tendência muitos anos à frente é arriscado — monitorar.
