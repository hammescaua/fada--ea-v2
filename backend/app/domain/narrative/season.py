"""Leitura da safra em linguagem natural — explica a projeção para o agricultor.

Transforma os **números já computados** pelo domínio (produtividade, cenários,
preço, custo, margem, ação de maior retorno) em parágrafos claros em português,
amarrando os *porquês* (perfil, clima do ano, ZARC) com honestidade (incerteza
sempre na mesa; preço observado, não previsto).

Puro e determinístico — não inventa número, só verbaliza. Quando houver chave de
LLM, o mesmo conjunto de fatos pode ser refraseado de forma mais fluida (ADR-0002),
mas o conteúdo factual é este.
"""

from __future__ import annotations


def _brl(v: float) -> str:
    return f"R$ {v:,.0f}".replace(",", ".")


def _n(v: float) -> str:
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _scenario(brief: dict, name: str) -> float | None:
    for s in brief["yield"]["scenarios"]:
        if s["name"] == name:
            return s["yield_sc_ha"]
    return None


def narrate_brief(brief: dict) -> list[str]:
    """Retorna a leitura da safra como parágrafos curtos (linguagem natural)."""
    y = brief["yield"]
    muni, season = brief["municipality"], brief["season"]
    lo, hi = y["interval_sc_ha"]
    paras: list[str] = []

    # 1) Produtividade e por quê
    p1 = (
        f"Para a safra {season} em {muni}, a expectativa é de cerca de "
        f"{_n(y['expected_sc_ha'])} sc/ha (faixa provável de {_n(lo)} a {_n(hi)})."
    )
    adj = y.get("adjustment")
    if y.get("personalized") and adj:
        eff = adj["total_effect_pct"]
        direction = "acima" if eff >= 0 else "abaixo"
        drivers = [f["question"].lower() for f in adj.get("factors", [])[:2]]
        if drivers:
            p1 += (
                f" Isso é {_n(abs(eff))}% {direction} da média da região, sobretudo por "
                f"{' e '.join(drivers)}."
            )
    pess = _scenario(brief, "pessimista")
    if pess is not None:
        p1 += f" Num ano seco (veranico), pode cair para ~{_n(pess)} sc/ha — o principal risco da região."
    paras.append(p1)

    # 2) Decisão econômica
    margin = brief.get("margin")
    price = brief.get("price")
    if margin and price:
        exp = margin["expected"]
        be = margin["break_even_yield_sc_ha"]["cot"]
        src = "cotação CEPEA" if str(price.get("source", "")).startswith("CEPEA") else "preço informado"
        sit = "fecha a conta com folga" if y["expected_sc_ha"] >= be * 1.1 else (
            "fica no limite" if y["expected_sc_ha"] >= be else "não cobre o custo de referência"
        )
        verb = "sobra" if exp["profit_per_ha"] >= 0 else "falta"
        p2 = (
            f"Ao preço de {_brl(price['price_per_bag'])}/sc ({src}) e custo de referência "
            f"CONAB de {_brl(margin['cost_per_ha_cot'])}/ha, a margem esperada é "
            f"{_brl(abs(exp['profit_per_ha']))}/ha ({verb}). O ponto de equilíbrio é "
            f"{_n(be)} sc/ha — a expectativa {sit}."
        )
        paras.append(p2)
    else:
        paras.append(
            "Para fechar a conta da margem (lucro e ponto de equilíbrio), falta preço "
            "e/ou custo de referência — rode os pipelines de cotação/custo."
        )

    # 3) Ação de maior retorno + janela ZARC
    recs = brief.get("recommendations") or []
    bits = []
    if recs and recs[0].get("net_gain_rs_ha", 0) > 0:
        top = recs[0]
        bits.append(
            f"a ação de maior retorno é {top['question'].lower()} "
            f"({top['current_label'].lower()} → {top['target_label'].lower()}), "
            f"valendo cerca de {_brl(top['net_gain_rs_ha'])}/ha líquidos"
        )
    zarc = brief.get("planting", {}).get("zarc")
    if zarc:
        wins = zarc.get("windows_by_risk", {}).get("20") or []
        if wins:
            w = wins[0]
            bits.append(f"a janela de plantio ZARC (risco 20%) vai de {w['start']} a {w['end']}")
    best = brief.get("planting", {}).get("best_date")
    if best:
        bits.append(f"a data mais robusta estimada é {best['planting_date']}")
    if bits:
        paras.append("Para decidir: " + "; ".join(bits) + ".")

    # 4) Ressalva honesta
    paras.append(
        "Lembre: produtividade é estimativa probabilística (não garantia), o preço é "
        "observado (não previsto) e o custo é referência regional — a previsão melhora "
        "conforme você registra as colheitas do seu talhão."
    )
    return paras
