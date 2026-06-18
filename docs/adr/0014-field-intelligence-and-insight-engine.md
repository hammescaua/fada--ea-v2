# ADR-0014 — Field Intelligence (descritivo) e Insight Engine

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
Proposta de três camadas: Field Intelligence, Cultivar Intelligence e Insight Engine.
O objetivo declarado é **valor ao produtor**, não mais inteligência do modelo. As
tabelas de fazenda/talhão estão essencialmente vazias (flywheel recém-iniciado).

## Decisões (o que sobreviveu à crítica)

### 1. Field Intelligence — separar descritivo de preditivo
- **Análise descritiva por talhão (AGORA):** histórico, rankings de produtividade/
  custo/estabilidade, melhores/piores, evolução — sobre o dado que o produtor já
  registra. Computada **na leitura** (sem tabela `FieldPerformanceProfile` persistida).
- **Bias-correction por talhão (ADIADO):** 1 talhão gera ~1 observação/ano → com
  encolhimento, n=1–2 dá ajuste ~zero. Inútil por anos. Quando entrar, a estrutura
  correta é **hierárquica de 3 níveis** (talhão encolhe para a fazenda, fazenda para a
  região), não talhão→região direto. Documentado, não implementado.
- **Estabilidade** é medida sobre os **resíduos ajustados ao clima** (variância do
  desvio vs. expectativa regional do ano), não sobre produtividade bruta — senão
  confunde-se clima com instabilidade do talhão.

### 2. Cultivar Intelligence — REJEITADO por enquanto
Performance de cultivar em dado observacional é **gravemente confundida** com ano,
talhão e manejo. Um ranking ingênuo entrega um número causal-aparente que é
confundido — **viola honestidade > inteligência**. Exigiria muitas observações
cruzadas ou um modelo misto. **Adiado para V3**, e só com dado controlado ou modelo
hierárquico. (Farm → Field → CropCycle apenas, sem cultivar agora.)

### 3. Insight Engine — regras determinísticas com evidence gating (AGORA)
Regras + estatística, sem LLM gerando número. O risco não é "regra ser insuficiente",
é **emitir insight com dado insuficiente**. Logo todo insight declara **N (safras) e
tamanho de efeito**, e só é emitido acima de limiares (ranking ≥2 safras; estabilidade/
tendência ≥3; anomalia ≥4 com variância > 0). Insights de "anos de El Niño" e similares
foram **descartados** (dado externo + inferência fraca com n minúsculo).

## Bounded contexts
`domain/insights` (sumários + estatística + regras, puro) + `services/insights`
(coleta dado real → sumários → insights). O cálculo do *fitted* regional foi extraído
para `services/regional_fitted` e compartilhado com o adaptive.

## Descartado
- `CultivarPerformanceProfile` (confundimento).
- `FieldPerformanceProfile` com shrinkage (fome de dados → adiar).
- Tabela persistida de perfil de talhão (computar na leitura).
- Insights de padrão climático/ENSO (inferência fraca + dado externo).
- Time-decay (prematuro).

## Consequências
- (+) Valor imediato e honesto ao produtor a partir do dado que ele já registra.
- (+) Mesma filosofia clima-condicionada do adaptive (estabilidade defensável).
- (−) Insights só aparecem quando há dado suficiente — intencional (gating).
