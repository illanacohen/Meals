from pydantic import BaseModel
from typing import Optional


class MealCreate(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float


class MealUpdate(BaseModel):
    name: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    fiber: Optional[float] = None


class MealResponse(BaseModel):
    id: int
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float

    model_config = {
        'from_attributes': True
    }


class ErrorResponse(BaseModel):
    detail: str


class MealDelete(BaseModel):
    id: int


class Meal(MealCreate):
    id: int

    model_config = {
        'from_attributes': True
    }
