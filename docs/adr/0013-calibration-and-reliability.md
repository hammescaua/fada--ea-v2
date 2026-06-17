# ADR-0013 — Calibração e confiabilidade dos intervalos

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
A pergunta desta etapa não é "o FADA é preciso?", mas "**os intervalos que o FADA
comunica são honestos?**". Um sistema calibrado vale mais que um meramente preciso:
uma previsão pontual sem incerteza confiável é perigosa para a decisão do agricultor.

## Decisões

### Por que calibração > precisão
A hierarquia correta de avaliação probabilística (Gneiting) é **calibração primeiro,
sharpness depois**. De nada adianta um ponto exato se o intervalo de 80% só contém a
realidade em 60% das vezes (overconfidence). Medimos calibração com **cobertura +
IC de Wilson** e a forma da má-calibração com o **reliability diagram**.

### O que realmente calibramos (honestidade)
- **Regional:** 787 observações reais (IBGE × clima) → calibração empírica via
  **leave-one-year-out**. Real.
- **Personalizado:** não há ground truth por fazenda ainda. Usamos **municípios como
  proxy de fazenda** (cada município tem um desvio sistemático vs. o modelo pooled —
  exatamente o que o adaptive corrige). É um teste legítimo do *mecanismo*; calibração
  com fazendas reais virá com o flywheel.

### Por que NÃO usamos deep learning
Calibração exige um modelo cuja incerteza seja estimável e auditável. Nosso intervalo
vem dos **quantis dos resíduos out-of-fold** (estilo conformal) — calibrado por
construção e verificável. Deep learning traria incerteza opaca, miscalibração típica
(redes são notoriamente overconfident) e nenhum ganho com os ~800 dados que temos.

### Por que NÃO estreitamos intervalos
A incerteza dominante é o **clima do ano** — irredutível. Personalizar corrige o
*offset sistemático* da fazenda, não o desconhecimento sobre a próxima safra ser seca
ou não. Garantia provada e testada (property-based):
```
meia-largura_pers = √(meia-largura_reg² + (ponto·SE_bias)²) ≥ meia-largura_reg
```
Vale para **a largura** (a magnitude da incerteza), **não** para contenção de conjunto
— o centro legitimamente se desloca com o bias.

### CRPS descartado
CRPS é computável (ensemble empírico dos resíduos, sem hipótese distribucional forte),
mas é **redundante com pinball + cobertura** (CRPS = integral do pinball sobre todos os
níveis) e menos interpretável. Pela exigência de parcimônia, descartado. Mantidos:
cobertura(+Wilson), sharpness, reliability diagram, pinball (proper score), MAE/RMSE/bias.

## Resultados (backtest LOYO, 787 casos)
- Regional: IC80 cobre **79%** (Wilson [76%, 82%]) → **calibrado**; reliability quase
  diagonal (0,5→0,49; 0,9→0,89; 0,95→0,94).
- Personalizado: IC80 **81%** (calibrado), **MAE 6,65 < 6,96** e **pinball 2,18 < 2,25**
  do regional, **sem estreitar** o intervalo (22,5 vs 22,4 sc/ha). Ou seja: personalizar
  melhora a acurácia preservando a honestidade da incerteza.

## Limitações
- Calibração personalizada por proxy (municípios) até haver dado de fazenda.
- Quantis OOF assumem certa estacionariedade; mudança climática pode alargar a
  incerteza verdadeira → monitorar a cobertura ao longo das safras.
- Sharpness alta em termos relativos (~68%) reflete a variância climática real do RS,
  não um defeito do modelo.
