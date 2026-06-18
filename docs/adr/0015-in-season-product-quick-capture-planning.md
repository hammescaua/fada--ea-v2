# ADR-0015 — Produto na safra: Quick Capture, Plano e Orçamento

**Status:** Aceito · **Data:** 2026-06-17

## Contexto
Virada de foco: de "refinar estatística" para "ferramenta que o produtor usa durante
a safra". O dia real do produtor é **registrar o que fez hoje** — logo a espinha é
Quick Capture, e o resto orbita os eventos. As tabelas de fazenda ainda estão
essencialmente vazias (flywheel recém-iniciado).

## Decisões

### IMPLEMENTAR AGORA
1. **Quick Capture — `EventPreset` + quick-log.** O atrito não é o modelo de dados
   (o `AgriculturalEvent` já basta), é a UX. Um preset (favorito) pré-preenche tipo/
   produto/dose/custo; o **quick-log aplica a mesma operação a 1..N talhões** numa
   chamada — porque o produtor pulveriza a fazenda inteira num dia, não um talhão.
2. **Plano no `CropCycle` + `PlannedEvent`.** O plano **não** é um agregado `CropPlan`
   separado (geraria duas fontes de verdade para a mesma safra). O `CropCycle` já é a
   safra: adicionados `target_yield_sc_ha` e `expected_price_per_bag`; `PlannedEvent`
   (operações planejadas) é a única entidade nova.
3. **Orçamento (Plano x Realizado) — extensão do Cost Engine**, não um "Budget Engine"
   separado. Responde "estou no orçamento?", "quanto falta investir?", "estou seguindo
   o plano?".
4. **Agenda — vista derivada de `PlannedEvent`**, não um contexto `Operations`.
   Status por reconciliação de contagem por tipo (sem matching frágil per-evento).
5. **3 intenções de orçamento no orchestrator** (determinístico; LLM não gera número).

> **Ganho arquitetural:** `PlannedEvent` unifica planejamento, baseline de orçamento e
> agenda — uma entidade serve três frentes. É assim que se "evita duplicação".

### ADIAR
- **Import CSV/Excel:** é onboarding/backfill, não uso na safra; valioso depois.
- **Receitas de pulverização (tank mix multi-produto):** agregado novo; um preset por
  produto aproxima.
- **Lembretes/push:** entrega de notificação é infra; a agenda read-only basta.

### DESCARTAR (complexidade prematura)
- **OCR de notas/recibos:** subsistema inteiro (imagem→OCR→extração→validação), alto
  risco, payoff incerto. Revisitar com demanda real.
- **`CropPlan` como agregado separado:** duplicação. O plano vive no `CropCycle`.
- **`Budget Engine` separado:** o Cost Engine basta.
- **Contexto `Operations`:** a agenda é derivada de `PlannedEvent`.
- **"Personalizar modelo" como passo do usuário:** é automático (recompute).

## Princípios preservados
- **Baixo atrito > arquitetura bonita:** preset + quick-log multi-talhão; o plano é
  **opcional** (captura funciona sem plano).
- **Honestidade > inteligência:** agenda por contagem real, sem matching especulativo;
  LLM nunca gera número.
- **Flywheel > modelo:** o objetivo desta etapa é reduzir o atrito de entrada de dados.

## Consequências
- (+) Loop de safra utilizável: planejar (opcional) → registrar rápido → acompanhar
  plano x real → agenda.
- (−) Sem import em massa nem OCR ainda — entrada manual (mitigada por presets/quick-log).
