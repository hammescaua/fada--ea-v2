# ADR-0012 — Adaptive Farm Intelligence (encolhimento hierárquico)

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
Queremos personalizar progressivamente a predição por fazenda **sem** treinar novos
modelos, sem deep learning e sem retreinar o modelo regional. O regional permanece a
fonte; a fazenda entra como **correção**: `Prediction = Regional + BiasCorrection`.

## Decisão
Partial pooling hierárquico (Normal-Normal) com **prior fixo**, aplicado como
correção multiplicativa, com incerteza preservada.

1. **Resíduo clima-condicionado.** `predicted` é o ajuste do modelo regional sob o
   **clima REAL daquele ano** (features reais do município-ano), não a normal
   climatológica. Isola o efeito-fazenda do efeito-clima. `r = (actual − fitted)/fitted`.
2. **Bias multiplicativo** (proporcional ao nível de produtividade), mais defensável
   que offset aditivo em anos extremos.
3. **Encolhimento:** `w = n/(n+k)`, `k = s²/τ²`, com `s²` (ruído de uma observação)
   regularizado por um prior (σ₀=0,20; ν₀=5) e `τ` (desvio entre fazendas, 0,07). O
   peso cresce com a **quantidade E a consistência** das safras.
4. **Empirical Bayes é prematuro** (exige população de fazendas que ainda não existe)
   → prior fixo agora; caminho para EB documentado quando houver população.
5. **Incerteza nunca encolhe artificialmente:**
   `halfwidth_pers = √(halfwidth_reg² + (point_reg·SE_bias)²)`. A largura climática
   regional (irredutível) é mantida; a incerteza da estimativa do bias é **adicionada**.
   Com `n=0`, fallback neutro ao regional.

## Por que é defensável
- A incerteza dominante (clima/ano) é irredutível — personalizar **move o centro,
  quase não estreita a banda**. Isso é a honestidade científica exigida.
- Interpretável, sem overfitting (o encolhimento é exatamente o anti-overfitting),
  sem treino, reprodutível (estatísticas suficientes + política na leitura).
- Validação: fazenda sintética +12% → bias recuperado 12,1%; correção encolhida
  +9,3% (n=10, confiança 77%); intervalo personalizado ≥ regional.

## Defaults (ShrinkagePrior)
`τ=0,07` · `σ₀=0,20` · `ν₀=5` → n=1→w≈0,11; n=10 consistente→≈0,70; n=20→≈0,86.

## Riscos / limitações
- **Não-estacionariedade** (troca de manejo/dono): memória longa fica obsoleta →
  *time-decay* futuro.
- **Confundimento de cultivar**: bias agrega sobre cultivares → `CultivarPerformanceProfile` (futuro).
- **Seleção por poucos anos** e **qualidade do ground truth**: mitigados por
  clima-condicionamento + encolhimento + incerteza honesta.

## Bounded context
`adaptive`: `FarmPerformanceProfile` (memória) + encolhimento (domínio puro) +
`AdaptiveService` (resíduos → perfil → personalização). Field/Cultivar profiles ficam
para evolução (apenas Farm implementado agora).
