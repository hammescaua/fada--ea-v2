# ADR-0007 — Metodologia do What-If de data de plantio

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
O modelo de produtividade foi treinado em rendimentos municipais com janela
reprodutiva **fixa** e **sem variável de data de plantio** (ADR-0005). Ainda assim,
queremos responder "e se eu plantar 10 dias antes/depois?".

## Decisão
1. **Mecanismo por tempo térmico (GDD):** a data de plantio recoloca as janelas
   fenológicas via soma térmica (base 10 °C), de forma não-linear (meses frios
   acumulam GDD mais devagar). Limiares planta→R1 (720 GDD) e planta→R6 (1500 GDD)
   são parâmetros documentados, calibrados para reproduzir ~a janela de treino na
   data-base regional.
2. **Backtest climatológico:** para cada data candidata, rejogamos a data contra
   cada ano histórico (clima real), relocando a janela e recalculando as 4 features;
   o modelo gera uma **distribuição** de produtividade por data. Cenários, intervalo
   e risco saem dessa distribuição.
3. **Ferramenta comparativa:** resultados são reportados primariamente como **deltas
   vs. a data-base regional**, pois o nível absoluto é ancorado pelo modelo, não
   calibrado por data de plantio.

## Validação
- **Reconciliação:** a data-base simulada (~01/11) reproduz o endpoint regional
  (Horizontina: 52,4 vs 51,2 sc/ha; Δ +1,2). 
- **Plausibilidade fenológica:** janela reprodutiva da data-base (~24/12–12/02)
  sobrepõe a janela de treino (21/12–28/02).
- **Validação temporal:** o grid usa clima real por ano (não sintético); o modelo
  subjacente já é validado por leave-one-year-out.

## Limitações (honestidade-first)
- **Não captura o potencial produtivo intrínseco da data** (fotoperíodo, radiação,
  comprimento de ciclo) — só a exposição a estresse climático. Por isso a otimização
  opera **dentro do ZARC** (ADR-0008), onde o potencial é tido como adequado.
- Calibração empírica do efeito absoluto de data exige dado resolvido por lavoura
  (flywheel, V1+).

## Consequências
- (+) Responde perguntas de decisão reais com método defensável e reprodutível.
- (+) Runtime leve: grid pré-computado offline; inferência só com numpy.
- (−) Escopo limitado à dimensão de risco climático — comunicado em `scope_note`.
