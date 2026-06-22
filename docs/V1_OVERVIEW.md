# FADA V1 — Visão geral da conclusão

A V1 é um **sistema de apoio à decisão agrícola utilizável** para soja na
microrregião Três Passos (Noroeste RS): backend determinístico + frontend Next.js,
do registro da safra à decisão, com incerteza sempre visível e nada de número
inventado por LLM.

## O que a V1 entrega

| Camada | Capacidade | ADR |
|---|---|---|
| Inteligência Regional | produtividade + intervalo + cenários + riscos + janela (dados reais IBGE/clima) | 0003–0006 |
| Planting What-If | simulação e otimização robusta de data de plantio (ZARC, fenologia GDD) | 0007, 0008 |
| Digital Twin / Flywheel | Farm·Field·CropCycle·YieldObservation; captura de ground truth | 0009 |
| Timeline + Cost Engine | eventos agrícolas + custo/ha, custo/saca, break-even, cenários | 0011 |
| Adaptive Intelligence | personalização por fazenda (encolhimento bayesiano, incerteza preservada) | 0012 |
| Calibração | os intervalos são honestos? (cobertura + Wilson + reliability) + selo | 0013 |
| Field Intelligence + Insights | comparação de talhões + insights com *evidence gating* | 0014 |
| Quick Capture / Planning | registro rápido, presets, plano × realizado, agenda | 0015 |
| Decision Support | atenção por talhão (flags nomeadas, sem score mágico) | 0016 |
| Robustez / Produto | CORS, /system, dashboard, demo, export CSV, contexto global, onboarding | 0017 |
| Orchestrator | assistente conversacional determinístico (roteia + explica) | 0002, 0010 |

## Princípios mantidos (inegociáveis)
- **Determinístico-first** — toda conta nos domain services; o LLM nunca gera número.
- **Incerteza sempre visível** — intervalos e cenários em toda previsão; calibração medida.
- **Evidência > especulação** — *evidence gating*: nada é afirmado sem N e tamanho de efeito.
- **Honestidade > inteligência** — sem score único opaco, sem prescrição agronômica,
  sem extrapolação linear; o que falta dado é dito explicitamente.
- **Baixo atrito** — contexto Fazenda·Safra persistente, zero digitação de ID,
  registro em poucos toques, fazenda de demonstração.
- **Modular monolith / DDD** — bounded contexts puros e testáveis (164 testes).

## Qualidade
- Backend: 164 testes (unit + property-based + integração), ruff limpo.
- Frontend: `tsc --noEmit` limpo + `next build` OK em cada entrega.
- Modelo, dataset e relatório de calibração versionados → funciona out-of-the-box.

## Backlog honesto (V2+)
Adiado conscientemente, por depender de mais dados/usuários — não por esquecimento:
- **`FieldPerformanceProfile` / `CultivarPerformanceProfile`** — exigem ~anos de dado
  por talhão e desenho que evite confundimento (estrutura hierárquica de 3 níveis;
  cultivar exige controle de clima/manejo).
- **Calibração com fazendas reais** — hoje usa municípios como proxy honesto.
- **Importação CSV/Excel e OCR de notas** — onboarding/backfill; OCR é subsistema à parte.
- **Expansão de região e culturas** — arquitetura já preparada para o pooling regional.
- **Export Excel/PDF, testes E2E (Playwright), container do frontend no compose.**
- **Retreino/calibração automáticos por safra** — quando o flywheel acumular massa.

> Princípio de evolução: **o flywheel de dados é mais importante que qualquer modelo.**
> A V1 foi desenhada para capturar dado limpo desde o primeiro uso; é isso que torna
> a personalização e a calibração por fazenda possíveis nas próximas safras.
