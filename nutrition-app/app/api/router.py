from fastapi import APIRouter
from app.routes import meals

api_router = APIRouter()

api_router.include_router(meals.router, prefix='/meals', tags=['Meals'])
