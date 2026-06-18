# FADA — Roadmap

Princípio de execução: **fatias verticais finas** que entregam uma *resposta real*
ao agricultor, não camadas horizontais incompletas. Cada release é utilizável.

---

## MVP — "Inteligência Regional honesta"
**Escopo:** Camada 1 · cultura **soja** · **Horizontina + Noroeste RS** · Modo Básico.

**Input:** município + cultura + safra.

**Pipeline:**
- Clima histórico (NASA POWER + Open-Meteo) no ponto do município →
  **índices agroclimáticos** (chuva na janela crítica R1–R5, déficit hídrico, GDD,
  veranicos/dry spells).
- Produtividade histórica municipal (CONAB / IBGE).

**Saída:**
- Produtividade estimada (**sc/ha**) **com banda de incerteza**.
- Janela ótima de plantio.
- Riscos climáticos da safra.
- **3 cenários** (pessimista / normal / otimista).
- Resumo em **linguagem natural (Claude)** explicando os números e citando fontes.

**Não-objetivos do MVP:** predição por talhão, ML pesado, multi-cultura, preço futuro.

**Critério de pronto:** endpoint `/api/v1/regional-intelligence` + 1 página Next.js;
captura de feedback "quanto você colheu?" embutida (semente do *flywheel*).

---

## V1 — "Gêmeo Digital + Economia"
**Escopo:** Camadas 2–3 · base do Modo Avançado · adiciona **milho**.

- Entidades **Fazenda / Talhão** (PostGIS), import **CAR/SICAR**, histórico.
- Ingestão de **análise de solo** + interpretação agronômica determinística
  (regras CQFS-RS/SC, EMBRAPA).
- **Módulo Custo/Margem/ROI** + breakeven (o que o agricultor mais quer ver).
- **What-If de data de plantio** (primeira alavanca: alto valor, baixo custo).
- Persistência acumulando *ground truth* de campo.

---

## V2 — "ML + Decisão"
- Modelo de yield em **gradient boosting** treinado no dado regional + proprietário
  acumulado, com **incerteza calibrada**.
- What-If completo (cultivar, adubação, nº de aplicações).
- **Disease module:** risco de ferrugem asiática (modelos epidemiológicos /
  Consórcio Antiferrugem), lagartas, cigarrinha.
- **Market module:** preço atual, futuros (B3/CBOT), basis, cenários de margem.
- **Research/RAG** sobre EMBRAPA e boletins técnicos (aqui o LLM agrega muito).

---

## V3 — "Escala nacional + Sensoriamento"
- Expansão multirregião (arquitetura já preparada).
- **NDVI / Sentinel-2** para monitoramento *in-season*.
- Otimização de recomendação (taxa variável por talhão).
- Mobile.

---

## Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Ausência de ground truth por talhão | Predição personalizada inviável por anos | Começar regional; capturar dado do produtor desde o MVP |
| Over-engineering (12 LLMs, microsserviços) | Queima tempo do founder solo | Modular monolith; LLM só onde agrega (ADR-0002) |
| Resposta confiante e errada | Perda de confiança do agricultor | Incerteza sempre (ADR-0003) |
| Promessa de prever preço de commodity | Exposição/credibilidade | Market = dados + cenário, nunca forecast de preço |
| LGPD (CAR, localização, finanças) | Legal | Base legal + isolamento por tenant desde o início |
