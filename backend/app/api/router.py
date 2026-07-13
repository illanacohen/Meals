from fastapi import APIRouter
from app.routes import (
    meals,
    plans,
    goals,
    onboarding,
    library,
    suggest,
    shopping,
    goal_plans,
    context,
    execution_items,
)

api_router = APIRouter()

# Entidad principal: Plan orientado a objetivos
api_router.include_router(goal_plans.router, prefix='/plans', tags=['Plans'])

# Canonical execution context (Plan + UserContext → Execution Engine)
api_router.include_router(context.router, prefix='/context', tags=['UserContext'])

# Exception logs, visual substitutes, friction analysis
api_router.include_router(execution_items.router, prefix='/execution-items', tags=['Execution Items'])

# Módulo nutrición (legado: día alimenticio)
api_router.include_router(plans.router, prefix='/meal-plans', tags=['Nutrition / Meal Days'])
api_router.include_router(meals.router, prefix='/meals', tags=['Nutrition / Meals'])
api_router.include_router(goals.router, prefix='/goals', tags=['Nutrition / Daily Goals'])
api_router.include_router(library.router, prefix='/library', tags=['Nutrition / Library'])
api_router.include_router(suggest.router, prefix='/suggest', tags=['Nutrition / Suggest'])
api_router.include_router(shopping.router, prefix='/shopping-list', tags=['Nutrition / Shopping'])

# Onboarding remains a producer of UserContext (not a consumer path for the engine)
api_router.include_router(onboarding.router, prefix='/onboarding', tags=['Onboarding'])
