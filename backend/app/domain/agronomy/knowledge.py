"""Base de conhecimento agronômico citável — o "guia" do FADA (ADR-0027).

Cada fator/tema do Perfil Agronômico ganha uma explicação **com fonte citada**
(Embrapa Soja, CQFS-RS/SC, Consórcio Antiferrugem, ZARC/MAPA). É a camada de
*insight* que explica **por que** uma variável pesa — sem gerar número (o número é
do domínio determinístico). Determinística e curada; é a fundação sobre a qual um
RAG (busca vetorial + LLM citando fonte) pode assentar depois.

Honestidade: citamos as **fontes/instituições** reconhecidas, não números de
portaria/página que não possamos verificar. O texto é educativo e deve ser
confirmado com o agrônomo do produtor.
"""

from __future__ import annotations

from dataclasses import dataclass

# Fontes reconhecidas (instituições/referências reais).
EMBRAPA = "Embrapa Soja — Tecnologias de Produção de Soja"
CQFS = "CQFS-RS/SC (2016) — Manual de Calagem e Adubação para RS e SC"
ANTIFERRUGEM = "Consórcio Antiferrugem (Embrapa)"
ZARC = "ZARC — Zoneamento Agrícola de Risco Climático (MAPA)"
AGROFIT = "Agrofit (MAPA) — defensivos registrados"


@dataclass(frozen=True)
class KnowledgeEntry:
    key: str
    title: str
    explanation: str
    practical: str          # nota prática/acionável
    sources: tuple[str, ...]


def _e(key, title, explanation, practical, sources) -> KnowledgeEntry:
    return KnowledgeEntry(key, title, explanation, practical, tuple(sources))


# Entradas por fator do perfil (chaves alinhadas com domain/agronomy/profile).
KNOWLEDGE: dict[str, KnowledgeEntry] = {e.key: e for e in [
    _e("fungicida", "Programa de fungicida (ferrugem asiática)",
       "A ferrugem asiática (Phakopsora pachyrhizi) é a doença mais severa da soja "
       "no Brasil e pode causar perdas elevadas sem controle adequado. O manejo eficaz "
       "combina cultivar, época de semeadura, monitoramento e fungicidas no momento "
       "certo, evitando o uso isolado e repetido do mesmo princípio ativo (resistência).",
       "Mantenha um programa preventivo/curativo conforme o monitoramento regional; "
       "rotacione princípios ativos.",
       [ANTIFERRUGEM, EMBRAPA]),
    _e("inoculacao", "Inoculação (fixação biológica de nitrogênio)",
       "A soja supre praticamente todo o nitrogênio pela fixação biológica via rizóbio "
       "(Bradyrhizobium). Sem inoculação eficiente, há limitação de N e queda de "
       "produtividade; a reinoculação anual é recomendada.",
       "Inocule sempre, com inoculante de qualidade e cuidados na semeadura; "
       "co-inoculação pode beneficiar.",
       [EMBRAPA]),
    _e("acidez_corrigida", "Correção de acidez (calagem)",
       "pH baixo e alta saturação por alumínio limitam o crescimento radicular, a "
       "nodulação e a absorção de nutrientes. A calagem corrige a acidez e eleva a "
       "saturação por bases ao nível adequado à cultura.",
       "Faça calagem com base na análise de solo (CQFS); o efeito é gradual — planeje "
       "com antecedência à semeadura.",
       [CQFS, EMBRAPA]),
    _e("fertilidade_p", "Fósforo (P)",
       "O fósforo é frequentemente limitante em solos do Sul; teores abaixo do nível "
       "crítico (por classe de argila) reduzem o teto produtivo. A interpretação segue "
       "as faixas da CQFS-RS/SC.",
       "Construa a fertilidade de P a níveis adequados e faça adubação de manutenção "
       "conforme a exportação da cultura.",
       [CQFS]),
    _e("fertilidade_k", "Potássio (K)",
       "O potássio atua no enchimento de grãos e na tolerância a estresses; teores "
       "abaixo do crítico (por CTC) limitam a produtividade. Interpretação pela CQFS.",
       "Ajuste a adubação potássica à análise e à expectativa de produtividade; "
       "atenção a perdas por lixiviação em solos arenosos.",
       [CQFS]),
    _e("janela_plantio", "Época de semeadura (ZARC)",
       "Semear na janela indicada pelo ZARC posiciona a fase reprodutiva no período de "
       "menor risco climático (hídrico/térmico) do município, reduzindo a chance de "
       "perda. A janela varia por solo e ciclo da cultivar.",
       "Priorize a janela ZARC do seu município/solo/ciclo; ela também é exigência de "
       "crédito e seguro (Proagro).",
       [ZARC, EMBRAPA]),
    _e("cultivar", "Cultivar / potencial genético",
       "Cultivares modernas reúnem maior potencial produtivo, estabilidade e sanidade "
       "(resistência a doenças/nematoides). A escolha deve considerar grupo de "
       "maturação, hábito e adaptação à região.",
       "Escolha cultivares adaptadas à sua microrregião e ao manejo; diversifique "
       "grupos de maturação para diluir risco.",
       [EMBRAPA]),
    _e("rotacao", "Rotação de culturas",
       "A rotação (ex.: milho, braquiária) melhora a estrutura e a biologia do solo, "
       "aumenta a palhada e quebra ciclos de pragas/doenças/nematoides; a monocultura "
       "de soja tende a agravar esses problemas.",
       "Inclua gramíneas na rotação/sucessão para solo e fitossanidade.",
       [EMBRAPA]),
    _e("nematoides", "Nematoides",
       "Nematoides (cisto, galhas, lesões) reduzem a absorção de água e nutrientes e "
       "podem causar grandes perdas. O manejo integra rotação, cultivares resistentes "
       "e qualidade do solo.",
       "Faça amostragem para identificar a espécie; combine rotação + cultivar "
       "resistente.",
       [EMBRAPA]),
    _e("textura_solo", "Textura do solo e água disponível",
       "Solos mais argilosos retêm mais água disponível e amparam veranicos; arenosos "
       "têm menor reserva e sofrem mais em estiagem (sequeiro). A textura condiciona o "
       "risco hídrico do talhão.",
       "Em solos arenosos, atenção redobrada à época de semeadura e à cobertura/"
       "palhada para reduzir perdas em ano seco.",
       [EMBRAPA]),
    _e("plantio_direto", "Sistema plantio direto / palhada",
       "O plantio direto consolidado, com palhada e rotação, melhora a infiltração, a "
       "retenção de água e a estrutura do solo, reduzindo erosão e amenizando "
       "veranicos.",
       "Mantenha cobertura e rotação para colher os benefícios do PD ao longo do tempo.",
       [EMBRAPA]),
    _e("manejo_pragas", "Manejo integrado de pragas (MIP)",
       "O MIP usa monitoramento e nível de dano para decidir o controle, reduzindo "
       "aplicações desnecessárias e preservando inimigos naturais; percevejos e "
       "lagartas mal manejados reduzem grãos e qualidade.",
       "Monitore e respeite os níveis de ação; preserve inimigos naturais.",
       [EMBRAPA, AGROFIT]),
    _e("manejo_daninhas", "Manejo de plantas daninhas",
       "Plantas daninhas (ex.: buva, capim-amargoso) competem por água, luz e "
       "nutrientes e podem causar perdas relevantes; o manejo integrado e a rotação de "
       "mecanismos de ação evitam resistência.",
       "Controle no momento certo e rotacione mecanismos de ação dos herbicidas.",
       [EMBRAPA, AGROFIT]),
]}


# Temas transversais (clima/decisão), além dos fatores do perfil.
TOPICS: dict[str, KnowledgeEntry] = {e.key: e for e in [
    _e("veranico", "Veranico (estiagem na fase crítica)",
       "Períodos secos durante o florescimento/enchimento de grãos são o principal "
       "fator de perda da soja de sequeiro no RS. A vulnerabilidade depende do solo "
       "(retenção de água) e da época de semeadura.",
       "Posicione a fase reprodutiva fora do período de maior risco (ZARC) e cuide da "
       "água disponível do solo.",
       [EMBRAPA, ZARC]),
    _e("geada", "Risco de geada",
       "Geadas causam dano por baixas temperaturas em fases sensíveis; a previsão é "
       "probabilística e o risco varia com topografia e umidade.",
       "Acompanhe a previsão; avalie proteção/colheita conforme o estádio e a "
       "severidade prevista.",
       [EMBRAPA]),
]}


def for_factor(key: str) -> KnowledgeEntry | None:
    return KNOWLEDGE.get(key) or TOPICS.get(key)


def guide() -> list[KnowledgeEntry]:
    """Todas as entradas (fatores + temas), para a página de Guia."""
    return list(KNOWLEDGE.values()) + list(TOPICS.values())
