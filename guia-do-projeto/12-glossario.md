# Capítulo 12 — Glossário (dicionário de termos)

Consulte aqui sempre que travar num termo. Em ordem alfabética.

### Termos de software

- **API** — o conjunto de "endereços" pelos quais o frontend conversa com o backend. (O
  garçom do restaurante.)
- **Backend** — o "cérebro" do sistema, que faz as contas e fala com o banco. (A cozinha.)
- **Banco de dados** — onde a informação é guardada de forma permanente. No FADA dev, o
  arquivo SQLite. (A despensa.)
- **Bug** — um erro/defeito no programa.
- **Build** — o processo de "empacotar" o frontend pronto para uso. "Build OK" = empacotou
  sem erros.
- **Cache** — uma cópia guardada de algo que já foi buscado, para não buscar de novo.
- **Camada** — uma "fatia" do sistema com um papel (API, serviço, domínio, infra).
- **Cliente** — quem faz o pedido (o frontend no seu navegador).
- **Commit** — uma "foto" salva das mudanças do código num momento (no Git).
- **Componente** — um "bloco" reutilizável de interface (um botão, um card).
- **CORS** — uma permissão de segurança que deixa o frontend (numa origem) conversar com
  o backend (em outra). Sem ela, dá o erro "não foi possível conectar".
- **Deploy** — colocar o sistema "no ar" para uso real.
- **Determinístico** — mesma entrada → sempre o mesmo resultado. (2+2 sempre 4.)
- **DDD** (Domain-Driven Design) — organizar o código **por assunto do negócio**.
- **Endpoint** — um "endereço" específico da API (ex.: `/api/v1/farms`).
- **Frontend** — "a cara" do sistema, as telas no navegador. (O salão.)
- **Framework** — uma estrutura/esqueleto pronto sobre o qual você constrói (ex.: Next.js).
- **Git / GitHub** — sistema de histórico do código / site que o guarda na nuvem.
- **HTTP** — o "protocolo" (regras) de conversa pela web. `GET` busca, `POST` cria/envia.
- **ID** — um número único que identifica algo no banco (ex.: a fazenda nº 5). O FADA
  esconde isso do usuário final, mostrando **nomes**.
- **JSON** — formato de texto para empacotar dados de forma organizada.
- **Lint / ruff** — verificação automática de estilo/limpeza do código.
- **localhost** — "este computador aqui mesmo".
- **Monólito modular** — o backend é um único programa, mas bem dividido por dentro.
- **ORM** — ferramenta que traduz "objetos do código" ↔ "tabelas do banco" (SQLAlchemy).
- **Porta** — o "número da sala" onde um programa atende (backend: 8000; frontend: 3000).
- **Pipeline** — uma "receita" automatizada (ex.: baixar dados → treinar modelo).
- **Repositório (repo)** — a pasta do projeto inteiro, versionada pelo Git.
- **Requisição / Resposta** — o pedido do cliente / o retorno do servidor.
- **Servidor** — o computador que atende os pedidos (o backend).
- **Status (200, 404, 422, 500)** — número que diz se a resposta deu certo ou o tipo de
  erro.
- **Tipo (TypeScript)** — a "categoria" de um dado (número, texto…). Tipos pegam erros cedo.
- **Variável de ambiente** — um ajuste de configuração que fica fora do código (ex.: o
  endereço do banco, ou `NEXT_PUBLIC_API_URL`).

### Termos de IA / dados / estatística

- **Calibração** — verificar se as faixas de incerteza são honestas (se "80%" é 80% mesmo).
- **Cenários (pessimista/normal/otimista)** — três resultados possíveis para uma previsão,
  refletindo anos de clima ruim/médio/bom.
- **Cobertura (coverage)** — de quantas vezes a faixa de incerteza realmente conteve a
  realidade.
- **Encolhimento (shrinkage)** — puxar um ajuste para perto de zero quando há pouca
  evidência. É a base da personalização cética do FADA.
- **Evidence gating** — só afirmar algo se houver dados suficientes (N) e efeito claro.
- **Feature** — cada "ingrediente" que entra no modelo (ex.: déficit hídrico).
- **Ground truth** — a "verdade-terreno", o dado real observado (ex.: a colheita real).
- **Intervalo de confiança / incerteza** — a faixa em torno da previsão ("de 40 a 62").
- **LLM** — modelo de linguagem (tipo ChatGPT). No FADA: só entende perguntas e explica;
  **nunca** gera número.
- **Machine learning** — "aprendizado de máquina": ensinar um modelo com exemplos.
- **Modelo** — a "fórmula aprendida de dados" que faz a previsão.
- **Property-based testing** — testar uma regra com milhares de entradas aleatórias.
- **Reprodutibilidade** — outra pessoa conseguir refazer os mesmos resultados.
- **Regressão linear** — modelo simples = soma ponderada de fatores. O escolhido no FADA.
- **Saca** — unidade comercial = 60 kg (para soja).

### Termos do agronegócio (que aparecem no projeto)

- **Cultivar / híbrido** — a "variedade" da semente.
- **Déficit hídrico** — falta de água para a planta (água que ela precisava menos a chuva).
- **Fenologia** — as fases de desenvolvimento da planta (emergência, floração, etc.).
- **Período reprodutivo (R1–R6)** — a fase crítica de florada e enchimento de grãos, onde
  a falta de água mais machuca.
- **Talhão** — um pedaço/divisão da terra dentro da fazenda.
- **Veranico** — uma sequência de dias sem chuva no meio da safra.
- **ZARC** — Zoneamento Agrícola de Risco Climático, a janela oficial recomendada de
  plantio.

➡️ Próximo: **[Capítulo 13 — Como rodar e estudar](13-como-rodar-e-estudar.md)**.
