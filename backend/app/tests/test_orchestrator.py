"""Testa o roteamento determinístico do orchestrator (puro, sem serviços)."""

from app.engine.orchestrator import DeterministicRouter, Intent

ROUTER = DeterministicRouter(known_municipalities=["Horizontina", "Três Passos"])


def test_optimization_intent():
    r = ROUTER.route("Qual a melhor data para plantar soja em Horizontina?", None)
    assert r.intent == Intent.OPTIMIZATION
    assert r.municipality == "Horizontina"


def test_simulation_intent_with_date_pt():
    r = ROUTER.route("Vale plantar em 20 de outubro?", "Horizontina")
    assert r.intent == Intent.SIMULATION
    assert r.planting_date == "2026-10-20"  # ano de plantio da safra default 2026/27


def test_simulation_intent_month_only():
    r = ROUTER.route("Quanto eu colheria se plantasse em novembro?", "Horizontina")
    assert r.intent == Intent.SIMULATION
    assert r.planting_date == "2026-11-01"


def test_regional_intent():
    r = ROUTER.route("Quais os riscos?", "Horizontina")
    assert r.intent == Intent.REGIONAL
    assert r.planting_date is None


def test_numeric_date_format():
    r = ROUTER.route("vale plantar em 05/11?", "Horizontina")
    assert r.planting_date == "2026-11-05"


def test_context_municipality_used_when_absent():
    r = ROUTER.route("Quais os riscos?", "Três Passos")
    assert r.municipality == "Três Passos"


def test_season_override():
    r = ROUTER.route("riscos da safra 2024/25 em Horizontina", None)
    assert r.season == "2024/25"


def test_unknown_intent():
    r = ROUTER.route("bom dia, tudo bem?", "Horizontina")
    assert r.intent == Intent.UNKNOWN


def test_cost_total_intent():
    assert ROUTER.route("Quanto já investi nesta safra?", None).intent == Intent.COST_TOTAL


def test_cost_per_hectare_intent():
    assert ROUTER.route("Qual meu custo por hectare?", None).intent == Intent.COST_PER_HECTARE


def test_applications_intent():
    assert ROUTER.route("Quantas aplicações fiz?", None).intent == Intent.APPLICATIONS


def test_break_even_intent():
    assert ROUTER.route(
        "Qual produtividade preciso para empatar?", None
    ).intent == Intent.BREAK_EVEN


def test_above_average_intent():
    assert ROUTER.route(
        "Minha fazenda costuma produzir acima da média?", None
    ).intent == Intent.ABOVE_AVERAGE


def test_learned_intent():
    assert ROUTER.route(
        "Quanto o FADA já aprendeu sobre minha área?", None
    ).intent == Intent.LEARNED


def test_reliability_intent():
    assert ROUTER.route("Quão confiável é essa personalização?", None).intent == Intent.RELIABILITY


def test_regional_vs_personalized_intent():
    assert ROUTER.route(
        "Qual a diferença entre a previsão regional e a personalizada?", None
    ).intent == Intent.REGIONAL_VS_PERSONALIZED


def test_intervals_calibrated_intent():
    assert ROUTER.route("Os intervalos estão calibrados?", None).intent == \
        Intent.INTERVALS_CALIBRATED


def test_model_reliability_intent():
    assert ROUTER.route("Quão confiável é o modelo?", None).intent == Intent.MODEL_RELIABILITY


def test_bias_direction_intent():
    assert ROUTER.route(
        "Ele costuma errar para cima ou para baixo?", None
    ).intent == Intent.BIAS_DIRECTION


def test_personalized_better_intent():
    assert ROUTER.route("O personalizado é realmente melhor?", None).intent == \
        Intent.PERSONALIZED_BETTER


def test_model_reliability_not_confused_with_farm_reliability():
    # "personalização" -> reliability adaptativa; "modelo" -> calibração
    assert ROUTER.route("Quão confiável é essa personalização?", None).intent == \
        Intent.RELIABILITY
    assert ROUTER.route("Quão confiável é o modelo?", None).intent == Intent.MODEL_RELIABILITY


def test_over_budget_intent():
    assert ROUTER.route("Estou gastando acima do planejado?", None).intent == \
        Intent.OVER_BUDGET


def test_remaining_budget_intent():
    assert ROUTER.route("Quanto ainda falta investir?", None).intent == \
        Intent.REMAINING_BUDGET


def test_following_plan_intent():
    assert ROUTER.route("Estou seguindo meu plano?", None).intent == Intent.FOLLOWING_PLAN


def test_field_attention_intent():
    assert ROUTER.route("Qual talhão merece mais atenção?", None).intent == \
        Intent.FIELD_ATTENTION


def test_cost_highest_field_intent():
    assert ROUTER.route("Qual talhão está mais caro?", None).intent == \
        Intent.COST_HIGHEST_FIELD


def test_attention_not_confused_with_over_budget():
    # "acima do planejado" -> orçamento; "merece atenção" -> decisão
    assert ROUTER.route("Estou gastando acima do planejado?", None).intent == Intent.OVER_BUDGET
    assert ROUTER.route("Qual talhão precisa de atenção?", None).intent == \
        Intent.FIELD_ATTENTION
