# ADR-0008 — Otimização de data de plantio ajustada a risco

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
Otimizar data de plantio escolhendo a **maior produtividade média** é frágil: pode
recomendar uma data com média alta mas com anos ruins catastróficos. O agricultor
quer alta produtividade **e** estabilidade entre anos.

## Decisão
Ranquear datas por um **equivalente-certeza** com aversão a risco:

```
score(D) = mediana(D) − λ · (mediana(D) − P10(D))
```

onde a distribuição é a do backtest climatológico (ADR-0007), `P10` é o piso em anos
adversos, e `λ` (default 0.5) é a aversão a risco, exposta como parâmetro da API.

Restrições e relatório:
- **ZARC como restrição dura:** só datas dentro da janela ZARC são candidatas. Isso
  também mitiga a ausência da dimensão de potencial produtivo (ADR-0007).
- Reporta-se, por data: esperado (mediana), **downside (P10)**, upside (P90),
  **estabilidade (IQR)**, score, drivers de risco e justificativa.

## Justificativa
- O equivalente-certeza penaliza explicitamente o downside — alinha a recomendação
  ao que o agricultor valoriza (não quebrar em ano ruim).
- `λ` torna a aversão a risco transparente e ajustável, em vez de embutida.
- Interpretável: o usuário vê *por que* uma data foi escolhida (componentes expostos).

## Consequências
- (+) Recomendações robustas e auditáveis; sensíveis à aversão a risco do produtor.
- (+) Respeita a janela agronômica oficial (ZARC).
- (−) Com `λ=0` recai em maximizar a mediana; cabe ao produto definir o default
  (0.5, conservador-moderado).
