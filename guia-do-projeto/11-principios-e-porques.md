# Capítulo 11 — Os princípios e o "porquê" das decisões

Um projeto bom não é só "código que funciona" — é um conjunto de **decisões conscientes**.
O FADA documenta cada decisão importante num **ADR** (*Architecture Decision Record*,
Registro de Decisão de Arquitetura). São 17 deles, em `docs/adr/`. Aqui eu traduzo os
**princípios** por trás de todos e resumo os ADRs em linguagem simples.

## Os princípios inegociáveis (a "constituição" do projeto)

1. **Determinístico-first.** Toda conta vive em código puro e testável, **não** dentro
   de um LLM. *Por quê?* Para ser auditável, reprodutível e confiável — decisão com
   dinheiro real não pode depender de "chute".

2. **Honestidade > inteligência.** É melhor uma resposta honesta e modesta do que uma
   esperta e enganosa. *Por quê?* Uma previsão confiante e errada destrói a confiança do
   produtor — e sem confiança, ele não usa.

3. **Incerteza sempre visível.** Nunca um número seco; sempre a faixa e os cenários. E a
   faixa é **medida** (calibração). *Por quê?* A realidade agrícola é incerta; esconder
   isso seria mentir.

4. **Evidência > especulação.** O sistema só afirma algo se houver **dados suficientes**
   (o "evidence gating"). Ele prefere o **silêncio** a inventar um insight de dado ralo.

5. **O flywheel de dados é mais importante que qualquer modelo.** O valor de longo prazo
   está em capturar dado de campo limpo. Por isso, **reduzir o atrito de registro** é
   prioridade máxima.

6. **Baixo atrito > arquitetura bonita.** Funcionalidade que o produtor realmente usa
   vale mais que sofisticação que ninguém liga.

## Os 17 ADRs em uma frase cada

| ADR | Decisão | Em uma frase |
|---|---|---|
| 0001 | Monólito modular | Um programa bem dividido, não microsserviços (complexidade prematura). |
| 0002 | LLM só onde agrega | A maioria das "IAs" são contas determinísticas; o LLM só roteia/explica. |
| 0003 | Incerteza-first | Sempre faixa + cenários; baseline simples antes de modelo complexo. |
| 0004 | Seleção de features | Poucos ingredientes defensáveis (déficit hídrico é o nº 1); rejeitar o resto. |
| 0005 | Pooling regional + tendência | Juntar 20 municípios p/ ter dados; separar tecnologia de clima. |
| 0006 | Modelo interpretável | Linear em JSON legível (os 3 modelos empataram → ficou o simples). |
| 0007 | What-if de plantio | Fenologia por calor + "backtest" climatológico; é comparativo, honesto. |
| 0008 | Otimização com risco | Escolher data por alta produtividade **E** estabilidade, dentro do ZARC. |
| 0009 | Persistência do ground truth | Entidades mínimas (Farm/Field/CropCycle); SQLite simples; capturar ≠ treinar. |
| 0010 | Assistente determinístico | Roteia por regras; LLM opcional; nunca gera número. |
| 0011 | Gêmeo digital por eventos | Uma tabela flexível de eventos; estado derivado na leitura (não event sourcing). |
| 0012 | Personalização (shrinkage) | Encolhimento bayesiano; incerteza **nunca** diminui artificialmente. |
| 0013 | Calibração | Medir se as faixas são honestas (cobertura + Wilson); descartar CRPS (redundante). |
| 0014 | Inteligência por talhão | Descritivo agora; perfis por talhão/cultivar adiados (falta dado / confundimento). |
| 0015 | Produto na safra | Quick capture + presets + plano×real + agenda; rejeitar OCR e CropPlan separado. |
| 0016 | Apoio à decisão | Alertas nomeados, **não** score único mágico; sem prescrição agronômica. |
| 0017 | Robustez V1 | CORS (a causa do "não conecta"), /system, demo, export, contexto global. |

## Exemplos de "coisas que NÃO foram feitas" — e por quê (isto é qualidade!)

Saber **dizer não** é tão importante quanto saber fazer. O FADA rejeitou conscientemente:

- **Deep learning** — pouco dado; traria caixa-preta sem ganho.
- **Prever preço de commodity** — quase impossível de forma confiável; o preço é input.
- **Score único de prioridade** — falsa precisão; misturar grandezas diferentes num
  número é enganoso. Trocado por **alertas nomeados**.
- **Recomendação agronômica** ("aplique X na dose Y") — exige modelos validados e
  responsabilidade técnica. O FADA aponta **onde olhar**, não **o que fazer**.
- **OCR de notas fiscais, microsserviços, event sourcing** — complexidade prematura.
- **Perfis por cultivar** — em dado observacional, o efeito do cultivar é **confundido**
  com clima/talhão/manejo; afirmar seria desonesto sem mais dados.

## Resumo do capítulo

O FADA é guiado por **princípios** (determinismo, honestidade, incerteza, evidência,
flywheel, baixo atrito), e cada decisão grande está registrada num **ADR**. A disciplina
de **descartar** o que é prematuro ou cientificamente fraco é parte central da qualidade.

➡️ Próximo: **[Capítulo 12 — Glossário](12-glossario.md)**.
