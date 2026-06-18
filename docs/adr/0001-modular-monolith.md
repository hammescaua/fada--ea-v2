# ADR-0001 — Modular monolith em vez de microsserviços

**Status:** Aceito · **Data:** 2026-06-16

## Contexto
O conceito original sugere um sistema multi-agente amplo, o que facilmente leva à
tentação de microsserviços (um serviço por "agente"). O desenvolvimento inicial é
conduzido por um **founder técnico solo**.

## Decisão
Construir um **modular monolith**: um único deploy FastAPI, organizado por
*bounded contexts* (DDD) com fronteiras internas explícitas. Cada contexto é um
pacote Python isolado, com dependências unidirecionais e sem I/O no núcleo.

## Justificativa
- Microsserviços impõem custo de rede, deploy, observabilidade e consistência
  distribuída — proibitivo para um time de uma pessoa.
- Fronteiras limpas internas permitem **extrair** um contexto em serviço no futuro,
  quando a escala (e não a estética) justificar.
- Velocidade de iteração é a métrica que mais importa no estágio atual.

## Consequências
- (+) Deploy e debugging simples; refactor barato dentro do processo.
- (+) Caminho de migração para serviços preservado pelas fronteiras de contexto.
- (−) Disciplina de import é responsabilidade do dev (mitigado por testes de
  arquitetura e revisão).
