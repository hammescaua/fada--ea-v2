"""Planejamento de safra (pré-safra) — o brief de decisão que sintetiza tudo.

Pilar do produto: usar o FADA **antes** de plantar. Compõe os serviços
determinísticos numa só resposta — produtividade esperada (±), janela de plantio
ZARC oficial, melhor data (otimizador), preço observado e custo de referência —
e projeta a **margem esperada** e o **ponto de equilíbrio**. Apoio à decisão, não
promessa: cada seção é opcional e degrada graciosamente se a fonte faltar.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.agronomy import (
    apply_adjustment,
    compute_adjustment,
    compute_cost_adjustment,
    economic_recommendations,
    scenario_multipliers,
)
from app.domain.planning.season import season_margin
from app.services.benchmark import BenchmarkService, BenchmarkUnavailable
from app.services.market import MarketService, PriceUnavailable
from app.services.planting_date import PlantingDateService
from app.services.regional_intelligence import (
    MunicipalityNotInRegion,
    RegionalIntelligenceService,
)
from app.services.zarc import MunicipalityNotInZarc, ZarcService, ZarcUnavailable


@dataclass
class SeasonPlanningService:
    regional: RegionalIntelligenceService
    planting: PlantingDateService
    zarc: ZarcService
    market: MarketService
    benchmark: BenchmarkService

    def brief(
        self,
        municipality: str,
        crop: str = "soja",
        season: str = "2026/27",
        uf: str = "RS",
        price_per_bag: float | None = None,
        profile: dict[str, str] | None = None,
    ) -> dict:
        # 1) Produtividade regional (obrigatória — é a âncora do brief).
        reg = self.regional.run(municipality, crop, season)
        code = reg["municipality_code"]
        scenarios = {s["name"]: s["yield_sc_ha"] for s in reg["scenarios"]}
        expected = reg["estimated_yield_sc_ha"]
        interval = list(reg["confidence_interval_sc_ha"])

        # 1b) Personalização a priori pelo Perfil Agronômico (ADR-0022), se houver.
        # Quando há perfil, a produtividade — e portanto a margem — passam a ser do
        # talhão, não da média regional. Incerteza alarga (nunca estreita).
        adjustment_block = None
        if profile:
            adj = compute_adjustment(profile)
            est = apply_adjustment(
                expected, tuple(interval), scenarios, adj,
                scenario_multipliers=scenario_multipliers(profile),
            )
            expected = est.personalized_point_sc_ha
            interval = list(est.personalized_interval_sc_ha)
            scenarios = est.scenarios_sc_ha
            adjustment_block = {
                "multiplier": est.multiplier,
                "total_effect_pct": est.total_effect_pct,
                "regional_point_sc_ha": est.regional_point_sc_ha,
                "n_factors": adj.n_factors,
                "factors": [vars(a) for a in adj.applied],
            }

        scenarios_payload = [{"name": n, "yield_sc_ha": y} for n, y in scenarios.items()]
        yield_block = {
            "expected_sc_ha": expected,
            "interval_sc_ha": interval,
            "scenarios": scenarios_payload,
            "risks": reg["climatic_risks"],
            "n_years": reg["n_years"],
            "personalized": adjustment_block is not None,
            "adjustment": adjustment_block,
        }

        # 2) Janela de plantio: ZARC oficial + melhor data do otimizador (opcionais).
        planting_block = {
            "zarc": self._zarc(code, crop, uf),
            "best_date": self._best_date(municipality, crop, season),
        }

        # 3) Preço observado (CEPEA) e 4) custo de referência (CONAB) — opcionais.
        price_block = self._price(crop, price_per_bag)
        cost_block = self._cost(crop, uf)

        # 5) Margem só quando há preço E custo. Com perfil, o custo de referência
        # também é personalizado (rentabilidade única por talhão).
        margin_block = None
        if price_block is not None and cost_block is not None:
            costs = {
                "coe": cost_block["coe_per_ha"],
                "cot": cost_block["cot_per_ha"],
                "ct": cost_block["ct_per_ha"],
            }
            cost_adj_block = None
            if profile:
                cadj = compute_cost_adjustment(profile)
                if cadj.multiplier != 1.0:
                    costs = {k: round(v * cadj.multiplier, 2) for k, v in costs.items()}
                    cost_adj_block = {
                        "multiplier": cadj.multiplier,
                        "total_effect_pct": cadj.total_effect_pct,
                        "reference_cot_per_ha": cost_block["cot_per_ha"],
                        "factors": [vars(a) for a in cadj.applied],
                    }
            margin_block = season_margin(
                yield_scenarios=scenarios,
                expected_yield_sc_ha=expected,
                price_per_bag=price_block["price_per_bag"],
                costs_per_ha=costs,
            )
            margin_block["cost_adjustment"] = cost_adj_block

        # 6) Recomendações na linguagem do produtor (ganho líquido R$/ha) — exige
        # perfil + preço + custo de referência.
        recommendations_block = None
        if profile and price_block is not None and cost_block is not None:
            recs = economic_recommendations(
                profile=profile,
                personalized_point_sc_ha=expected,
                price_per_bag=price_block["price_per_bag"],
                reference_cost_per_ha=cost_block["cot_per_ha"],
            )
            recommendations_block = [vars(r) for r in recs]

        return {
            "municipality": reg["municipality"],
            "municipality_code": code,
            "crop": crop,
            "season": season,
            "harvest_year": reg["harvest_year"],
            "yield": yield_block,
            "planting": planting_block,
            "price": price_block,
            "cost": cost_block,
            "margin": margin_block,
            "recommendations": recommendations_block,
            "verdict": _verdict(
                reg["municipality"], expected, margin_block, recommendations_block
            ),
            "data_sources": _sources(price_block, cost_block, planting_block),
            "disclaimer": (
                "Síntese de apoio à decisão pré-safra a partir de dados públicos "
                "oficiais. Produtividade é estimativa probabilística (não garantia); "
                "preço é observado (não previsto); custo é referência regional CONAB."
            ),
        }

    # -- seções opcionais (degradação graciosa) -----------------------------

    def _zarc(self, code: int, crop: str, uf: str) -> dict | None:
        try:
            return self.zarc.planting_window(code, crop, uf)
        except (ZarcUnavailable, MunicipalityNotInZarc):
            return None

    def _best_date(self, municipality: str, crop: str, season: str) -> dict | None:
        try:
            res = self.planting.optimize(municipality, crop, season)
        except (MunicipalityNotInRegion, Exception):  # noqa: BLE001 — opcional
            return None
        recs = res.get("top_recommendations") or []
        if not recs:
            return None
        top = recs[0]
        return {
            "planting_date": top["planting_date"],
            "expected_yield_sc_ha": top["expected_yield_sc_ha"],
            "downside_sc_ha": top["downside_sc_ha"],
            "justification": top["justification"],
        }

    def _price(self, crop: str, price_per_bag: float | None) -> dict | None:
        if price_per_bag is not None and price_per_bag > 0:
            return {"price_per_bag": round(price_per_bag, 2), "source": "informado pelo produtor"}
        try:
            data = self.market.price(crop)
        except PriceUnavailable:
            return None
        s = data["summary"]
        return {
            "price_per_bag": s.latest_value,
            "source": data["source"],
            "day": s.latest_day.isoformat(),
            "unit": data["unit"],
            "is_stale": s.is_stale,
        }

    def _cost(self, crop: str, uf: str) -> dict | None:
        try:
            return self.benchmark.cost_benchmark(crop, uf)
        except BenchmarkUnavailable:
            return None


def _verdict(
    municipality: str, expected: float, margin: dict | None,
    recommendations: list[dict] | None = None,
) -> str:
    if margin is None:
        return (
            f"Produtividade esperada de {expected} sc/ha em {municipality}. "
            "Para fechar a conta da margem, falta preço e/ou custo de referência."
        )
    exp = margin["expected"]
    be_cot = margin["break_even_yield_sc_ha"]["cot"]
    direction = "acima" if expected >= be_cot else "abaixo"
    base = (
        f"À produtividade esperada ({expected} sc/ha) e ao preço de "
        f"R$ {margin['price_per_bag']:.2f}/sc, a margem esperada sobre o custo "
        f"operacional total (CONAB) é R$ {exp['profit_per_ha']:.0f}/ha "
        f"({exp['margin_pct']:.0f}%). O ponto de equilíbrio é {be_cot} sc/ha — a "
        f"expectativa está {direction} dele."
    )
    if recommendations:
        top = recommendations[0]
        if top["net_gain_rs_ha"] > 0:
            base += (
                f" Ação de maior retorno: {top['question'].lower()} "
                f"({top['current_label']} → {top['target_label']}), "
                f"+R$ {top['net_gain_rs_ha']:.0f}/ha líquidos."
            )
    return base


def _sources(price: dict | None, cost: dict | None, planting: dict) -> list[str]:
    src = ["IBGE/PAM + reanálise climática (produtividade regional)"]
    if planting.get("zarc"):
        src.append("ZARC/MAPA (janela de plantio oficial)")
    if price and price.get("source", "").startswith("CEPEA"):
        src.append("CEPEA/ESALQ (preço observado)")
    if cost:
        src.append("CONAB (custo de produção de referência)")
    return src
