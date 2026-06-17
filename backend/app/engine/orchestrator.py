"""Orchestrator conversacional — roteia intenção e explica, sem gerar números.

Interpreta a pergunta do agricultor, escolhe qual serviço determinístico chamar e
verbaliza o resultado. O LLM (quando há chave) só faz roteamento/explicação; todos
os números vêm dos domain services (ADR-0002, ADR-0010).

Roteamento determinístico (offline, testável) é o padrão; um roteador via Claude é
opcional e cai no determinístico em qualquer falha.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from enum import Enum

from app.services.adaptive import AdaptiveService, FarmNotFound
from app.services.cost import AreaUnknown, CostService, CycleNotFound
from app.services.planting_date import PlantingDateService
from app.services.regional_intelligence import (
    MunicipalityNotInRegion,
    RegionalIntelligenceService,
)

DEFAULT_SEASON = "2026/27"

_MONTHS = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}


class Intent(str, Enum):
    REGIONAL = "regional_intelligence"
    SIMULATION = "planting_simulation"
    OPTIMIZATION = "planting_optimization"
    COST_TOTAL = "cost_total"
    COST_PER_HECTARE = "cost_per_hectare"
    APPLICATIONS = "applications_count"
    BREAK_EVEN = "break_even"
    ABOVE_AVERAGE = "above_average"
    LEARNED = "learned"
    RELIABILITY = "reliability"
    REGIONAL_VS_PERSONALIZED = "regional_vs_personalized"
    MODEL_RELIABILITY = "model_reliability"
    INTERVALS_CALIBRATED = "intervals_calibrated"
    BIAS_DIRECTION = "bias_direction"
    PERSONALIZED_BETTER = "personalized_better"
    UNKNOWN = "unknown"


COST_INTENTS = frozenset(
    {Intent.COST_TOTAL, Intent.COST_PER_HECTARE, Intent.APPLICATIONS, Intent.BREAK_EVEN}
)
ADAPTIVE_INTENTS = frozenset(
    {Intent.ABOVE_AVERAGE, Intent.LEARNED, Intent.RELIABILITY, Intent.REGIONAL_VS_PERSONALIZED}
)
CALIBRATION_INTENTS = frozenset(
    {Intent.MODEL_RELIABILITY, Intent.INTERVALS_CALIBRATED, Intent.BIAS_DIRECTION,
     Intent.PERSONALIZED_BETTER}
)


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


@dataclass
class Routed:
    intent: Intent
    municipality: str | None
    season: str
    planting_date: str | None


class DeterministicRouter:
    """Extrai intenção e slots por regras — base do orchestrator."""

    def __init__(self, known_municipalities: list[str]) -> None:
        # mapa nome_normalizado -> canônico, ordenado por tamanho (match mais específico)
        self._munis = sorted(known_municipalities, key=len, reverse=True)

    def _municipality(self, text: str) -> str | None:
        n = _norm(text)
        for name in self._munis:
            if _norm(name) in n:
                return name
        return None

    def _season(self, text: str) -> str:
        m = re.search(r"\b(20\d{2})\s*/\s*(\d{2})\b", text)
        return f"{m.group(1)}/{m.group(2)}" if m else DEFAULT_SEASON

    def _planting_date(self, text: str, harvest_year: int) -> str | None:
        n = _norm(text)
        plant_year = harvest_year - 1
        # "20 de outubro", "20 out"
        m = re.search(r"\b(\d{1,2})\s*(?:de\s*)?([a-z]{3,9})\b", n)
        if m and m.group(2)[:3] in _MONTHS:
            day, month = int(m.group(1)), _MONTHS[m.group(2)[:3]]
            return _safe_date(plant_year, month, day)
        # "20/10" ou "20-10"
        m = re.search(r"\b(\d{1,2})[/-](\d{1,2})\b", text)
        if m:
            return _safe_date(plant_year, int(m.group(2)), int(m.group(1)))
        # "em novembro" (sem dia) -> dia 1
        for key, month in _MONTHS.items():
            if re.search(rf"\bem\s+{key}", n):
                return _safe_date(plant_year, month, 1)
        return None

    def route(self, message: str, ctx_municipality: str | None) -> Routed:
        n = _norm(message)
        season = self._season(message)
        harvest_year = int(season.split("/")[0]) + 1
        muni = self._municipality(message) or ctx_municipality
        planting = self._planting_date(message, harvest_year)

        # Intenções de calibração (qualidade dos intervalos / do modelo).
        if re.search(r"calibrad|intervalos?\s+(honest|corret|estao|sao)", n):
            return Routed(Intent.INTERVALS_CALIBRATED, muni, season, planting)
        if re.search(r"err\w*\s+(mais\s+)?para\s+(cima|baixo)|super.?prev|sub.?prev|vies", n):
            return Routed(Intent.BIAS_DIRECTION, muni, season, planting)
        if re.search(r"personaliz.*(realmente\s+)?melhor|(vale|compensa).*personaliz|"
                     r"personaliz.*(vale|compensa)", n):
            return Routed(Intent.PERSONALIZED_BETTER, muni, season, planting)
        if re.search(r"(confiav|confianc).*(modelo|sistema)|modelo.*(confiav|confianc)|"
                     r"quao\s+bom\s+(e\s+)?o\s+modelo", n):
            return Routed(Intent.MODEL_RELIABILITY, muni, season, planting)

        # Intenções adaptativas (personalização por fazenda).
        if re.search(r"diferenca.*(regional|personaliz)|regional.*personaliz|"
                     r"personaliz.*regional", n):
            return Routed(Intent.REGIONAL_VS_PERSONALIZED, muni, season, planting)
        if re.search(r"confiav|confianca|quao\s+confi", n):
            return Routed(Intent.RELIABILITY, muni, season, planting)
        if re.search(r"aprend|sobre\s+minha\s+(area|fazenda|lavoura)", n):
            return Routed(Intent.LEARNED, muni, season, planting)
        if re.search(r"acima\s+da\s+media|abaixo\s+da\s+media|costuma\s+produz", n):
            return Routed(Intent.ABOVE_AVERAGE, muni, season, planting)

        # Intenções de custo têm prioridade (palavras como "quanto" são ambíguas).
        if re.search(r"empatar|break.?even|empate", n):
            intent = Intent.BREAK_EVEN
        elif re.search(r"quantas?\s+aplica|quantos?\s+manejo|numero\s+de\s+aplica", n):
            intent = Intent.APPLICATIONS
        elif re.search(r"custo\s+por\s+hectare|custo/ha|por\s+hectare", n):
            intent = Intent.COST_PER_HECTARE
        elif re.search(r"investi|gastei|gastan|custo\s+total|investimento|ja\s+gast", n):
            intent = Intent.COST_TOTAL
        elif re.search(r"melhor\s+(data|epoca|periodo)|qual\s+data|quando\s+plant|otimiz", n):
            intent = Intent.OPTIMIZATION
        elif planting and re.search(r"vale|se\s+eu\s+plant|plantar\s+em|colheria|e\s+se", n):
            intent = Intent.SIMULATION
        elif re.search(r"risco|quanto|produtiv|colher|colheria|safra|expectativa", n):
            intent = Intent.REGIONAL if not planting else Intent.SIMULATION
        else:
            intent = Intent.UNKNOWN
        return Routed(intent, muni, season, planting)


@dataclass
class Orchestrator:
    regional: RegionalIntelligenceService
    planting: PlantingDateService
    cost: CostService
    adaptive: AdaptiveService
    router: DeterministicRouter
    calibration_report: dict | None = None

    def handle(
        self, message: str, ctx_municipality: str | None = None,
        ctx_crop_cycle_id: int | None = None, ctx_price_per_bag: float | None = None,
        ctx_farm_id: int | None = None,
    ) -> dict:
        r = self.router.route(message, ctx_municipality)

        if r.intent in COST_INTENTS:
            return self._dispatch_cost(r, ctx_crop_cycle_id, ctx_price_per_bag)
        if r.intent in ADAPTIVE_INTENTS:
            return self._dispatch_adaptive(r, ctx_farm_id)
        if r.intent in CALIBRATION_INTENTS:
            return self._dispatch_calibration(r)

        if r.municipality is None:
            return self._reply(r, None, "Para responder, preciso do município (ex.: Horizontina).")
        try:
            return self._dispatch(r)
        except MunicipalityNotInRegion:
            return self._reply(
                r, None,
                f"O município '{r.municipality}' está fora da região coberta pelo MVP "
                "(microrregião Três Passos/RS).",
            )

    def _dispatch_cost(
        self, r: Routed, cycle_id: int | None, price: float | None
    ) -> dict:
        if cycle_id is None:
            return self._reply(r, None, "Para responder sobre custos, selecione a safra "
                                        "(crop_cycle_id).")
        try:
            if r.intent == Intent.BREAK_EVEN:
                if price is None:
                    return self._reply(r, None, "Informe o preço da saca (R$/sc) para "
                                                "calcular a produtividade de equilíbrio.")
                fin = self.cost.financials(cycle_id, price)
                answer = (
                    f"Para empatar a R$ {price:.2f}/saca, você precisa de "
                    f"{fin['break_even_yield_sc_ha']} sc/ha (custo de "
                    f"R$ {fin['breakdown'].cost_per_hectare:.2f}/ha)."
                )
                return self._reply(r, _financials_dict(fin), answer)

            b = self.cost.breakdown(cycle_id)
            if r.intent == Intent.COST_TOTAL:
                answer = (f"Você já investiu R$ {b.total_cost:.2f} nesta safra "
                          f"({b.n_applications} aplicações).")
            elif r.intent == Intent.COST_PER_HECTARE:
                answer = f"Seu custo é R$ {b.cost_per_hectare:.2f} por hectare."
            else:  # APPLICATIONS
                answer = f"Você fez {b.n_applications} aplicações nesta safra."
            return self._reply(r, {"breakdown": vars(b)}, answer)
        except CycleNotFound:
            return self._reply(r, None, f"Safra (crop_cycle_id={cycle_id}) não encontrada.")
        except AreaUnknown:
            return self._reply(r, None, "Área desconhecida: informe area_ha na safra ou no talhão.")

    def _dispatch_calibration(self, r: Routed) -> dict:
        rep = self.calibration_report
        if rep is None:
            return self._reply(r, None, "O relatório de calibração ainda não foi computado.")
        reg, per = rep["regional"], rep["personalized"]
        if r.intent == Intent.INTERVALS_CALIBRATED:
            answer = reg["interpretation"]
        elif r.intent == Intent.MODEL_RELIABILITY:
            answer = (f"O modelo é {'calibrado' if not reg['overconfident'] else 'overconfident'}: "
                      f"o IC80 cobriu {reg['coverage_80']:.0%} das safras no backtest "
                      f"(leave-one-year-out, {reg['n_predictions']} casos), MAE {reg['mae']} sc/ha.")
        elif r.intent == Intent.BIAS_DIRECTION:
            b = reg["bias"]
            d = ("super-prever (errar para cima)" if b > 0 else
                 "sub-prever (errar para baixo)" if b < 0 else "não tem viés sistemático")
            answer = (f"Na média, o modelo tende a {d}: viés de {b:+} sc/ha "
                      f"(MAE {reg['mae']} sc/ha).")
        else:  # PERSONALIZED_BETTER
            better = per["mae"] < reg["mae"] and per["pinball"]["mean"] <= reg["pinball"]["mean"]
            verdict = "Sim" if better else "Não de forma conclusiva"
            answer = (f"{verdict}: o personalizado tem MAE {per['mae']} vs {reg['mae']} sc/ha e "
                      f"pinball {per['pinball']['mean']} vs {reg['pinball']['mean']}, mantendo a "
                      f"calibração (IC80 {per['coverage_80']:.0%}) e sem estreitar o intervalo.")
        return self._reply(r, {"regional": reg, "personalized": per}, answer)

    def _dispatch_adaptive(self, r: Routed, farm_id: int | None) -> dict:
        if farm_id is None:
            return self._reply(r, None, "Para responder sobre sua fazenda, selecione-a "
                                        "(farm_id).")
        try:
            res = self.adaptive.personalized_intelligence(farm_id, r.season)
        except FarmNotFound:
            return self._reply(r, None, f"Fazenda (farm_id={farm_id}) não encontrada.")
        except (KeyError, MunicipalityNotInRegion):
            return self._reply(r, None, "Município da fazenda fora da região do modelo.")

        adj, conf = res["farm_adjustment"], res["confidence_score"]
        n = adj["n_cycles"]
        if r.intent == Intent.ABOVE_AVERAGE:
            if n == 0:
                answer = ("Ainda não há safras registradas — não dá para dizer se sua "
                          "fazenda produz acima da média. Registre colheitas.")
            else:
                d = "acima" if adj["observed_bias_pct"] >= 0 else "abaixo"
                answer = (f"Com base em {n} safra(s), sua fazenda produz cerca de "
                          f"{abs(adj['observed_bias_pct'])}% {d} da média regional "
                          f"(confiança {conf:.0%}).")
        elif r.intent == Intent.LEARNED:
            answer = (f"O FADA usou {n} safra(s) reais desta fazenda. Nível de adaptação: "
                      f"{res['adaptation_level']} (confiança {conf:.0%}).")
        elif r.intent == Intent.RELIABILITY:
            answer = (f"A confiabilidade da personalização é {conf:.0%} (adaptação "
                      f"{res['adaptation_level']}, {n} safras). Quanto mais safras "
                      f"consistentes, maior — e a incerteza climática nunca é mascarada.")
        else:  # REGIONAL_VS_PERSONALIZED
            rp = res["regional_prediction"]["point_sc_ha"]
            pp = res["personalized_prediction"]["point_sc_ha"]
            answer = (f"Previsão regional: {rp} sc/ha. Personalizada para sua fazenda: "
                      f"{pp} sc/ha ({adj['applied_pct']:+}% após encolhimento por confiança).")
        return self._reply(r, res, answer)

    def _dispatch(self, r: Routed) -> dict:
        if r.intent == Intent.OPTIMIZATION:
            res = self.planting.optimize(r.municipality, "soja", r.season)
            best = res["top_recommendations"][0]
            answer = (
                f"A data mais robusta para soja em {res['municipality']} na safra "
                f"{r.season} é {best['planting_date']}: produtividade esperada "
                f"{best['expected_yield_sc_ha']} sc/ha, piso {best['downside_sc_ha']} sc/ha "
                f"(P10). {best['justification']}"
            )
            return self._reply(r, res, answer)
        if r.intent == Intent.SIMULATION:
            res = self.planting.simulate(r.municipality, "soja", r.season, r.planting_date)
            answer = (
                f"Plantando em {res['evaluated_planting_date']} em {res['municipality']}: "
                f"produtividade esperada {res['expected_yield_sc_ha']} sc/ha "
                f"({res['delta_vs_baseline_sc_ha']:+} vs data-base), piso "
                f"{res['downside_sc_ha']} sc/ha. {res['explanation']}"
            )
            return self._reply(r, res, answer)
        if r.intent == Intent.REGIONAL:
            res = self.regional.run(r.municipality, "soja", r.season)
            return self._reply(r, res, res["explanation"])
        return self._reply(
            r, None,
            "Posso estimar produtividade regional, simular uma data de plantio ou "
            "recomendar a melhor janela. Reformule, por favor (ex.: 'qual a melhor data "
            "para plantar soja em Horizontina?').",
        )

    @staticmethod
    def _reply(r: Routed, result: dict | None, answer: str) -> dict:
        return {
            "intent": r.intent.value,
            "parameters": {
                "municipality": r.municipality,
                "season": r.season,
                "planting_date": r.planting_date,
            },
            "result": result,
            "answer": answer,
        }


def _financials_dict(fin: dict) -> dict:
    return {
        "breakdown": vars(fin["breakdown"]),
        "price_per_bag": fin["price_per_bag"],
        "break_even_yield_sc_ha": fin["break_even_yield_sc_ha"],
        "yield_source": fin["yield_source"],
        "scenarios": [vars(s) for s in fin["scenarios"]],
    }


def _safe_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None
