# 📚 Guia Completo do FADA — para quem está começando do zero

Bem-vindo! Este guia explica **todo o projeto FADA**, do começo ao fim, para uma
pessoa que **não é da área de software nem de inteligência artificial**. A ideia é
que você consiga, com calma, entender o que o sistema faz, como ele é construído por
dentro, quais tecnologias usa e **por que** cada decisão foi tomada.

> Não precisa ler tudo de uma vez. Cada capítulo é independente o suficiente para
> você ir no seu ritmo. Se travar num termo técnico, consulte o **Capítulo 12 —
> Glossário**, que explica cada palavra difícil em linguagem simples.

---

## Como este guia está organizado

| Capítulo | Sobre o quê | Para quê serve |
|---|---|---|
| **[01 — O que é o FADA](01-o-que-e-o-fada.md)** | O produto, em linguagem de gente | Entender o "para quê isso existe" |
| **[02 — Conceitos de software](02-conceitos-de-software.md)** | Backend, frontend, API, banco de dados… | Ter a base para entender o resto |
| **[03 — Conceitos de IA e modelos](03-conceitos-de-ia-e-modelos.md)** | Modelo, previsão, incerteza, LLM | Entender a parte "inteligente" sem matemática |
| **[04 — Arquitetura geral](04-arquitetura-geral.md)** | Como as peças se encaixam | A visão de cima do sistema |
| **[05 — Tecnologias usadas](05-tecnologias-usadas.md)** | Cada ferramenta e o porquê | Saber o que é Python, FastAPI, Next.js… |
| **[06 — Estrutura de pastas](06-estrutura-de-pastas.md)** | O mapa dos arquivos | Achar as coisas no projeto |
| **[07 — O backend por dentro](07-backend-por-dentro.md)** | Cada parte do "cérebro" | Entender onde vivem as contas |
| **[08 — Dados e modelos](08-dados-e-modelos.md)** | De onde vêm os números | Entender a base científica |
| **[09 — O frontend por dentro](09-frontend-por-dentro.md)** | Cada tela do aplicativo | Entender o que o usuário vê |
| **[10 — Uma ação de ponta a ponta](10-ponta-a-ponta.md)** | O caminho completo de um clique | Ver tudo funcionando junto |
| **[11 — Princípios e porquês](11-principios-e-porques.md)** | As regras de ouro do projeto | Entender a "filosofia" |
| **[12 — Glossário](12-glossario.md)** | Dicionário de termos | Consultar quando travar |
| **[13 — Como rodar e estudar](13-como-rodar-e-estudar.md)** | Mão na massa | Explorar você mesmo |

---

## Resumo de um parágrafo (para já sair sabendo)

O **FADA** (Farm AI Decision Agent, ou "Agente de Decisão Agrícola com IA") é um
programa que ajuda um **produtor de soja** a tomar decisões: *quanto vou colher?
quanto vou gastar? quanto vou lucrar? qual a melhor data de plantio? qual talhão
merece atenção?* Ele junta **dados públicos** (clima, produtividade da região) com os
**dados da fazenda** (o que o produtor registra) e transforma isso em **respostas com
números honestos** — sempre mostrando a margem de incerteza. Tem duas grandes partes:
um **"cérebro"** que faz as contas (chamado *backend*) e uma **"cara"** com telas que o
usuário usa (chamado *frontend*).

Boa leitura! 🌱
