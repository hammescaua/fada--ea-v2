"""Roteador agregador da API v1."""

from fastapi import APIRouter

from app.api.v1.routes import (
    adaptive,
    agronomic,
    assistant,
    calibration,
    capture,
    cost,
    credit,
    dashboard,
    decision_cards,
    decisions,
    demo,
    export,
    farms,
    health,
    insights,
    market,
    operations,
    planning,
    planting_date,
    regional_intelligence,
    season_planning,
    system,
    weather,
    zarc,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(system.router, tags=["system"])
api_router.include_router(regional_intelligence.router, tags=["regional-intelligence"])
api_router.include_router(planting_date.router, tags=["planting-date"])
api_router.include_router(farms.router, tags=["ground-truth"])
api_router.include_router(operations.router, tags=["operations"])
api_router.include_router(capture.router, tags=["quick-capture"])
api_router.include_router(planning.router, tags=["planning"])
api_router.include_router(cost.router, tags=["cost"])
api_router.include_router(credit.router, tags=["credit"])
api_router.include_router(adaptive.router, tags=["adaptive"])
api_router.include_router(agronomic.router, tags=["agronomic"])
api_router.include_router(calibration.router, tags=["calibration"])
api_router.include_router(insights.router, tags=["insights"])
api_router.include_router(market.router, tags=["market"])
api_router.include_router(weather.router, tags=["weather"])
api_router.include_router(zarc.router, tags=["zarc"])
api_router.include_router(season_planning.router, tags=["season-planning"])
api_router.include_router(decisions.router, tags=["decisions"])
api_router.include_router(decision_cards.router, tags=["decision-cards"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(demo.router, tags=["demo"])
api_router.include_router(export.router, tags=["export"])
api_router.include_router(assistant.router, tags=["assistant"])
