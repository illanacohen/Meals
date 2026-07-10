from fastapi import APIRouter
from app.routes import meals, plans, goals, onboarding, library, suggest

api_router = APIRouter()

api_router.include_router(meals.router, prefix='/meals', tags=['Meals'])
api_router.include_router(plans.router, prefix='/plans', tags=['Meal Plans'])
api_router.include_router(goals.router, prefix='/goals', tags=['Daily Goals'])
api_router.include_router(onboarding.router, prefix='/onboarding', tags=['Onboarding'])
api_router.include_router(library.router, prefix='/library', tags=['Meal Library'])
api_router.include_router(suggest.router, prefix='/suggest', tags=['Suggest'])
