# ADR-0025 — Convergência a priori (perfil) + a posteriori (colheitas)

**Status:** Aceito · **Data:** 2026-06-24 · **Marco:** V2.0 (acurácia / data flywheel)

## Contexto
A V2 tinha **três** camadas de personalização desconexas: regional (clima), a priori
(Perfil Agronômico, ADR-0022) e a posteriori (shrinkage por colheita, ADR-0012). A
camada a posteriori **encolhia o resíduo observado em direção a 0 (o regional)** —
ignorando o que o perfil agronômico já sabe sobre o talhão. E o agricultor pergunta:
*"como ser mais certeiro nas variáveis que impactam minha lavoura?"*. A resposta é
**aprender do dado real do talhão**, partindo do conhecimento agronômico.

## Decisão
Unificar a priori e a posteriori: o **Perfil Agronômico vira o *prior* do
encolhimento bayesiano**. Generaliza-se `domain/adaptive/shrinkage.personalize` para
encolher em direção a um `prior_bias` (não a 0):

```
viés_aplicado = w · viés_observado(colheitas) + (1 − w) · prior_bias(perfil)
w = n / (n + k)
```

- **n = 0** (sem colheita) ⇒ `w = 0` ⇒ usa o **perfil** (conhecimento agronômico).
- **n cresce** ⇒ `w → 1` ⇒ converge para o **dado real do talhão**.
- `prior_bias = 0` recupera o comportamento original (retrocompatível).

`FieldLearningService` (nível de **talhão**) compõe: regional sob o clima real do ano
(`regional_fitted`) → resíduos das colheitas do talhão → `prior_bias` do perfil →
`personalize(..., prior_bias)`. Rota `GET /fields/{id}/learned-estimate`. A UI mostra
"o que o FADA aprendeu da sua lavoura" (partida no perfil → realidade).

## Justificativa
- É o mecanismo que torna a previsão **certeira por talhão**: começa no conhecimento
  e **adapta-se** ao dado real — exatamente o "ir adaptando" pedido.
- Fecha o **data flywheel**: cada colheita registrada melhora a previsão daquela área.
- Honestidade preservada (ADR-0003/0012): o encolhimento protege contra poucas
  observações ruidosas (confiança baixa com n pequeno) e o intervalo **nunca estreita
  artificialmente** (a incerteza climática do ano é irredutível).

## Consequências
- (+) A personalização passa a ter um único eixo coerente: regional → perfil →
  aprendido, com transição suave governada pela confiança.
- (+) Dá sentido imediato ao registro de colheitas (motiva o flywheel).
- (−) Resíduos podem ser extremos quando o fitted do ano é baixo (divisão por valor
  pequeno); mitigado pelo encolhimento. Winsorização de resíduos fica como refino.
- (−) Hoje a nível de talhão usa o perfil **atual** como proxy do manejo de todas as
  safras; capturar o perfil **por safra** (histórico de manejo) é o próximo passo
  para aprender o efeito de *cada variável* (não só o viés agregado).

## Próximos passos
Capturar o perfil/manejo **por safra** (snapshot no CropCycle) → histórico de manejo ×
resultado → base para, no futuro, aprender o efeito de cada variável (e revisar a
matriz a priori com dado real). RAG agronômico (Embrapa/Agrofit) para **explicar** as
recomendações com fonte citada, sem gerar número.
