# ADR-0004 — Seleção parcimoniosa de features agroclimáticas

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
Havia uma lista candidata ampla (GDD, precipitação acumulada, déficit hídrico,
veranicos, dias >35 °C, distribuição de chuva, chuva em período crítico, indicadores
fenológicos). Com ~800 observações e forte colinearidade entre variáveis hídricas, o
excesso de features causa overfitting e instabilidade dos coeficientes.

## Decisão
Conjunto final de 4 features climáticas + 1 termo de tendência:

1. **Déficit hídrico no período reprodutivo** (Hargreaves ET0 − chuva, 21/dez–28/fev)
2. **Maior veranico no reprodutivo** (dias consecutivos secos)
3. **Dias > 35 °C no reprodutivo** (estresse térmico)
4. **Precipitação total da safra** (out–mar, contexto)
5. **Ano de colheita** (tendência tecnológica — ver ADR-0005)

### Rejeitadas e por quê
- **GDD como preditor:** em RS a energia térmica raramente limita soja; correlaciona
  com duração de ciclo, não com variância de produtividade. Usada apenas para
  *delimitar* janelas fenológicas.
- **Distribuição da chuva (CV, dias de chuva):** redundante com veranico + déficit.
- **Chuva em período crítico isolada:** colinear com o déficit reprodutivo; absorvida.
- **Indicadores fenológicos como feature:** sem fenologia observada, estimá-los injeta
  ruído. Servem para definir janelas, não para prever.

## Evidência
O modelo treinado confirma a hipótese: coeficiente do **déficit reprodutivo é o
dominante e fortemente negativo** (≈ −456 kg/ha por desvio-padrão), com os demais
estresses negativos e menores, e a **tendência de ano fortemente positiva**
(≈ +525 kg/ha). Sinais agronomicamente corretos e interpretáveis.

## Consequências
- (+) Coeficientes estáveis e auditáveis; baixo risco de overfitting.
- (+) Cada número rastreável a um mecanismo agronômico.
- (−) Não captura efeitos de 2ª ordem (ex.: excesso hídrico/doença) — fica para V2.
