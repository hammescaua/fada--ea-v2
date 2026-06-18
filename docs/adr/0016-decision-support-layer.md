# ADR-0016 — Camada de apoio à decisão (sem score único, sem prescrição)

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
Transformar o FADA em apoio à decisão sem virar "ChatGPT agrícola" nem um "semáforo
mágico". O risco maior aos princípios do projeto é um **Priority Score único**.

## Decisões

### Fronteira de escopo (a mais importante)
**FADA aponta ONDE olhar, não O QUE fazer agronomicamente.** Recomendação agronômica
exige modelos de resposta validados e responsabilidade técnica que não temos. A camada
de decisão **prioriza atenção baseada em dados**, não prescreve manejo.

### Rejeitado: Priority Score único
Combinar grandezas incomensuráveis (sc/ha, R$, %, contagem, confiança) em um número:
- **falsa precisão** ("prioridade 0,73" — de quê?);
- **pesos arbitrários** = juízo de valor opaco;
- **compensatório** (margem ótima "compensa" estabilidade péssima);
- **inverificável** (sem ground truth de "era o talhão certo a priorizar").
→ **REJEITADO.**

### Implementado: flags nomeadas + ranking multi-critério
- **`AttentionFlag`** (Value Object): alertas nomeados, com limiares **explícitos**,
  *evidence gating* (N), tamanho de efeito e **confiança** (alta para custo/orçamento;
  conforme N para histórico; moderada para meta-vs-regional). Códigos: `custo_ha_alto`,
  `abaixo_da_meta`, `orcamento_estourado`, `orcamento_quase_esgotado`,
  `abaixo_da_regiao`, `instavel`.
- **`FieldAttention`** (VO): `attention_level` = **severidade máxima** das flags
  (alta/média/saudável). É o heatmap — e clicar mostra exatamente as flags. Sem score.
- **Ranking multi-critério**: uma dimensão por vez (custo/ha, distância da meta,
  % de orçamento consumido, desvio vs região). Sem blending.

### Orçamento futuro: projeção baseada no plano (não extrapolação linear)
Custo de safra é irregular (picos de plantio/adubação/pulverização/colheita) →
extrapolação linear engana. **Projeção honesta = gasto real + custo das operações
planejadas pendentes** (usa a agenda). Sem plano → não projeta (declarado).

### Decisão explicável = Value Object, não entidade
Computada na hora (persistir = dado velho); sem identidade. VO imutável (como
`Insight`), exposto como DTO. Carrega evidência, métricas, N, efeito, confiança, limite.

## Descartado (viola princípios)
- Priority Score único (falsa precisão).
- Extrapolação linear de custo (especulação).
- IA generativa / LLM escolhendo ações (não-determinístico, inauditável).
- Otimização matemática (sem função-objetivo validada).
- Modelos causais (confundimento, sem desenho experimental).
- "Talhão ideal" (falsa certeza, dependente de contexto).
- Recomendações agronômicas (exigem modelos validados + responsabilidade técnica).

## Arquitetura
Contexto fino `domain/decisions` (VOs + regras + ranking, puro) + `services/decisions`
(compõe Field Intelligence + Budget + modelo regional). Reusa as camadas existentes.

## Consequências
- (+) Apoio à decisão honesto, auditável, sem magia; cada cor do heatmap é explicável.
- (−) Não diz "faça X" — intencional. Aponta onde olhar; a decisão agronômica é do produtor.
