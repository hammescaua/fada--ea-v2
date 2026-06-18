# Camada de Apoio à Decisão

Ajuda o produtor a priorizar atenção entre talhões — **sem score único, sem
prescrição agronômica, sem LLM**. FADA aponta ONDE olhar, não O QUE fazer (ADR-0016).

## Atenção por flags nomeadas (o heatmap honesto)

Cada talhão recebe um `attention_level` (**alta / média / saudável**) = severidade
máxima das **flags nomeadas** que dispara. Não há score combinado — clicar na cor
mostra exatamente os alertas.

| Flag | Limiar | Severidade | Confiança |
|---|---|---|---|
| `custo_ha_alto` | > 1,3× mediana da fazenda | média / alta (≥1,6×) | alta |
| `abaixo_da_meta` | expectativa 15% / 25% abaixo da meta | média / alta | moderada |
| `orcamento_estourado` | real > planejado (≥1,15×) | média / alta | alta |
| `orcamento_quase_esgotado` | ≥90% consumido + ops pendentes | média | alta |
| `abaixo_da_regiao` | bias ≤ −10% / −20% (N≥2) | média / alta | conforme N |
| `instavel` | desvio ≥15% dos resíduos (N≥3) | média | conforme N |

Cada flag carrega **evidência, métrica, N, efeito e confiança**. Limiares são
constantes explícitas e auditáveis.

## Ranking multi-critério (uma dimensão por vez)

`GET /api/v1/farms/{id}/decisions` retorna, além da atenção por talhão, rankings
**separados** (sem blending): `custo_por_hectare`, `distancia_da_meta_pct`,
`pct_orcamento_consumido`, `desvio_vs_regiao_pct`. O produtor ordena pela que importa.

## Projeção de custo (baseada no plano, não linear)

`GET /api/v1/crop-cycles/{id}/cost-projection`:
`projetado = gasto real + custo das operações planejadas pendentes`. Não é
extrapolação linear (custo de safra é irregular). **Sem plano → não projeta.**

Exemplo: real R$ 160.000 + planejado pendente R$ 25.000 = **projetado R$ 185.000**.

## Assistente (determinístico)

`POST /assistant` com `farm_id`: "Qual talhão merece mais atenção?" → nomeia o talhão
e os motivos (flags). "Qual talhão está mais caro?" → ranking de custo/ha. O LLM nunca
gera número.

## O que NÃO faz (e por quê)
- **Score único de prioridade** — falsa precisão, pesos opacos, inverificável.
- **Extrapolação linear de custo** — especulação (custo de safra é irregular).
- **Recomendação agronômica / "talhão ideal"** — exige modelos validados; fora de escopo.
- **LLM/otimização/causalidade** — não-determinístico/opaco/sem dados.

## Limitações
- Atenção é da safra-alvo (última safra com cycle); contexto histórico (bias/
  estabilidade) entra com N explícito.
- Expectativa de produtividade é regional (tem incerteza) — sinalizado nas flags.
