"""Projeção plurianual por talhão (ADR-0031).

Produtividade é calculada **uma vez** (a base climática = safra típica se repete);
a rentabilidade varia por safra conforme preço/custo (e tendência) do produtor. O
LLM, se houver, só reescreve a narrativa — nunca os números (ADR-0002/0029).
"""

from __future__ import annotations

from app.data.connectors.cost_benchmark import CostBenchmarkStore
from app.data.connectors.market_snapshot import MarketSnapshotStore
from app.domain.finance import next_seasons, project_economics
from app.engine.llm_client import refine_narrative
from app.infra.repositories import AgronomicProfileRepository, FarmRepository
from app.services.agronomic import AgronomicService


class FieldNotFound(Exception):
    pass


class MultiSeasonService:
    def __init__(
        self,
        farms: FarmRepository,
        profiles: AgronomicProfileRepository,
        agronomic: AgronomicService,
        model,
        market: MarketSnapshotStore | None = None,
        costs: CostBenchmarkStore | None = None,
    ) -> None:
        self._farms = farms
        self._profiles = profiles
        self._agronomic = agronomic
        self._model = model
        self._market = market or MarketSnapshotStore()
        self._costs = costs or CostBenchmarkStore()

    def project(
        self,
        field_id: int,
        *,
        n_seasons: int = 3,
        base_season: str = "2026/27",
        crop: str = "soja",
        uf: str = "RS",
        price_per_bag: float | None = None,
        cost_per_ha: float | None = None,
        price_trend_pct: float = 0.0,
        cost_trend_pct: float = 0.0,
    ) -> dict:
        field = self._farms.get_field(field_id)
        if field is None:
            raise FieldNotFound(str(field_id))
        farm = self._farms.get_farm(field.farm_id)
        info = self._model.municipalities().get(str(farm.municipality_code))
        if info is None:
            raise FieldNotFound(str(field_id))
        municipality = info["name"]
        profile = self._profiles.get(field_id) or {}

        est = self._agronomic.personalized_estimate(municipality, crop, base_season, profile)
        scenarios = {s["name"]: s["yield_sc_ha"] for s in est["personalized"]["scenarios"]}
        point = est["personalized"]["point_sc_ha"]
        interval = est["personalized"]["interval_sc_ha"]

        # Preço/custo: usa o informado; senão, fontes públicas datadas (CEPEA/CONAB).
        price, price_src = self._resolve_price(price_per_bag, crop)
        cost, cost_src = self._resolve_cost(cost_per_ha, crop, uf)

        labels = next_seasons(base_season, max(1, n_seasons))
        seasons = [
            project_economics(
                scenarios, price, cost, label, i, price_trend_pct, cost_trend_pct
            )
            for i, label in enumerate(labels)
        ]

        payload = {
            "field_id": field_id,
            "field_name": field.name,
            "municipality": municipality,
            "crop": crop,
            "area_ha": field.area_ha,
            "productivity": {
                "point_sc_ha": point,
                "interval_sc_ha": interval,
                "scenarios": est["personalized"]["scenarios"],
                "note": (
                    "A base climática é a safra típica da região (cenários seco/"
                    "normal/favorável) e se repete a cada safra — não é previsão do "
                    "clima de um ano específico."
                ),
            },
            "assumptions": {
                "price_per_bag": price,
                "price_source": price_src,
                "cost_per_ha": cost,
                "cost_source": cost_src,
                "price_trend_pct": price_trend_pct,
                "cost_trend_pct": cost_trend_pct,
            },
            "seasons": [
                {
                    "season": s.season,
                    "year_index": s.year_index,
                    "price_per_bag": s.price_per_bag,
                    "cost_per_ha": s.cost_per_ha,
                    "expected_profit_per_ha": s.expected_profit_per_ha,
                    "scenarios": [vars(sc) for sc in s.scenarios],
                }
                for s in seasons
            ],
            "data_sources": est["data_sources"] + [src for src in (price_src, cost_src) if src],
            "disclaimer": (
                "Projeção determinística. A produtividade por cenário se repete (safra "
                "típica); a rentabilidade varia conforme o preço e o custo que você "
                "assume. Não é garantia — é o intervalo provável sob essas hipóteses."
            ),
        }
        payload["narrative"] = refine_narrative(_narrate(payload))
        return payload

    def _resolve_price(self, price: float | None, crop: str) -> tuple[float, str | None]:
        if price is not None:
            return price, None
        snap = self._market.load(crop)
        if snap is not None:
            return snap.latest.value, f"{snap.source} ({snap.fetched_at})"
        return 0.0, None

    def _resolve_cost(self, cost: float | None, crop: str, uf: str) -> tuple[float, str | None]:
        if cost is not None:
            return cost, None
        bench = self._costs.load(crop, uf)
        if bench is not None:
            return bench.ct_per_ha, f"{bench.source} ({bench.fetched_at})"
        return 0.0, None


def _narrate(payload: dict) -> str:
    p = payload["productivity"]
    first = payload["seasons"][0]
    lo, hi = p["interval_sc_ha"]
    worst = min(s["profit_per_ha"] for s in first["scenarios"])
    best = max(s["profit_per_ha"] for s in first["scenarios"])
    n = len(payload["seasons"])
    return (
        f"Para o talhão {payload['field_name']} em {payload['municipality']}, a soja deve "
        f"render cerca de {p['point_sc_ha']:.0f} sc/ha (entre {lo:.0f} e {hi:.0f}) numa "
        f"safra típica. Com preço de R$ {first['price_per_bag']:.2f}/sc e custo de "
        f"R$ {first['cost_per_ha']:.0f}/ha, o lucro por hectare na próxima safra fica "
        f"entre R$ {worst:.0f} (ano seco) e R$ {best:.0f} (ano favorável). A projeção "
        f"cobre {n} safras: a base climática se repete; o que muda é o preço e o custo "
        f"que você assume ao longo dos anos."
    )
